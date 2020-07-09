
statements = []

def statement(func):
    def wrapper(self, *args, **kwargs):
        return func(self, *args, **kwargs)
    
    statements.append(wrapper)
    
    return wrapper


class Policy:
    
    def __call__(self, *args, **kwargs):
        statement_results = []
        
        stmts = [
            getattr(self.__class__, m)
            for m in dir(self.__class__)
            if getattr(self.__class__, m) in statements
        ]
        
        for stmt in stmts:
            statement_result = stmt(self, *args, **kwargs)
            
            assert isinstance(statement_result, (Allowance, Rejection))
            statement_results.append(statement_result)
        
        return PolicyEvaluationResult(statement_results)


class StatementResult:
    pass


class Allowance(StatementResult):
    
    def __init__(self, payload=None):
        self.payload = payload


class Rejection(StatementResult):
    
    def __init__(self, reason: str):
        if not reason or reason == "":
            raise ValueError("Reason must be defined")
            
        self.reason = reason


class PolicyEvaluationResult:
    
    def __init__(self, results):
        self.results = results
    
    @property
    def allowed(self):
        return len(self.rejections) == 0
        
    @property
    def allowances(self):
        return [r for r in self.results if isinstance(r, Allowance)]
        
    @property
    def rejections(self):
        return [r for r in self.results if isinstance(r, Rejection)]
        
    @property
    def reason(self):
        if self.allowed:
            return None
        else:
            return ", ".join(
                [rejection.reason for rejection in self.rejections]
            )
            
    @property
    def payload(self):
        payload = {}
        
        for a in self.allowances:
            payload.update(a.payload)
            
        return payload