import latok.core.constants as C
import latok.core.latok_utils as latok_utils


def test_get_specs_and_repls():
    assert latok_utils.get_specs_and_repls(None) == (None, None)
    assert latok_utils.get_specs_and_repls([]) == (None, None)
    specs, repls = latok_utils.get_specs_and_repls([(C.URL_FEATURE, None)])
    assert (specs, repls) == ([C.URL_FEATURE], None)
    specs, repls = latok_utils.get_specs_and_repls([(None, '???')])
    assert (specs, repls) == (None, None)
    specs, repls = latok_utils.get_specs_and_repls([(C.URL_FEATURE, '_URL')])
    assert (specs, repls) == ([C.URL_FEATURE], {C.URL_FEATURE.name: '_URL'})
