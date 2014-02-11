# -*- coding: utf-8 -*
'''
__author__  = 'Roach'
__version__ = '1.0'
'''
import subprocess
import os
import time
import re
import logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s-%(name)s-%(levelname)s-%(message)s',
                    filename='main.log',
                    filemode='w',
                    )
sh = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s-%(name)s-%(levelname)s-%(message)s')
sh.setFormatter(formatter)
logger = logging.getLogger('MonkeyTest')
logger.addHandler(sh)

RE_CRASH = re.compile('// CRASH: (.*?) \(pid \d+?\)')


class AdbCmd(object):

    def __init__(self):
        self.command = ['adb']
        self.set_command_default()

    def set_command_default(self):
        self.serial_number = ''
        self.shell_command = None
    
    def get_command(self):
        if self.serial_number:
            self.command.append('-s %s'%self.serial_number)
        if self.shell_command:
            self.command.append('shell %s'%self.shell_command.get_command())
        return ' '.join(self.command)


class Monkey(object):
    '''
    seed:
        伪随机数生成器的seed值。如果用相同的seed值再次运行Monkey。它将生成相同的
        事件序列。
    throttle:
        在事件之间插入固定延迟。通过这个选项可以减缓Monkey的执行速度。如果不指定
        该选项，Monkey将不会延迟，事件将尽可能快的产生。
    pct_touch:
        调整触摸事件的百分比（触摸事件是一个down-up事件，它发生在屏幕上的某一位
        置）。
    pct_motion:
        调整动作事件的百分比（动作事件由屏幕上某处的一个down事件、一系列的伪随机
        事件和一个up事件组成）。
    pct_trackball:
        调整轨迹事件的百分比（轨迹事件由一个或几个随机的移动组成，有时还伴随有点
        击）。
    pct_nav:
        调整‘基本’导航事件的百分比（导航事件由来自方向输入设备的up/down/left/
        right组成）。
    pct_majornav:
        调整‘主要’导航事件的百分比（这些导航事件常引发图形界面的动作，如：5-way
        键盘的中间按键、回退按键、菜单按键）。
    pct_syskeys:
        调整‘系统’按键事件的百分比（这些按键通常被保留，由系统使用，如Home、
        Back、Start Call、End Call及音量控制键）。
    pct_appswitch:
        调整启动Activity的百分比。在随机间隔里，Monkey将执行一个startActivity()
        调用，作为最大程度覆盖包中全部Activity的一种方法。
    pct_anyevent:
        调整其他类型事件的备份比。它包罗了所有其他类型的事件，如：按键、其它不常
        用的设备按钮、等等。
    p_allowed_package_name:
        如果用此参数指定了一个或几个包，Monkey将只允许系统启动这些包里的
        Activity。如果你的应用程序还需要访问其他包里的Activity（如选取一个联系人
        ），那些包也需要在此同时指定。如果不指定任何包，Monkey将允许系统启动全部
        包里的Activity。要指定多个包，需要使用多个-p选项，每个-p选项只能用于一个
        包。
    c_main_category:
        如果使用此参数指定了一个或几个类别，Monkey将只允许系统启动被这些类别中的
        某个类别列出的Activity。如果不指定任何类别，Monkey将选择下列类别中列出的
        Activity：Internet.CATEGORY_LAUNCHER或Internet.CATEGORY_MONKRY。要指定多
        个类别，需要使用多个-c选项，每个-c选项只能用于一个类别。
    dbg_no_events:
        设置此选项， Monkey 将执行初始启动，进入到一个测试 Activity ，然后不会再
        进一步生成事件。为了得到最佳结果，把它与 -v 、一个或几个包约束、以及一个
        保持 Monkey 运行 30 秒或更长时间的非零值联合起来，从而提供一个环境，可以
        监视应用程序所调用的包之间的转换。
    hprof:
        设置此选项，将在 Monkey 事件序列之前和之后立即生成 profiling 报告。这将
        会在 data/misc 中生成大文件 (~5Mb) ，所以要小心使用它。
    ignore_crashes:
        通常，当应用程序崩溃或发生任何失控异常时， Monkey 将停止运行。如果设置此
        选项， Monkey 将继续向系统发送事件，直到计数完成。
    ignore_timeouts:
        通常，当应用程序发生任何超时错误 ( 如“ Application Not Responding ”对话
        框 ) 时， Monkey 将停止运行。如果设置此选项， Monkey 将继续向系统发送事
        件，直到计数完成。
    ignore_security_exceptions:
        通常，当应用程序发生许可错误 ( 如启动一个需要某些许可的 Activity) 时，
        Monkey 将停止运行。如果设置了此选项， Monkey 将继续向系统发送事件，直到
        计数完成。
    kill_process_after_error:
        通常，当 Monkey 由于一个错误而停止时，出错的应用程序将继续处于运行状态。
        当设置了此选项时，将会通知系统停止发生错误的进程。注意，正常的 (成功的)
        结束，并没有停止启动的进程，设备只是在结束事件之后，简单地保持在最后的
        状态。
    monitor_native_crashes:
        监视并报告 Android 系统中本地代码的崩溃事件。如果设置了
        --kill-process-after-error ，系统将停止运行。
    wait_dbg:停止执行中的 Monkey ，直到有调试器和它相连接。
    pkg_whitelist_file:白名单
    pkg_blacklist_file:黑名单
    '''
    def __init__(self):
        self.command = ['monkey']
        self.set_command_default()
    
    def set_command_default(self):
        self.event_count = 100000
        self.verbose_level = 3
        self.seed = False
        self.throttle = 500
        self.pct_touch = False
        self.pct_motion = False
        self.pct_trackball = False
        self.pct_nav = False
        self.pct_majornav = False
        self.pct_syskeys = False
        self.pct_appswitch = 20
        self.pct_anyevent = 0
        self.p_allowed_package_name = None
        self.c_main_category = False
        self.dbg_no_events = False
        self.hprof  = True
        self.ignore_crashes = False
        self.ignore_timeouts = True
        self.ignore_security_exceptions = False
        self.kill_process_after_error = False
        self.monitor_native_crashes = False
        self.wait_dbg = False
        self.pkg_whitelist_file = False
        self.pkg_blacklist_file = False

    def get_command(self):
        self.command.append('-v '*self.verbose_level)
        if self.seed:
            self.command.append('-s %d'%self.seed)
        if self.pkg_whitelist_file:
            self.command.append('--pkg-whitelist-file %s'%
                    self.pkg_whitelist_file)
        elif self.pkg_blacklist_file:
            self.command.append('--pkg-blacklist-file %s'%
                    self.pkg_blacklist_file)
        if self.throttle:
            self.command.append('--throttle %d'%self.throttle)
        if self.hprof:
            self.command.append('--hprof')
        if self.ignore_crashes:
            self.command.append('--ignore-crashes')
        if self.ignore_timeouts:
            self.command.append('--ignore-timeouts')
        if self.pct_appswitch:
            self.command.append('--pct-appswitch %d'%self.pct_appswitch)
        if self.pct_anyevent:
            self.command.append('--pct-anyevent %d'%self.pct_anyevent)
        if self.p_allowed_package_name \
        and isinstance(self.p_allowed_package_name, str):
            self.command.append('-p %s'%self.p_allowed_package_name)
        elif self.p_allowed_package_name \
        and isinstance(self.p_allowed_package_name, (list, tuple)):
            for package_name in self.p_allowed_package_name:
                self.command.append('-p %s'%self.package_name)
        self.command.append(str(self.event_count))
        return ' '.join(self.command)

def find_all_crashes(string):
    crashes = {}
    crash_names = RE_CRASH.findall(string)
    for name in crash_names:
        if name in crashes:
            crashes[name] += 1
        else:
            crashes[name] = 1
    return crashes

def run_command_in_shell(command, output=None):
    subprocess.call(command, shell=True, stdout=output)

if __name__ == '__main__':
    monkey = Monkey()
    monkey.verbose_level = 3
    monkey.throttle = 500
    monkey.hprof = True
    monkey.ignore_crashes = True
    monkey.ignore_timeouts = True
    monkey.event_count = 10000000
    #monkey.pct_appswitch = 0
    monkey.p_allowed_package_name = 'com.android.settings'
    adbcmd = AdbCmd()
    #adbcmd.serial_number = '123456789'
    adbcmd.shell_command = monkey

    output = open('output.log', 'w+')
    try:
        command = adbcmd.get_command()
        logger.info(command)
        run_command_in_shell(command, output)
    except  KeyboardInterrupt:
        pass
    finally:
        output.flush()
        output.seek(0)
        crashes = find_all_crashes(output.read())
        logger.info('Crashes package:')
        if crashes:
            logger.info(crashes)
        else:
            logger.info('No crashed package!!!')
        raw_input('press anykey continue...')
