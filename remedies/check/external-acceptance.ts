/** Opt-in completion check. The external host owns every authoritative decision. */
import {randomUUID} from 'node:crypto';
import {lstat, readFile, rename, writeFile} from 'node:fs/promises';
import type {PiLike, UnitMeta} from '../install.ts';

export const meta: UnitMeta = {
  pathology: 'Reports completion before external requirements pass',
  does: 'Requests a protected external check and continues only for bounded repairs',
  lesson: '', evidence: 'under qualification; no measured reliability claim',
};

type Request = {task_id:string; request_id:string; sequence:number};
type Reply = Request & {status:string; continue:boolean; feedback?:string};

async function exchange(request:Request):Promise<Reply> {
  const directory = '/attempt/gate';
  await writeFile(`${directory}/request.tmp`, JSON.stringify(request));
  await rename(`${directory}/request.tmp`, `${directory}/request.json`);
  const until = Date.now() + 35000;
  while (Date.now() < until) {
    try {
      const path = `${directory}/reply.json`, info = await lstat(path);
      if (!info.isFile() || info.size > 20000) throw new Error('invalid acceptance reply');
      const reply = JSON.parse(await readFile(path, 'utf8'));
      if (reply.request_id === request.request_id) return reply;
    } catch (error:any) {
      if (error.code !== 'ENOENT') throw error;
    }
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  throw new Error('external acceptance controller timed out');
}

export function install(pi:PiLike, options:{taskId?:string; exchange?:(request:Request)=>Promise<any>} = {}):void {
  const taskId = options.taskId ?? process.env.MELLUM_EXTERNAL_ACCEPTANCE_TASK;
  if (!taskId || !/^[a-zA-Z0-9_-]{1,100}$/.test(taskId))
    throw new Error('external acceptance requires a qualified external controller');
  let sequence = 0, pending = false;
  pi.on('agent_before_settle', async () => {
    if (pending) throw new Error('overlapping acceptance request');
    pending = true;
    try {
      const request = {task_id:taskId, request_id:randomUUID().replaceAll('-', ''), sequence:++sequence};
      const reply = await (options.exchange ?? exchange)(request);
      if (!reply || reply.task_id !== taskId || reply.request_id !== request.request_id ||
          typeof reply.continue !== 'boolean' ||
          !['verified','repairing','repair_exhausted','checker_error','timeout','integrity_error','deadline'].includes(reply.status) ||
          (reply.continue && (reply.status !== 'repairing' || typeof reply.feedback !== 'string')))
        throw new Error('invalid external acceptance reply');
      if (reply.continue) return {
        entries:[{type:'custom_message',customType:'external-acceptance',
          content:reply.feedback.slice(0,8000),display:true}], continue:true,
      };
      return undefined;
    } finally {pending = false;}
  });
}

export default (pi:PiLike) => install(pi);
