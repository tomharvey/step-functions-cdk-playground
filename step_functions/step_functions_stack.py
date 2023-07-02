from aws_cdk import (
    Stack,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as sfn_tasks,
    aws_lambda as _lambda,
    Duration
)
from constructs import Construct

class StepFunctionsStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        wait = sfn.Wait(
            self, "Wait",
            time=sfn.WaitTime.duration(Duration.seconds(5))
        )

        greeter = _lambda.Function(
            self, "GreeterFunction",
            runtime=_lambda.Runtime.PYTHON_3_7,
            handler="host.hello",
            code=_lambda.Code.from_asset("lambda"),
        )

        say_hello = sfn_tasks.LambdaInvoke(
            self, "SayHello",
            lambda_function=greeter,
            # result_path="$.Greeter",
            output_path="$.Payload"
        )

        coat_receiver = _lambda.Function(
            self, "CoatReceiverFunction",
            runtime=_lambda.Runtime.PYTHON_3_7,
            handler="cloakroom.receive",
            code=_lambda.Code.from_asset("lambda"),
        )

        take_coat = sfn_tasks.LambdaInvoke(
            self, "TakeCoat",
            lambda_function=coat_receiver,
            # result_path="$.CoatReceived",
            output_path="$.Payload"
        )

        welcome_tasks = sfn.Parallel(
            self, 'WelcomeTasks',
            result_path="$.WelcomeTasksResults",
        )
        welcome_tasks.branch(say_hello, take_coat)

        collate_welcome_results = sfn.Pass(
            self, "CollateWelcomeResults",
            result_path="$.WelcomeTasksResults",
            parameters={
                "Message.$": "$.WelcomeTasksResults[0].Message",
                "Hanger.$": "$.WelcomeTasksResults[1].Hanger",
            }
        )

        departer = _lambda.Function(
            self, "DeparterFunction",
            runtime=_lambda.Runtime.PYTHON_3_7,
            handler="host.goodbye",
            code=_lambda.Code.from_asset("lambda"),
        )

        say_goodbye = sfn_tasks.LambdaInvoke(
            self, "SayGoodbye",
            lambda_function=departer,
            output_path="$.Payload"
        )

        coat_collector = _lambda.Function(
            self, "CoatCollectorFunction",
            runtime=_lambda.Runtime.PYTHON_3_7,
            handler="cloakroom.collect",
            code=_lambda.Code.from_asset("lambda"),
        )

        return_coat = sfn_tasks.LambdaInvoke(
            self, "ReturnCoat",
            lambda_function=coat_collector,
            output_path="$.Payload",
            payload=sfn.TaskInput.from_object({
                "hanger_id": sfn.JsonPath.string_at("$.WelcomeTasksResults.Hanger")
            })
        )

        departure_tasks = sfn.Parallel(
            self, 'DepartureTasks',
            result_path="$.DepartureTasksResults",
        )
        departure_tasks.branch(return_coat, say_goodbye)

        collate_departure_results = sfn.Pass(
            self, "CollateDepartureResults",
            result_path="$.DepartureTasksResults",
            parameters={
                "Hanger.$": "$.DepartureTasksResults[0].Hanger",
                "Message.$": "$.DepartureTasksResults[1].Message",
            }
        )

        succeed = sfn.Succeed(
            self, 'Greeted',
        )

        definition = welcome_tasks.next(
            collate_welcome_results
        ).next(
            wait
        ).next(
            departure_tasks
        ).next(
            collate_departure_results
        ).next(
            succeed
        )

        sfn.StateMachine(
            self, "ExampleStateMachine",
            definition=definition,
            timeout=Duration.seconds(300),
        )
