
import os, asyncio
import json, shutil
import Shared, Byond, ClopenDream, OpenDream, SS13

from .Byond import *
from .ClopenDream import *
from .Compare import *
from .OpenDream import *
from .SS13 import *
from .Reports import *
from .TestCase import *
from .Tests import *
from .Updates import *

class App(
    ByondApp, ClopenDreamApp, OpenDreamApp,
    SS13App, 
    CompareApp, 
    TestsApp, ReportsApp,
    UpdateApp):
    def __init__(self):
        pass

    def init(self):
        self.env = Shared.Environment()
        self.load_configs()

        self.env.attr.test_mode = "all"

        self.env.attr.scheduler.task_state = Shared.FilesystemState( self.env.attr.dirs.state / 'scheduler' / 'tasks', 
            loader=lambda s: json.loads(s), saver=lambda js: json.dumps(js) )
        self.env.attr.scheduler.event_state = Shared.FilesystemState( self.env.attr.dirs.state / 'scheduler' / 'events', 
            loader=lambda s: json.loads(s), saver=lambda js: json.dumps(js) )
        self.env.attr.scheduler.result_state = Shared.FilesystemState( self.env.attr.dirs.state / 'scheduler' / 'results',
            loader=lambda s: json.loads(s), saver=lambda js: json.dumps(js) )

        self.env.event_handlers['process.complete'] = self.handle_process_complete

        self.env.attr.process.log_mode = "auto"
        self.env.attr.process.auto_log_path = self.env.attr.dirs.ramdisc / "auto_process_logs"
        self.env.attr.process.auto_logs = []

        self.env.attr.git.repo.remote = "origin"

        self.env.attr.resources.git = Shared.CountedResource(2)
        self.env.attr.resources.process = Shared.CountedResource(4)

        Shared.Workflow.init( self.env )
        Shared.Scheduler.init( self.env )

        self.env.attr.wf.report_path = self.env.attr.dirs.ramdisc / "workflow_report.html"
        print(f"file://{self.env.attr.wf.report_path}")

        self.load_states(self.env)

    def load_states(self, env):
        for name in os.listdir(env.attr.dirs.state + 'app'):
            state_filename = env.attr.dirs.state / 'app' / f'{name}.json'
            state = Shared.InfiniteDefaultDict()
            with Shared.File.open(state_filename, "r") as f:
                try:
                    state.initialize( json.load(f) )
                except json.decoder.JSONDecodeError:
                    raise Exception(f"State decode error: {name}")
            env.set_attr(name, state)

    def save_states(self, env):
        for name in env.filter_properties(".state.*"):
            state_filename = env.attr.dirs.state / 'app' / f'{name}.json'
            result = json.dumps( env.get_attr(name).finitize(), cls=Shared.Json.BetterEncoder)
            with Shared.File.open(state_filename, "w") as f:
                f.write( result )

    async def deinit(self):
        self.save_states(self.env)
        Shared.Scheduler.deinit(self.env)

    async def start(self):
        self.running = True
        self.init()
        try:
            await self.run()
        finally:
            await self.deinit()
            self.running = False
            os.system('stty sane')
        #self.update_report(self.env)

    def load_configs(self):
        config_dir = os.path.abspath( os.path.expanduser("~/dream-storage/config") )
        for file_path in sorted(os.listdir( config_dir )):
            config_path = os.path.join(config_dir, file_path)
            config_obj = Shared.Object.import_file( config_path )
            for name, attr in vars(config_obj).items():
                if name.startswith('setup_'):
                    attr(self.env)

    def parse_install_arg(s):
        s = s.split(".")
        return {'platform':s[0], 'install_id':s[1]}

    @staticmethod
    async def handle_process_complete(env):
        process = env.prefix('.process')

        if process.log_mode == "auto":
            process.auto_logs.append( env )