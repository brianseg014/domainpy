
from domainpy.domain.policies import Policy, Allowance, Rejection, statement

class ExamplePolicy(Policy):
    
    def __init__(self, allow):
        self.allow = allow
        
    def should_not_execute(self):
        return Rejection("Should not execute")
    
    @statement
    def policy_test_1(self):
        return Allowance()
    
    @statement
    def policy_test_2(self):
        if self.allow:
            return Allowance()
        else:
            return Rejection("Reason")


def test_allowance():
    policy = ExamplePolicy(True)
    result = policy()
    assert result.allowed
    
    
def test_rejection():
    policy = ExamplePolicy(False)
    result = policy()
    assert not result.allowed
    assert len(result.rejections) == 1
