import {readFileSync, realpathSync} from 'node:fs';
import {execFileSync} from 'node:child_process';
console.log(JSON.stringify({node:process.version, execPath:process.execPath,
  pi:{version:execFileSync('pi',['--version'],{encoding:'utf8'}).trim(),
    entry_path:realpathSync('/usr/local/bin/pi')},
  python:execFileSync('/opt/dependencies/.venv/bin/python',['-c','import platform; print(platform.python_version())'],{encoding:'utf8'}).trim(),
  uv:execFileSync('uv',['--version'],{encoding:'utf8'}).trim().split(' ')[1],
  checkers:JSON.parse(readFileSync('/opt/tool-versions.json','utf8')),
  sources:JSON.parse(readFileSync('/opt/sources.json','utf8'))}));
