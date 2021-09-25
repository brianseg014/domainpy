
from domainpy.utils.contextualized import Contextualized
from domainpy.utils.traceable import Traceable
from domainpy.application.integration import IntegrationEvent


def test_stamp_with_args():
    m = IntegrationEvent.stamp(
        trace_id='tid',
        context='context'
    )(
        __timestamp__=0.0,
        __resolve__='success',
        __error__=None,
        __version__=1
    )
    assert m.__trace_id__ == 'tid'
    assert m.__context__ == 'context'
    
def test_stamp_without_args():
    Traceable.set_default_trace_id('tid')
    Contextualized.__context__ = 'context'
    
    m = IntegrationEvent.stamp()(
        __timestamp__=0.0,
        __resolve__='success',
        __error__=None,
        __version__=1
    )
    assert m.__trace_id__ == 'tid'
    assert m.__context__ == 'context'
