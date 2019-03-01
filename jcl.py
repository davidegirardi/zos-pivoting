""" JCL job generator"""

from string import Template

class Job():
    """ JCL job generator

    Create a Job object and then add steps of type Step to it.
    It is possible to add steps by passing the step code too"""
    INTRO = '''//${JOB_NAME}JOB 1'''
    END = '''
/*'''
    OMVS = 'OMVS'
    TSO = 'TSO'
    JOB_NAME_SIZE = 12

    def __init__(self, name='PYJCL', intro=None, end=END):
        if intro is None:
            self.intro = Template(self.INTRO).substitute(
                JOB_NAME=name.upper().ljust(self.JOB_NAME_SIZE, ' '))
        else:
            self.intro = intro
        self.steps = []
        self.end = end

    def add_step(self, step_code):
        """Add a Step object to the JCL"""
        self.steps.append(step_code)

    def add_inline(self, step_code, step_type=OMVS):
        """Add a step with step_code as step.
        Pass step_type to specify you need a TSO or OMVS (default) step"""
        if step_type == self.OMVS:
            step = OMVSstep().run_inline(step_code)
        elif step_type == self.TSO:
            step = TSOstep().run_inline(step_code)
        else:
            raise ValueError('Invalid step_type')
        self.add_step(step)

    def render(self):
        """Render the complete JCL"""
        jcl = self.intro
        for step in self.steps:
            jcl += step
        jcl += self.end
        return jcl

    def __str__(self):
        """Wrap for render(self)"""
        return self.render()


class Step():
    """Superclass representing a JCL step"""
    DEFAULT_NAME = 'RUNOMVS'
    INLINE_STEP = '''
//${RUNID}EXEC PGM=JUST_A_PLACEHOLDER
${STEPCMD}'''
    STEP_NAME_SIZE = 12

    def __init__(self, name=DEFAULT_NAME):
        self.name = name

    def run_inline(self, stepcmd):
        """Run inline code"""
        step_code = Template(self.INLINE_STEP).substitute(
            RUNID=self.name.upper().ljust(self.STEP_NAME_SIZE, ' '),
            STEPCMD=stepcmd)
        return step_code

class OMVSstep(Step):
    """Class implementing Step for an OMVS command"""
    DEFAULT_NAME = 'RUNOMVS'
    INLINE_STEP = '''
//${RUNID}EXEC PGM=BPXBATCH
//STDOUT      DD SYSOUT=*
//STDERR      DD SYSOUT=*
//STDIN       DD DUMMY
//STDENV      DD DUMMY
//STDPARM     DD *
${STEPCMD}'''


class TSOstep(Step):
    """Class implementing Step for a TSO command"""
    DEFAULT_NAME = 'RUNTSO'
    INLINE_STEP = '''
//${RUNID}EXEC PGM=IKJEFT01
//SYSPRINT    DD SYSOUT=*
//SYSTSPRT    DD SYSOUT=*
//SYSTSIN     DD *
${STEPCMD}'''


if __name__ == '__main__':
    # Just an example
    JCL = Job('MyStuff')
    S1 = OMVSstep('MYLABE').run_inline('SH ls > ~/output.txt')
    S2 = TSOstep('TSO').run_inline('LISTC')
    JCL.add_step(S1)
    JCL.add_step(S2)
    JCL.add_inline('LISTDSD', 'TSO')
    JCL.add_inline('SH pwd >> ~/output.txt')
    print(JCL)
