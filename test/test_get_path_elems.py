from common_util import get_path_elements


def test(path):
    dirs = get_path_elements(path)
    print('{}->{}'.format(path, dirs))


def main():
    test('/')
    test('/qwer')
    test('/asdf/foo.txt')
    test('/zxcv/bar')
    # this on is a weird case.
    test('/qwer/baz/')
    test('asdf')
    test('asdf/foo')
    # thses are really fine, because re should be smart and not use relative paths
    test('zxcv/qwer/asdf/../../../..')
    test('/zxcv/qwer/asdf/../../../..')
    test('zxcv/qwer/asdf/../../../../bing')
    test('c:/zxcv/qwer/asdf/../../../..')
    test('c:/')

if __name__ == '__main__':
    main()
