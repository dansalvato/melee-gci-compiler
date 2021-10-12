import re
from .pyiiasmh import ppctools
from .errors import BuildError
from . import context

def _make_tmp_directory():
    root = context.root()
    tmp_directory = root.path.parent/'tmp'
    try:
        tmp_directory.mkdir(exist_ok=True)
    except FileNotFoundError:
        raise BuildError("Unable to create tmp directory")
    return tmp_directory


def compile_asm(asm: str) -> str:
    """Takes ASM and compiles it to hex using pyiiasmh."""
    tmp_dir = _make_tmp_directory()
    txtfile = tmp_dir/"code.txt"
    with open(txtfile, 'w') as f:
        f.write(asm)
    with context.top() as c:
        try:
            compiled_asm = ppctools.asm_opcodes(tmp_dir)
        except RuntimeError as e:
            r = re.search(r'code\.txt\:(\d+)\: Error: (.*?)\\', str(e))
            if r:
                asm_line_number = int(r.group(1))
                error = r.group(2)
                if c.line_number:
                    c.line_number += asm_line_number
                else:
                    c.line_number = asm_line_number
                raise BuildError(f"Error compiling ASM: {error}")
            else:
                raise BuildError(f"Error compiling ASM")
        except Exception as e:
            raise BuildError(f"Error compiling ASM: {e}")
    return compiled_asm


def compile_c2(asm: str, c2_ba: int) -> str:
    """Takes ASM and compiles it into a C2 code using pyiiasmh."""
    compiled_asm = compile_asm(asm)
    c2_ba_str = "%08x" % c2_ba
    try:
        compiled_c2 = ppctools.construct_code(compiled_asm, bapo=c2_ba_str, ctype='C2D2')
    except Exception as e:
        raise BuildError(f"Error compiling ASM: {e}")
    return compiled_c2
