"""
########################################################################################################################
Fabric 간단 사용법.

본 스크립트는 Python 3.5에서 작성되었어요. 본디 'fabric'은 Python2에서 동작하게 구현되었지만, 최근 Python3에서 돌아갈 수 있도록 포팅한
프로젝트가 있습니다. requirements.txt 파일을 참고하세요.

copy2local 사용하기
-----------------
copy2local 스크립트는 scripts 디렉토리 안의 파이썬 스크립트를 임포트 해서, 그 스크립트 안에 있는 copy2local() 함수를 부릅니다.
그리고 각 스크립트를 위한 환경 설정 변수(rc file)를 별도로 지정하면 됩니다.

실행 예)
$ fab copy2local:applypathway -c rcfiles/applypathway.rc

########################################################################################################################
"""


from utils import (
    add_path,
    run_once,
    run_copy_to_local,
)

from os.path import (
    dirname,
)


def test():
    add_path(dirname(__file__))
    print(run_once('test_script', 'test_func'))


def copy2local(script_name):
    add_path(dirname(__file__))
    run_copy_to_local(script_name)
