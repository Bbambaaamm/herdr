import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { createQuantumCore } from './machine-core.js';
import { createMachineDrone, createMachineCity } from './machine-entities.js';

const AGENTS = ['majak-hermes','majak-codex','quantlab-hermes','quantlab-codex'];
const vector = (x,y,z) => new THREE.Vector3(x,y,z);
const DRONE_STATE = {working:'working',blocked:'waiting_user',done:'complete',idle:'idle',unknown:'offline',offline:'offline'};
const DISCONNECTED = new Set(['offline','unavailable','unknown','disconnected']);

function safeLabelCenter(x, width, labelWidth, margin = 12) {
  const inset = Math.min(width / 2, labelWidth / 2 + margin);
  return Math.max(inset, Math.min(width - inset, x));
}

function visibleDroneSpread(aspect, fov, distance, scale, width) {
  const halfWidth = Math.tan(fov * Math.PI / 360) * distance * aspect;
  const labelMargin = 24 / width * halfWidth * 2;
  // Include the full machine silhouette and the greatest cosmetic X displacement.
  const available = Math.max(0, halfWidth - 1.4 * scale - .18 - labelMargin);
  return Math.min(aspect < 1 ? 2.48 : Math.min(5.35, aspect * 2.58), available);
}

export function createMachineScene(canvas, fallback) {
  const renderer = new THREE.WebGLRenderer({canvas, antialias:true, powerPreference:'high-performance'});
  const low = innerWidth < 760 || (navigator.deviceMemory && navigator.deviceMemory <= 4);
  let pixelRatio = Math.min(devicePixelRatio, low ? 1 : 1.5);
  renderer.setPixelRatio(pixelRatio);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.2;
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x020911);
  scene.fog = new THREE.FogExp2(0x07131c, .041);
  const camera = new THREE.PerspectiveCamera(35, 1, .1, 90);
  camera.position.set(.35,.55,13.8);
  camera.lookAt(0,.35,0);
  const pmrem = new THREE.PMREMGenerator(renderer);
  const environment = new RoomEnvironment();
  const envTexture = pmrem.fromScene(environment,.08).texture;
  scene.environment = envTexture;
  scene.environmentIntensity = .72;
  environment.dispose(); pmrem.dispose();
  scene.add(new THREE.HemisphereLight(0x8fc9df,0x05090d,.82));
  const key = new THREE.DirectionalLight(0xb8ddea,3.6); key.position.set(-5,7,8);scene.add(key);
  const fill = new THREE.DirectionalLight(0x3f9fbe,1.35);fill.position.set(5,1,6);scene.add(fill);
  const rim = new THREE.DirectionalLight(0x4fc7e8,4.4);rim.position.set(4,6,-6);scene.add(rim);
  const bottom = new THREE.PointLight(0xe3a04c,7.5,13,2);bottom.position.set(-1,-3,3);scene.add(bottom);
  const core = createQuantumCore({low});
  const corePivot = new THREE.Group();corePivot.position.set(0,.42,-.35);corePivot.add(core.group);scene.add(corePivot);
  const city = createMachineCity({low});scene.add(city.group);
  const drones = new Map();
  for(const [index,id] of AGENTS.entries()) {
    const drone=createMachineDrone({kind:id.endsWith('hermes')?'hermes':'codex',seed:index+71,low});
    drone.group.userData.agentId=id; drone.base=vector(0,0,0);drone.id=id;drone.status='offline';
    drone.group.traverse(object=>{object.userData.agentId=id;});scene.add(drone.group);drones.set(id,drone);
  }
  const taskRoot = new THREE.Group(); taskRoot.name = 'swarm-task-nodes'; scene.add(taskRoot);
  const taskNodes = new Map();
  const TASK_COLORS = { running: 0x73f2df, pending: 0xb99b6a, blocked: 0xff8c72, failed: 0xff5f52, done: 0x72c996 };
  const taskOrder = { running: 0, blocked: 1, failed: 2, pending: 3, done: 4 };
  let taskFocus = null, taskSelect = () => {};

  function disposeTaskNode(node) {
    taskRoot.remove(node.group);
    node.group.traverse(object => {
      object.geometry?.dispose();
      if (object.material) for (const material of Array.isArray(object.material) ? object.material : [object.material]) material.dispose();
    });
  }

  function makeTaskNode(id, status, index, clusterCount = 0) {
    const group = new THREE.Group(); group.name = clusterCount ? 'swarm-task-cluster' : `swarm-task-${id}`;
    const color = TASK_COLORS[status] || 0x9c9487;
    const body = new THREE.Mesh(
      clusterCount ? new THREE.DodecahedronGeometry(.22, 0) : new THREE.OctahedronGeometry(.16, 0),
      new THREE.MeshStandardMaterial({ color: 0x252b2d, emissive: color, emissiveIntensity: status === 'running' ? 1.8 : .75, metalness: .72, roughness: .28 })
    );
    const ring = new THREE.Mesh(new THREE.TorusGeometry(clusterCount ? .30 : .23, .012, 5, 20), new THREE.MeshBasicMaterial({ color, transparent: true, opacity: .7 }));
    ring.rotation.x = Math.PI / 2; group.add(body, ring);
    group.userData.taskId = clusterCount ? null : id; group.userData.clusterCount = clusterCount;
    group.traverse(object => { object.userData.taskId = clusterCount ? null : id; });
    const node = { id, status, index, clusterCount, group, body, ring, base: new THREE.Vector3() };
    taskRoot.add(group); return node;
  }

  function layoutTaskNodes() {
    const nodes = [...taskNodes.values()];
    const visibleCount = nodes.length;
    nodes.forEach((node, index) => {
      const ringIndex = index < 10 ? 0 : 1;
      const indexInRing = ringIndex ? index - 10 : index;
      const ringCount = ringIndex ? Math.max(1, visibleCount - 10) : Math.min(10, visibleCount);
      const angle = -Math.PI * .92 + (indexInRing / Math.max(1, ringCount - 1)) * Math.PI * 1.84;
      const rx = ringIndex ? 3.55 : 2.65, ry = ringIndex ? 2.38 : 1.82;
      node.base.set(Math.cos(angle) * rx, .42 + Math.sin(angle) * ry, ringIndex ? 1.48 : 1.18);
      node.group.position.copy(node.base);
      node.group.scale.setScalar(node.clusterCount ? .9 : .72);
    });
  }

  function setTaskRows(rows) {
    const ordered = [...(Array.isArray(rows) ? rows : [])].filter(row => row && row.status !== 'done')
      .sort((a, b) => (taskOrder[a.status] ?? 9) - (taskOrder[b.status] ?? 9) || (b.updated_at || 0) - (a.updated_at || 0) || String(a.task_id).localeCompare(String(b.task_id)));
    const limit = 20, visible = ordered.slice(0, limit), wanted = new Map(visible.map((row, index) => [row.task_id, { row, index }]));
    const overflow = Math.max(0, ordered.length - limit);
    if (overflow) wanted.set('__cluster__', { row: { task_id: '__cluster__', status: 'pending' }, index: visible.length, clusterCount: overflow });
    for (const [id, node] of [...taskNodes]) {
      if (!wanted.has(id)) { disposeTaskNode(node); taskNodes.delete(id); }
    }
    for (const [id, data] of wanted) {
      let node = taskNodes.get(id);
      if (!node || node.status !== data.row.status || node.clusterCount !== (data.clusterCount || 0)) {
        if (node) disposeTaskNode(node);
        node = makeTaskNode(id, data.row.status, data.index, data.clusterCount || 0); taskNodes.set(id, node);
      }
      node.index = data.index; node.status = data.row.status;
    }
    if (taskFocus && !taskNodes.has(taskFocus)) taskFocus = null;
    layoutTaskNodes(); dirty = true;
  }

  // No pre-baked communication: this geometry is visible exclusively in explicit demo events.
  const linkGeometry = new THREE.BufferGeometry();linkGeometry.setAttribute('position',new THREE.BufferAttribute(new Float32Array(65*3),3));
  const link = new THREE.Line(linkGeometry,new THREE.LineBasicMaterial({color:0x89ddb0,transparent:true,opacity:.32}));link.visible=false;scene.add(link);
  const packets = new THREE.InstancedMesh(new THREE.SphereGeometry(.028,6,4),new THREE.MeshBasicMaterial({color:0xbfffc7}),12);packets.visible=false;scene.add(packets);
  const packetMatrix=new THREE.Matrix4(), packetScale=vector(1,1,1), packetQ=new THREE.Quaternion();
  const composer = new EffectComposer(renderer);composer.addPass(new RenderPass(scene,camera));
  const bloom = new UnrealBloomPass(new THREE.Vector2(1,1),.38,.38,1.18);composer.addPass(bloom);composer.addPass(new OutputPass());
  let state='offline', reduced=matchMedia('(prefers-reduced-motion: reduce)').matches,active=true,lost=false,dirty=true;
  let demo={enabled:false,state:'idle',target:'majak-codex'},focus=null,select=()=>{},inspection=0;
  let clockTime=0,lastTime=0,frame=0,slowFrames=0,adapted=false;
  let pointerX=0,pointerY=0;
  let activity={running:0,pending:0,blocked:0,workingAgents:0,activeAgent:null};
  const raycaster=new THREE.Raycaster(),mouse=new THREE.Vector2(),projected=new THREE.Vector3();
  const visibleDrone=id=>{const drone=drones.get(id);return drone?.group.visible?drone:null;};
  function failScene(error) {
    if(lost)return;
    lost=true;cancelAnimationFrame(frame);frame=0;fallback.hidden=false;
    canvas.dispatchEvent(new CustomEvent('scene-unavailable',{bubbles:true}));
    if(error)console.error('Machine City renderer unavailable',error);
  }
  const resize=()=>{
    if(lost)return;
    try{
      const {width,height}=canvas.getBoundingClientRect();if(!width||!height)return;
      camera.aspect=width/height;camera.position.z=camera.aspect<1?17.6:13.8;camera.updateProjectionMatrix();camera.updateMatrixWorld();
      renderer.setSize(width,height,false);composer.setSize(width,height);
      const scale=camera.aspect<1?.48:.7;
      const direction=camera.getWorldDirection(vector(0,0,0));
      [...drones.values()].forEach((drone,i)=>{
        const z=i%2===0?.5:1.05;
        const spread=visibleDroneSpread(camera.aspect,camera.fov,Math.max(.1,camera.position.z-z-.25),scale,width);
        const centerX=camera.position.x+(z-camera.position.z)/direction.z*direction.x;
        drone.base.set(centerX+(i<2?-spread:spread),i%2===0?2.15:-1.1,z);
        drone.group.scale.setScalar(scale);drone.group.position.copy(drone.base);
      });layoutTaskNodes();dirty=true;
    }catch(error){failScene(error);}
  };
  const ro=new ResizeObserver(resize);ro.observe(canvas);
  function taskAtPointer(e){
    const r=canvas.getBoundingClientRect();if(!r.width||!r.height)return null;
    mouse.set((e.clientX-r.left)/r.width*2-1,-(e.clientY-r.top)/r.height*2+1);
    raycaster.setFromCamera(mouse,camera);
    const hit=raycaster.intersectObjects([...taskNodes.values()].map(node=>node.group),true)
      .find(intersection=>Boolean(intersection.object.userData.taskId));
    return hit?.object.userData.taskId||null;
  }
  canvas.addEventListener('pointermove',e=>{
    const r=canvas.getBoundingClientRect();pointerX=(e.clientX-r.left)/r.width-.5;pointerY=(e.clientY-r.top)/r.height-.5;
    const taskId=taskAtPointer(e);
    canvas.dispatchEvent(new CustomEvent('swarm-task-hover',{bubbles:true,detail:{taskId,x:e.clientX-r.left,y:e.clientY-r.top}}));
  });
  canvas.addEventListener('pointerleave',()=>{
    pointerX=0;pointerY=0;
    canvas.dispatchEvent(new CustomEvent('swarm-task-hover',{bubbles:true,detail:{taskId:null,x:0,y:0}}));
  });
  canvas.addEventListener('click',e=>{
    if(lost||!active)return;
    const r=canvas.getBoundingClientRect();if(!r.width||!r.height)return;
    mouse.set((e.clientX-r.left)/r.width*2-1,-(e.clientY-r.top)/r.height*2+1);
    raycaster.setFromCamera(mouse,camera);
    const targets=[...drones.values()].filter(d=>d.group.visible).map(d=>d.group).concat([...taskNodes.values()].map(node=>node.group));
    const hit=raycaster.intersectObjects(targets,true).find(intersection=>{
      for(let object=intersection.object;object;object=object.parent)if(!object.visible)return false;
      return Boolean(intersection.object.userData.agentId||intersection.object.userData.taskId);
    });
    if(hit){
      const taskId=hit.object.userData.taskId,agentId=hit.object.userData.agentId;
      if(taskId)taskSelect(taskId);else if(agentId)select(agentId);
    }
  });
  canvas.addEventListener('webglcontextlost',event=>{event.preventDefault();failScene();});
  // A clean reload rebuilds GPU resources; existing data remains accessible without that reload.
  canvas.addEventListener('webglcontextrestored',()=>{fallback.hidden=false;});
  document.addEventListener('visibilitychange',()=>{lastTime=0;dirty=true;});
  function projectLabels() {
    scene.updateMatrixWorld();camera.updateMatrixWorld();
    const rect=canvas.getBoundingClientRect();if(!rect.width||!rect.height)return;
    for(const [id,drone] of drones){
      const button=document.querySelector(`#film-view [data-agent="${id}"]`);if(!button||!drone.group.visible)continue;
      drone.group.getWorldPosition(projected);projected.y-=.78*drone.group.scale.x;projected.project(camera);
      const parentRect=button.offsetParent?.getBoundingClientRect()||rect;
      const x=safeLabelCenter((projected.x*.5+.5)*rect.width,rect.width,button.offsetWidth);
      button.style.setProperty('--agent-x',`${rect.left-parentRect.left+x}px`);
      button.style.setProperty('--agent-y',`${rect.top-parentRect.top+(-projected.y*.5+.5)*rect.height}px`);
    }
    const focusedTask=taskFocus?taskNodes.get(taskFocus):null;
    if(focusedTask){
      focusedTask.group.getWorldPosition(projected);projected.project(camera);
      canvas.dispatchEvent(new CustomEvent('swarm-task-focus-position',{bubbles:true,detail:{
        taskId:focusedTask.id,
        x:(projected.x*.5+.5)*rect.width,
        y:(-projected.y*.5+.5)*rect.height,
      }}));
    }else{
      canvas.dispatchEvent(new CustomEvent('swarm-task-focus-position',{bubbles:true,detail:{taskId:null,x:0,y:0}}));
    }
  }
  function draw(now){
    frame=0;
    if(lost)return;
    try{
    if(document.hidden||!active||(reduced&&!dirty)){frame=requestAnimationFrame(draw);return;}
    const delta=lastTime?Math.min((now-lastTime)/1000,.08):1/60;lastTime=now;
    if(!reduced)clockTime+=delta;
    const t=reduced?0:clockTime;
    const coreStill=reduced||DISCONNECTED.has(state);
    corePivot.rotation.y=inspection?inspection:(coreStill?0:t*.028+pointerX*.11);
    corePivot.rotation.x=coreStill?0:-pointerY*.07+Math.sin(t*.17)*.025;
    const workingAgents=[...drones.values()].filter(drone=>drone.group.visible&&drone.status==='working').length;
    core.update({time:t,state,reduced,delta,activity:{...activity,workingAgents}});city.update({time:t,reduced});
    let i=0;for(const drone of drones.values()){
      const phase=i*1.83;
      const droneState=demo.enabled?(drone.id===demo.target?state:'idle'):DRONE_STATE[drone.status]||'offline';
      drone.group.position.copy(drone.base);
      if(!reduced&&!DISCONNECTED.has(droneState)){drone.group.position.x+=Math.sin(t*.24+phase)*.18;drone.group.position.y+=Math.sin(t*.37+phase)*.15;drone.group.position.z+=Math.cos(t*.22+phase)*.25;}
      drone.group.rotation.y=drone.base.x<0?.3:-.3;
      drone.update({time:t,state:droneState,reduced,delta});i++;
    }
    let taskIndex=0;for(const node of taskNodes.values()){
      const phase=taskIndex*.73;
      node.group.position.copy(node.base);
      if(!reduced){
        node.group.position.y+=Math.sin(t*.42+phase)*.055;
        node.group.position.z+=Math.cos(t*.31+phase)*.08;
        node.ring.rotation.z=t*(node.status==='running'?.75:.18)+phase;
        node.group.rotation.y=t*.08+phase*.2;
      }else{node.ring.rotation.z=phase;node.group.rotation.y=0;}
      const selected=taskFocus===node.id;
      const baseScale=node.clusterCount?.9:.72;
      node.group.scale.setScalar(selected?baseScale*1.45:baseScale);
      node.body.material.emissiveIntensity=(node.status==='running'?1.8:.75)+(selected?.9:0);
      taskIndex++;
    }
    const liveTarget=activity.activeAgent?visibleDrone(activity.activeAgent):[...drones.values()].find(drone=>drone.group.visible&&['working','blocked'].includes(drone.status));
    const communicationTarget=demo.enabled?visibleDrone(demo.target):liveTarget;
    const communicationState=demo.enabled?state:((state==='waiting_user'||(activity.userBlocked||0)>0||communicationTarget?.status==='blocked')?'waiting_user':'working');
    const communication=Boolean(communicationTarget&&(demo.enabled?['delegating','waiting_result','complete','tool'].includes(state):['working','waiting_user'].includes(communicationState)));
    link.visible=communication;packets.visible=communication&&communicationState!=='waiting_user';
    if(communication){
      const end=communicationTarget.group.position;
      const curve=new THREE.QuadraticBezierCurve3(vector(end.x<0?-1.55:1.55,.5,.6),vector(end.x*.56,end.y-.42,2.05),end.clone());
      const points=curve.getPoints(64);linkGeometry.setFromPoints(points);
      const linkColor=communicationState==='waiting_user'?0xff7864:(end.x<0?0xffb657:0x73f2df);
      link.material.color.setHex(linkColor);packets.material.color.setHex(linkColor);
      link.material.opacity=communicationState==='waiting_user'?.2:.43;
      for(let n=0;n<12;n++){let f=reduced?(n+1)/13:(t*(.3+Math.min(activity.running||0,2)*.08)+n/12)%1;if(demo.enabled&&state==='complete')f=1-f;packetMatrix.compose(curve.getPoint(f),packetQ,packetScale);packets.setMatrixAt(n,packetMatrix);}packets.instanceMatrix.needsUpdate=true;
    }
    projectLabels();
    composer.render();
    dirty=false;
    if(!reduced&&delta>.048)slowFrames++;else slowFrames=Math.max(0,slowFrames-1);
    if(slowFrames>90&&!adapted){pixelRatio=1;renderer.setPixelRatio(1);composer.setPixelRatio(1);bloom.enabled=false;adapted=true;resize();}
    }catch(error){failScene(error);return;}
    if(!lost)frame=requestAnimationFrame(draw);
  }
  resize();if(!lost)frame=requestAnimationFrame(draw);
  const inspect=document.querySelector('#inspect-model');
  inspect?.addEventListener('click',()=>{inspection=inspection===0?.6:inspection===.6?1.2:0;inspect.textContent=inspection===0?'Prohlédnout jádro':inspection===.6?'Jádro ze tří čtvrtin':'Jádro z boku';dirty=true;});
  return {
    setState(next){if(state!==next){state=next;dirty=true;}},setReduced(value){reduced=value;dirty=true;lastTime=0;},
    setActive(value){active=value;dirty=true;lastTime=0;if(value)resize();},setGaze(){},
    setActivity(value){activity={...activity,...value};core.setActivity(activity);dirty=true;},
    setAgents(rows){for(const drone of drones.values()){const row=rows.find(r=>(r.id||r.agent)===drone.id);drone.status=row?.status||'offline';drone.group.visible=Boolean(row)&&row.visible!==false;}if(!visibleDrone(focus))focus=null;if(!visibleDrone(demo.target))demo.target=null;dirty=true;},
    setTasks(rows){setTaskRows(rows);},
    focusAgent(id){focus=visibleDrone(id)?id:null;dirty=true;},
    focusTask(id){taskFocus=id&&taskNodes.has(id)?id:null;dirty=true;},
    setDemo(value){demo={...demo,...value};if(!visibleDrone(demo.target))demo.target=null;dirty=true;},
    onSelect(callback){select=callback;},onTaskSelect(callback){taskSelect=callback;},
    diagnostics(){return {geometry:'true-3d',state,reduced,active,contextLost:lost,quality:adapted?'adaptive-low':low?'low':'high',core:core.diagnostics(),drones:[...drones.values()].map(d=>({id:d.id,position:d.group.position.toArray(),...d.diagnostics()})),tasks:[...taskNodes.values()].map(node=>({id:node.id,status:node.status,clusterCount:node.clusterCount,position:node.group.position.toArray()})),drawCalls:renderer.info.render.calls,triangles:renderer.info.render.triangles};},
    quality:low?'Úsporná':'Vysoká',
    dispose(){cancelAnimationFrame(frame);ro.disconnect();scene.traverse(o=>{o.geometry?.dispose();if(o.material){for(const m of Array.isArray(o.material)?o.material:[o.material])m.dispose();}});envTexture.dispose();composer.dispose();renderer.dispose();}
  };
}