(()=>{var ea=new Uint32Array(256),pl=ea.length;function ht(){let i=globalThis.crypto;if(!i||typeof i.getRandomValues!="function")throw new Error("secure_random_unavailable");return pl>=ea.length&&(i.getRandomValues(ea),pl=0),ea[pl++]/4294967296}var gu=0,jl=1,_u=2;var Rr=1,xu=2,Cs=3,Ti=0,en=1,Jn=2,Rn=0,Rs=1,Gi=2,Jl=3,Kl=4,vu=5;var Wi=100,yu=101,bu=102,Mu=103,Su=104,Tu=200,Eu=201,wu=202,Au=203,Ql=204,ec=205,Cu=206,Ru=207,Pu=208,Iu=209,Lu=210,Nu=211,Du=212,Uu=213,Fu=214,Aa=0,Ca=1,Ra=2,ps=3,Pa=4,Ia=5,La=6,Na=7,uo=0,ku=1,Ou=2,zn=0,Pr=1,Ir=2,Lr=3,qi=4,Nr=5,Dr=6,Ur=7;var tc=300,Ei=301,Xi=302,ho=303,fo=304,Fr=306,Da=1e3,qn=1001,Ua=1002,Yt=1003,Bu=1004;var kr=1005;var Qt=1006,po=1007;var wi=1008;var xn=1009,nc=1010,ic=1011,Ps=1012,mo=1013,Vn=1014,Pn=1015,tn=1016,go=1017,_o=1018,Is=1020,sc=35902,rc=35899,ac=1021,oc=1022,In=1023,Xn=1026,Ai=1027,xo=1028,vo=1029,Ci=1030,yo=1031;var bo=1033,Or=33776,Br=33777,zr=33778,Vr=33779,Mo=35840,So=35841,To=35842,Eo=35843,wo=36196,Ao=37492,Co=37496,Ro=37488,Po=37489,Hr=37490,Io=37491,Lo=37808,No=37809,Do=37810,Uo=37811,Fo=37812,ko=37813,Oo=37814,Bo=37815,zo=37816,Vo=37817,Ho=37818,Go=37819,Wo=37820,qo=37821,Xo=36492,$o=36494,Yo=36495,Zo=36283,jo=36284,Gr=36285,Jo=36286;var nr=2300,Fa=2301,Ea=2302,zl=2303,Vl=2400,Hl=2401,Gl=2402;var zu=3200;var Wr=0,Vu=1,li="",cn="srgb",ir="srgb-linear",sr="linear",St="srgb";var wa=7680;var Hu=519,Gu=512,Wu=513,qu=514,Ko=515,Xu=516,$u=517,Qo=518,Yu=519,Zu=35044,lc=35048;var cc="300 es",kn=2e3,ms=2001;function Yh(i){for(let e=i.length-1;e>=0;--e)if(i[e]>=65535)return!0;return!1}function Zh(i){return ArrayBuffer.isView(i)&&!(i instanceof DataView)}function rr(i){return document.createElementNS("http://www.w3.org/1999/xhtml",i)}function ju(){let i=rr("canvas");return i.style.display="block",i}var kc={},gs=null;function uc(...i){let e="THREE."+i.shift();gs?gs("log",e,...i):console.log(e,...i)}function Ju(i){let e=i[0];if(typeof e=="string"&&e.startsWith("TSL:")){let t=i[1];t&&t.isStackTrace?i[0]+=" "+t.getLocation():i[1]='Stack trace not available. Enable "THREE.Node.captureStackTrace" to capture stack traces.'}return i}function je(...i){i=Ju(i);let e="THREE."+i.shift();if(gs)gs("warn",e,...i);else{let t=i[0];t&&t.isStackTrace?console.warn(t.getError(e)):console.warn(e,...i)}}function nt(...i){i=Ju(i);let e="THREE."+i.shift();if(gs)gs("error",e,...i);else{let t=i[0];t&&t.isStackTrace?console.error(t.getError(e)):console.error(e,...i)}}function ki(...i){let e=i.join(" ");e in kc||(kc[e]=!0,je(...i))}function Ku(i,e,t){return new Promise(function(n,s){function r(){switch(i.clientWaitSync(e,i.SYNC_FLUSH_COMMANDS_BIT,0)){case i.WAIT_FAILED:s();break;case i.TIMEOUT_EXPIRED:setTimeout(r,t);break;default:n()}}setTimeout(r,t)})}var Qu={[Aa]:Ca,[Ra]:La,[Pa]:Na,[ps]:Ia,[Ca]:Aa,[La]:Ra,[Na]:Pa,[Ia]:ps},$n=class{addEventListener(e,t){this._listeners===void 0&&(this._listeners={});let n=this._listeners;n[e]===void 0&&(n[e]=[]),n[e].indexOf(t)===-1&&n[e].push(t)}hasEventListener(e,t){let n=this._listeners;return n===void 0?!1:n[e]!==void 0&&n[e].indexOf(t)!==-1}removeEventListener(e,t){let n=this._listeners;if(n===void 0)return;let s=n[e];if(s!==void 0){let r=s.indexOf(t);r!==-1&&s.splice(r,1)}}dispatchEvent(e){let t=this._listeners;if(t===void 0)return;let n=t[e.type];if(n!==void 0){e.target=this;let s=n.slice(0);for(let r=0,a=s.length;r<a;r++)s[r].call(this,e);e.target=null}}},rn=["00","01","02","03","04","05","06","07","08","09","0a","0b","0c","0d","0e","0f","10","11","12","13","14","15","16","17","18","19","1a","1b","1c","1d","1e","1f","20","21","22","23","24","25","26","27","28","29","2a","2b","2c","2d","2e","2f","30","31","32","33","34","35","36","37","38","39","3a","3b","3c","3d","3e","3f","40","41","42","43","44","45","46","47","48","49","4a","4b","4c","4d","4e","4f","50","51","52","53","54","55","56","57","58","59","5a","5b","5c","5d","5e","5f","60","61","62","63","64","65","66","67","68","69","6a","6b","6c","6d","6e","6f","70","71","72","73","74","75","76","77","78","79","7a","7b","7c","7d","7e","7f","80","81","82","83","84","85","86","87","88","89","8a","8b","8c","8d","8e","8f","90","91","92","93","94","95","96","97","98","99","9a","9b","9c","9d","9e","9f","a0","a1","a2","a3","a4","a5","a6","a7","a8","a9","aa","ab","ac","ad","ae","af","b0","b1","b2","b3","b4","b5","b6","b7","b8","b9","ba","bb","bc","bd","be","bf","c0","c1","c2","c3","c4","c5","c6","c7","c8","c9","ca","cb","cc","cd","ce","cf","d0","d1","d2","d3","d4","d5","d6","d7","d8","d9","da","db","dc","dd","de","df","e0","e1","e2","e3","e4","e5","e6","e7","e8","e9","ea","eb","ec","ed","ee","ef","f0","f1","f2","f3","f4","f5","f6","f7","f8","f9","fa","fb","fc","fd","fe","ff"],Oc=1234567,Ks=Math.PI/180,_s=180/Math.PI;function Ls(){let i=ht()*4294967295|0,e=ht()*4294967295|0,t=ht()*4294967295|0,n=ht()*4294967295|0;return(rn[i&255]+rn[i>>8&255]+rn[i>>16&255]+rn[i>>24&255]+"-"+rn[e&255]+rn[e>>8&255]+"-"+rn[e>>16&15|64]+rn[e>>24&255]+"-"+rn[t&63|128]+rn[t>>8&255]+"-"+rn[t>>16&255]+rn[t>>24&255]+rn[n&255]+rn[n>>8&255]+rn[n>>16&255]+rn[n>>24&255]).toLowerCase()}function mt(i,e,t){return Math.max(e,Math.min(t,i))}function hc(i,e){return(i%e+e)%e}function jh(i,e,t,n,s){return n+(i-e)*(s-n)/(t-e)}function Jh(i,e,t){return i!==e?(t-i)/(e-i):0}function Qs(i,e,t){return(1-t)*i+t*e}function Kh(i,e,t,n){return Qs(i,e,1-Math.exp(-t*n))}function Qh(i,e=1){return e-Math.abs(hc(i,e*2)-e)}function ed(i,e,t){return i<=e?0:i>=t?1:(i=(i-e)/(t-e),i*i*(3-2*i))}function td(i,e,t){return i<=e?0:i>=t?1:(i=(i-e)/(t-e),i*i*i*(i*(i*6-15)+10))}function nd(i,e){return i+Math.floor(ht()*(e-i+1))}function id(i,e){return i+ht()*(e-i)}function sd(i){return i*(.5-ht())}function rd(i){i!==void 0&&(Oc=i);let e=Oc+=1831565813;return e=Math.imul(e^e>>>15,e|1),e^=e+Math.imul(e^e>>>7,e|61),((e^e>>>14)>>>0)/4294967296}function ad(i){return i*Ks}function od(i){return i*_s}function ld(i){return i>0&&Number.isInteger(i)&&2**Math.round(Math.log2(i))===i}function cd(i){return Math.pow(2,Math.ceil(Math.log(i)/Math.LN2))}function ud(i){return Math.pow(2,Math.floor(Math.log(i)/Math.LN2))}function hd(i,e,t,n,s){let r=Math.cos,a=Math.sin,o=r(t/2),l=a(t/2),c=r((e+n)/2),h=a((e+n)/2),f=r((e-n)/2),u=a((e-n)/2),d=r((n-e)/2),g=a((n-e)/2);switch(s){case"XYX":i.set(o*h,l*f,l*u,o*c);break;case"YZY":i.set(l*u,o*h,l*f,o*c);break;case"ZXZ":i.set(l*f,l*u,o*h,o*c);break;case"XZX":i.set(o*h,l*g,l*d,o*c);break;case"YXY":i.set(l*d,o*h,l*g,o*c);break;case"ZYZ":i.set(l*g,l*d,o*h,o*c);break;default:je("MathUtils: .setQuaternionFromProperEuler() encountered an unknown order: "+s)}}function ds(i,e){switch(e.constructor){case Float32Array:return i;case Uint32Array:return i/4294967295;case Uint16Array:return i/65535;case Uint8Array:case Uint8ClampedArray:return i/255;case Int32Array:return Math.max(i/2147483647,-1);case Int16Array:return Math.max(i/32767,-1);case Int8Array:return Math.max(i/127,-1);default:throw new Error("THREE.MathUtils: Invalid component type.")}}function ln(i,e){switch(e.constructor){case Float32Array:return i;case Uint32Array:return Math.round(i*4294967295);case Uint16Array:return Math.round(i*65535);case Uint8Array:case Uint8ClampedArray:return Math.round(i*255);case Int32Array:return Math.round(i*2147483647);case Int16Array:return Math.round(i*32767);case Int8Array:return Math.round(i*127);default:throw new Error("THREE.MathUtils: Invalid component type.")}}var el={DEG2RAD:Ks,RAD2DEG:_s,generateUUID:Ls,clamp:mt,euclideanModulo:hc,mapLinear:jh,inverseLerp:Jh,lerp:Qs,damp:Kh,pingpong:Qh,smoothstep:ed,smootherstep:td,randInt:nd,randFloat:id,randFloatSpread:sd,seededRandom:rd,degToRad:ad,radToDeg:od,isPowerOfTwo:ld,ceilPowerOfTwo:cd,floorPowerOfTwo:ud,setQuaternionFromProperEuler:hd,normalize:ln,denormalize:ds},De=class i{static{i.prototype.isVector2=!0}constructor(e=0,t=0){this.x=e,this.y=t}get width(){return this.x}set width(e){this.x=e}get height(){return this.y}set height(e){this.y=e}set(e,t){return this.x=e,this.y=t,this}setScalar(e){return this.x=e,this.y=e,this}setX(e){return this.x=e,this}setY(e){return this.y=e,this}setComponent(e,t){switch(e){case 0:this.x=t;break;case 1:this.y=t;break;default:throw new Error("THREE.Vector2: index is out of range: "+e)}return this}getComponent(e){switch(e){case 0:return this.x;case 1:return this.y;default:throw new Error("THREE.Vector2: index is out of range: "+e)}}clone(){return new this.constructor(this.x,this.y)}copy(e){return this.x=e.x,this.y=e.y,this}add(e){return this.x+=e.x,this.y+=e.y,this}addScalar(e){return this.x+=e,this.y+=e,this}addVectors(e,t){return this.x=e.x+t.x,this.y=e.y+t.y,this}addScaledVector(e,t){return this.x+=e.x*t,this.y+=e.y*t,this}sub(e){return this.x-=e.x,this.y-=e.y,this}subScalar(e){return this.x-=e,this.y-=e,this}subVectors(e,t){return this.x=e.x-t.x,this.y=e.y-t.y,this}multiply(e){return this.x*=e.x,this.y*=e.y,this}multiplyScalar(e){return this.x*=e,this.y*=e,this}divide(e){return this.x/=e.x,this.y/=e.y,this}divideScalar(e){return this.multiplyScalar(1/e)}applyMatrix3(e){let t=this.x,n=this.y,s=e.elements;return this.x=s[0]*t+s[3]*n+s[6],this.y=s[1]*t+s[4]*n+s[7],this}min(e){return this.x=Math.min(this.x,e.x),this.y=Math.min(this.y,e.y),this}max(e){return this.x=Math.max(this.x,e.x),this.y=Math.max(this.y,e.y),this}clamp(e,t){return this.x=mt(this.x,e.x,t.x),this.y=mt(this.y,e.y,t.y),this}clampScalar(e,t){return this.x=mt(this.x,e,t),this.y=mt(this.y,e,t),this}clampLength(e,t){let n=this.length();return this.divideScalar(n||1).multiplyScalar(mt(n,e,t))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this}negate(){return this.x=-this.x,this.y=-this.y,this}dot(e){return this.x*e.x+this.y*e.y}cross(e){return this.x*e.y-this.y*e.x}lengthSq(){return this.x*this.x+this.y*this.y}length(){return Math.sqrt(this.x*this.x+this.y*this.y)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)}normalize(){return this.divideScalar(this.length()||1)}angle(){return Math.atan2(-this.y,-this.x)+Math.PI}angleTo(e){let t=Math.sqrt(this.lengthSq()*e.lengthSq());if(t===0)return Math.PI/2;let n=this.dot(e)/t;return Math.acos(mt(n,-1,1))}distanceTo(e){return Math.sqrt(this.distanceToSquared(e))}distanceToSquared(e){let t=this.x-e.x,n=this.y-e.y;return t*t+n*n}manhattanDistanceTo(e){return Math.abs(this.x-e.x)+Math.abs(this.y-e.y)}setLength(e){return this.normalize().multiplyScalar(e)}lerp(e,t){return this.x+=(e.x-this.x)*t,this.y+=(e.y-this.y)*t,this}lerpVectors(e,t,n){return this.x=e.x+(t.x-e.x)*n,this.y=e.y+(t.y-e.y)*n,this}equals(e){return e.x===this.x&&e.y===this.y}fromArray(e,t=0){return this.x=e[t],this.y=e[t+1],this}toArray(e=[],t=0){return e[t]=this.x,e[t+1]=this.y,e}fromBufferAttribute(e,t){return this.x=e.getX(t),this.y=e.getY(t),this}rotateAround(e,t){let n=Math.cos(t),s=Math.sin(t),r=this.x-e.x,a=this.y-e.y;return this.x=r*n-a*s+e.x,this.y=r*s+a*n+e.y,this}random(){return this.x=ht(),this.y=ht(),this}*[Symbol.iterator](){yield this.x,yield this.y}},Gt=class{constructor(e=0,t=0,n=0,s=1){this.isQuaternion=!0,this._x=e,this._y=t,this._z=n,this._w=s}static slerpFlat(e,t,n,s,r,a,o){let l=n[s+0],c=n[s+1],h=n[s+2],f=n[s+3],u=r[a+0],d=r[a+1],g=r[a+2],b=r[a+3];if(f!==b||l!==u||c!==d||h!==g){let m=l*u+c*d+h*g+f*b;m<0&&(u=-u,d=-d,g=-g,b=-b,m=-m);let p=1-o;if(m<.9995){let E=Math.acos(m),C=Math.sin(E);p=Math.sin(p*E)/C,o=Math.sin(o*E)/C,l=l*p+u*o,c=c*p+d*o,h=h*p+g*o,f=f*p+b*o}else{l=l*p+u*o,c=c*p+d*o,h=h*p+g*o,f=f*p+b*o;let E=1/Math.sqrt(l*l+c*c+h*h+f*f);l*=E,c*=E,h*=E,f*=E}}e[t]=l,e[t+1]=c,e[t+2]=h,e[t+3]=f}static multiplyQuaternionsFlat(e,t,n,s,r,a){let o=n[s],l=n[s+1],c=n[s+2],h=n[s+3],f=r[a],u=r[a+1],d=r[a+2],g=r[a+3];return e[t]=o*g+h*f+l*d-c*u,e[t+1]=l*g+h*u+c*f-o*d,e[t+2]=c*g+h*d+o*u-l*f,e[t+3]=h*g-o*f-l*u-c*d,e}get x(){return this._x}set x(e){this._x=e,this._onChangeCallback()}get y(){return this._y}set y(e){this._y=e,this._onChangeCallback()}get z(){return this._z}set z(e){this._z=e,this._onChangeCallback()}get w(){return this._w}set w(e){this._w=e,this._onChangeCallback()}set(e,t,n,s){return this._x=e,this._y=t,this._z=n,this._w=s,this._onChangeCallback(),this}clone(){return new this.constructor(this._x,this._y,this._z,this._w)}copy(e){return this._x=e.x,this._y=e.y,this._z=e.z,this._w=e.w,this._onChangeCallback(),this}setFromEuler(e,t=!0){let n=e._x,s=e._y,r=e._z,a=e._order,o=Math.cos,l=Math.sin,c=o(n/2),h=o(s/2),f=o(r/2),u=l(n/2),d=l(s/2),g=l(r/2);switch(a){case"XYZ":this._x=u*h*f+c*d*g,this._y=c*d*f-u*h*g,this._z=c*h*g+u*d*f,this._w=c*h*f-u*d*g;break;case"YXZ":this._x=u*h*f+c*d*g,this._y=c*d*f-u*h*g,this._z=c*h*g-u*d*f,this._w=c*h*f+u*d*g;break;case"ZXY":this._x=u*h*f-c*d*g,this._y=c*d*f+u*h*g,this._z=c*h*g+u*d*f,this._w=c*h*f-u*d*g;break;case"ZYX":this._x=u*h*f-c*d*g,this._y=c*d*f+u*h*g,this._z=c*h*g-u*d*f,this._w=c*h*f+u*d*g;break;case"YZX":this._x=u*h*f+c*d*g,this._y=c*d*f+u*h*g,this._z=c*h*g-u*d*f,this._w=c*h*f-u*d*g;break;case"XZY":this._x=u*h*f-c*d*g,this._y=c*d*f-u*h*g,this._z=c*h*g+u*d*f,this._w=c*h*f+u*d*g;break;default:je("Quaternion: .setFromEuler() encountered an unknown order: "+a)}return t===!0&&this._onChangeCallback(),this}setFromAxisAngle(e,t){let n=t/2,s=Math.sin(n);return this._x=e.x*s,this._y=e.y*s,this._z=e.z*s,this._w=Math.cos(n),this._onChangeCallback(),this}setFromRotationMatrix(e){let t=e.elements,n=t[0],s=t[4],r=t[8],a=t[1],o=t[5],l=t[9],c=t[2],h=t[6],f=t[10],u=n+o+f;if(u>0){let d=.5/Math.sqrt(u+1);this._w=.25/d,this._x=(h-l)*d,this._y=(r-c)*d,this._z=(a-s)*d}else if(n>o&&n>f){let d=2*Math.sqrt(1+n-o-f);this._w=(h-l)/d,this._x=.25*d,this._y=(s+a)/d,this._z=(r+c)/d}else if(o>f){let d=2*Math.sqrt(1+o-n-f);this._w=(r-c)/d,this._x=(s+a)/d,this._y=.25*d,this._z=(l+h)/d}else{let d=2*Math.sqrt(1+f-n-o);this._w=(a-s)/d,this._x=(r+c)/d,this._y=(l+h)/d,this._z=.25*d}return this._onChangeCallback(),this}setFromUnitVectors(e,t){let n=e.dot(t)+1;return n<1e-8?(n=0,Math.abs(e.x)>Math.abs(e.z)?(this._x=-e.y,this._y=e.x,this._z=0,this._w=n):(this._x=0,this._y=-e.z,this._z=e.y,this._w=n)):(this._x=e.y*t.z-e.z*t.y,this._y=e.z*t.x-e.x*t.z,this._z=e.x*t.y-e.y*t.x,this._w=n),this.normalize()}angleTo(e){return 2*Math.acos(Math.abs(mt(this.dot(e),-1,1)))}rotateTowards(e,t){let n=this.angleTo(e);if(n===0)return this;let s=Math.min(1,t/n);return this.slerp(e,s),this}identity(){return this.set(0,0,0,1)}invert(){return this.conjugate()}conjugate(){return this._x*=-1,this._y*=-1,this._z*=-1,this._onChangeCallback(),this}dot(e){return this._x*e._x+this._y*e._y+this._z*e._z+this._w*e._w}lengthSq(){return this._x*this._x+this._y*this._y+this._z*this._z+this._w*this._w}length(){return Math.sqrt(this._x*this._x+this._y*this._y+this._z*this._z+this._w*this._w)}normalize(){let e=this.length();return e===0?(this._x=0,this._y=0,this._z=0,this._w=1):(e=1/e,this._x=this._x*e,this._y=this._y*e,this._z=this._z*e,this._w=this._w*e),this._onChangeCallback(),this}multiply(e){return this.multiplyQuaternions(this,e)}premultiply(e){return this.multiplyQuaternions(e,this)}multiplyQuaternions(e,t){let n=e._x,s=e._y,r=e._z,a=e._w,o=t._x,l=t._y,c=t._z,h=t._w;return this._x=n*h+a*o+s*c-r*l,this._y=s*h+a*l+r*o-n*c,this._z=r*h+a*c+n*l-s*o,this._w=a*h-n*o-s*l-r*c,this._onChangeCallback(),this}slerp(e,t){let n=e._x,s=e._y,r=e._z,a=e._w,o=this.dot(e);o<0&&(n=-n,s=-s,r=-r,a=-a,o=-o);let l=1-t;if(o<.9995){let c=Math.acos(o),h=Math.sin(c);l=Math.sin(l*c)/h,t=Math.sin(t*c)/h,this._x=this._x*l+n*t,this._y=this._y*l+s*t,this._z=this._z*l+r*t,this._w=this._w*l+a*t,this._onChangeCallback()}else this._x=this._x*l+n*t,this._y=this._y*l+s*t,this._z=this._z*l+r*t,this._w=this._w*l+a*t,this.normalize();return this}slerpQuaternions(e,t,n){return this.copy(e).slerp(t,n)}random(){let e=2*Math.PI*ht(),t=2*Math.PI*ht(),n=ht(),s=Math.sqrt(1-n),r=Math.sqrt(n);return this.set(s*Math.sin(e),s*Math.cos(e),r*Math.sin(t),r*Math.cos(t))}equals(e){return e._x===this._x&&e._y===this._y&&e._z===this._z&&e._w===this._w}fromArray(e,t=0){return this._x=e[t],this._y=e[t+1],this._z=e[t+2],this._w=e[t+3],this._onChangeCallback(),this}toArray(e=[],t=0){return e[t]=this._x,e[t+1]=this._y,e[t+2]=this._z,e[t+3]=this._w,e}fromBufferAttribute(e,t){return this._x=e.getX(t),this._y=e.getY(t),this._z=e.getZ(t),this._w=e.getW(t),this._onChangeCallback(),this}toJSON(){return this.toArray()}_onChange(e){return this._onChangeCallback=e,this}_onChangeCallback(){}*[Symbol.iterator](){yield this._x,yield this._y,yield this._z,yield this._w}},U=class i{static{i.prototype.isVector3=!0}constructor(e=0,t=0,n=0){this.x=e,this.y=t,this.z=n}set(e,t,n){return n===void 0&&(n=this.z),this.x=e,this.y=t,this.z=n,this}setScalar(e){return this.x=e,this.y=e,this.z=e,this}setX(e){return this.x=e,this}setY(e){return this.y=e,this}setZ(e){return this.z=e,this}setComponent(e,t){switch(e){case 0:this.x=t;break;case 1:this.y=t;break;case 2:this.z=t;break;default:throw new Error("THREE.Vector3: index is out of range: "+e)}return this}getComponent(e){switch(e){case 0:return this.x;case 1:return this.y;case 2:return this.z;default:throw new Error("THREE.Vector3: index is out of range: "+e)}}clone(){return new this.constructor(this.x,this.y,this.z)}copy(e){return this.x=e.x,this.y=e.y,this.z=e.z,this}add(e){return this.x+=e.x,this.y+=e.y,this.z+=e.z,this}addScalar(e){return this.x+=e,this.y+=e,this.z+=e,this}addVectors(e,t){return this.x=e.x+t.x,this.y=e.y+t.y,this.z=e.z+t.z,this}addScaledVector(e,t){return this.x+=e.x*t,this.y+=e.y*t,this.z+=e.z*t,this}sub(e){return this.x-=e.x,this.y-=e.y,this.z-=e.z,this}subScalar(e){return this.x-=e,this.y-=e,this.z-=e,this}subVectors(e,t){return this.x=e.x-t.x,this.y=e.y-t.y,this.z=e.z-t.z,this}multiply(e){return this.x*=e.x,this.y*=e.y,this.z*=e.z,this}multiplyScalar(e){return this.x*=e,this.y*=e,this.z*=e,this}multiplyVectors(e,t){return this.x=e.x*t.x,this.y=e.y*t.y,this.z=e.z*t.z,this}applyEuler(e){return this.applyQuaternion(Bc.setFromEuler(e))}applyAxisAngle(e,t){return this.applyQuaternion(Bc.setFromAxisAngle(e,t))}applyMatrix3(e){let t=this.x,n=this.y,s=this.z,r=e.elements;return this.x=r[0]*t+r[3]*n+r[6]*s,this.y=r[1]*t+r[4]*n+r[7]*s,this.z=r[2]*t+r[5]*n+r[8]*s,this}applyNormalMatrix(e){return this.applyMatrix3(e).normalize()}applyMatrix4(e){let t=this.x,n=this.y,s=this.z,r=e.elements,a=1/(r[3]*t+r[7]*n+r[11]*s+r[15]);return this.x=(r[0]*t+r[4]*n+r[8]*s+r[12])*a,this.y=(r[1]*t+r[5]*n+r[9]*s+r[13])*a,this.z=(r[2]*t+r[6]*n+r[10]*s+r[14])*a,this}applyQuaternion(e){let t=this.x,n=this.y,s=this.z,r=e.x,a=e.y,o=e.z,l=e.w,c=2*(a*s-o*n),h=2*(o*t-r*s),f=2*(r*n-a*t);return this.x=t+l*c+a*f-o*h,this.y=n+l*h+o*c-r*f,this.z=s+l*f+r*h-a*c,this}project(e){return this.applyMatrix4(e.matrixWorldInverse).applyMatrix4(e.projectionMatrix)}unproject(e){return this.applyMatrix4(e.projectionMatrixInverse).applyMatrix4(e.matrixWorld)}transformDirection(e){let t=this.x,n=this.y,s=this.z,r=e.elements;return this.x=r[0]*t+r[4]*n+r[8]*s,this.y=r[1]*t+r[5]*n+r[9]*s,this.z=r[2]*t+r[6]*n+r[10]*s,this.normalize()}divide(e){return this.x/=e.x,this.y/=e.y,this.z/=e.z,this}divideScalar(e){return this.multiplyScalar(1/e)}min(e){return this.x=Math.min(this.x,e.x),this.y=Math.min(this.y,e.y),this.z=Math.min(this.z,e.z),this}max(e){return this.x=Math.max(this.x,e.x),this.y=Math.max(this.y,e.y),this.z=Math.max(this.z,e.z),this}clamp(e,t){return this.x=mt(this.x,e.x,t.x),this.y=mt(this.y,e.y,t.y),this.z=mt(this.z,e.z,t.z),this}clampScalar(e,t){return this.x=mt(this.x,e,t),this.y=mt(this.y,e,t),this.z=mt(this.z,e,t),this}clampLength(e,t){let n=this.length();return this.divideScalar(n||1).multiplyScalar(mt(n,e,t))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this.z=Math.floor(this.z),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this.z=Math.ceil(this.z),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this.z=Math.round(this.z),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this.z=Math.trunc(this.z),this}negate(){return this.x=-this.x,this.y=-this.y,this.z=-this.z,this}dot(e){return this.x*e.x+this.y*e.y+this.z*e.z}lengthSq(){return this.x*this.x+this.y*this.y+this.z*this.z}length(){return Math.sqrt(this.x*this.x+this.y*this.y+this.z*this.z)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)+Math.abs(this.z)}normalize(){return this.divideScalar(this.length()||1)}setLength(e){return this.normalize().multiplyScalar(e)}lerp(e,t){return this.x+=(e.x-this.x)*t,this.y+=(e.y-this.y)*t,this.z+=(e.z-this.z)*t,this}lerpVectors(e,t,n){return this.x=e.x+(t.x-e.x)*n,this.y=e.y+(t.y-e.y)*n,this.z=e.z+(t.z-e.z)*n,this}cross(e){return this.crossVectors(this,e)}crossVectors(e,t){let n=e.x,s=e.y,r=e.z,a=t.x,o=t.y,l=t.z;return this.x=s*l-r*o,this.y=r*a-n*l,this.z=n*o-s*a,this}projectOnVector(e){let t=e.lengthSq();if(t===0)return this.set(0,0,0);let n=e.dot(this)/t;return this.copy(e).multiplyScalar(n)}projectOnPlane(e){return ml.copy(this).projectOnVector(e),this.sub(ml)}reflect(e){return this.sub(ml.copy(e).multiplyScalar(2*this.dot(e)))}angleTo(e){let t=Math.sqrt(this.lengthSq()*e.lengthSq());if(t===0)return Math.PI/2;let n=this.dot(e)/t;return Math.acos(mt(n,-1,1))}distanceTo(e){return Math.sqrt(this.distanceToSquared(e))}distanceToSquared(e){let t=this.x-e.x,n=this.y-e.y,s=this.z-e.z;return t*t+n*n+s*s}manhattanDistanceTo(e){return Math.abs(this.x-e.x)+Math.abs(this.y-e.y)+Math.abs(this.z-e.z)}setFromSpherical(e){return this.setFromSphericalCoords(e.radius,e.phi,e.theta)}setFromSphericalCoords(e,t,n){let s=Math.sin(t)*e;return this.x=s*Math.sin(n),this.y=Math.cos(t)*e,this.z=s*Math.cos(n),this}setFromCylindrical(e){return this.setFromCylindricalCoords(e.radius,e.theta,e.y)}setFromCylindricalCoords(e,t,n){return this.x=e*Math.sin(t),this.y=n,this.z=e*Math.cos(t),this}setFromMatrixPosition(e){let t=e.elements;return this.x=t[12],this.y=t[13],this.z=t[14],this}setFromMatrixScale(e){let t=this.setFromMatrixColumn(e,0).length(),n=this.setFromMatrixColumn(e,1).length(),s=this.setFromMatrixColumn(e,2).length();return this.x=t,this.y=n,this.z=s,this}setFromMatrixColumn(e,t){return this.fromArray(e.elements,t*4)}setFromMatrix3Column(e,t){return this.fromArray(e.elements,t*3)}setFromEuler(e){return this.x=e._x,this.y=e._y,this.z=e._z,this}setFromColor(e){return this.x=e.r,this.y=e.g,this.z=e.b,this}equals(e){return e.x===this.x&&e.y===this.y&&e.z===this.z}fromArray(e,t=0){return this.x=e[t],this.y=e[t+1],this.z=e[t+2],this}toArray(e=[],t=0){return e[t]=this.x,e[t+1]=this.y,e[t+2]=this.z,e}fromBufferAttribute(e,t){return this.x=e.getX(t),this.y=e.getY(t),this.z=e.getZ(t),this}random(){return this.x=ht(),this.y=ht(),this.z=ht(),this}randomDirection(){let e=ht()*Math.PI*2,t=ht()*2-1,n=Math.sqrt(1-t*t);return this.x=n*Math.cos(e),this.y=t,this.z=n*Math.sin(e),this}*[Symbol.iterator](){yield this.x,yield this.y,yield this.z}},ml=new U,Bc=new Gt,st=class i{static{i.prototype.isMatrix3=!0}constructor(e,t,n,s,r,a,o,l,c){this.elements=[1,0,0,0,1,0,0,0,1],e!==void 0&&this.set(e,t,n,s,r,a,o,l,c)}set(e,t,n,s,r,a,o,l,c){let h=this.elements;return h[0]=e,h[1]=s,h[2]=o,h[3]=t,h[4]=r,h[5]=l,h[6]=n,h[7]=a,h[8]=c,this}identity(){return this.set(1,0,0,0,1,0,0,0,1),this}copy(e){let t=this.elements,n=e.elements;return t[0]=n[0],t[1]=n[1],t[2]=n[2],t[3]=n[3],t[4]=n[4],t[5]=n[5],t[6]=n[6],t[7]=n[7],t[8]=n[8],this}extractBasis(e,t,n){return e.setFromMatrix3Column(this,0),t.setFromMatrix3Column(this,1),n.setFromMatrix3Column(this,2),this}setFromMatrix4(e){let t=e.elements;return this.set(t[0],t[4],t[8],t[1],t[5],t[9],t[2],t[6],t[10]),this}multiply(e){return this.multiplyMatrices(this,e)}premultiply(e){return this.multiplyMatrices(e,this)}multiplyMatrices(e,t){let n=e.elements,s=t.elements,r=this.elements,a=n[0],o=n[3],l=n[6],c=n[1],h=n[4],f=n[7],u=n[2],d=n[5],g=n[8],b=s[0],m=s[3],p=s[6],E=s[1],C=s[4],y=s[7],w=s[2],T=s[5],I=s[8];return r[0]=a*b+o*E+l*w,r[3]=a*m+o*C+l*T,r[6]=a*p+o*y+l*I,r[1]=c*b+h*E+f*w,r[4]=c*m+h*C+f*T,r[7]=c*p+h*y+f*I,r[2]=u*b+d*E+g*w,r[5]=u*m+d*C+g*T,r[8]=u*p+d*y+g*I,this}multiplyScalar(e){let t=this.elements;return t[0]*=e,t[3]*=e,t[6]*=e,t[1]*=e,t[4]*=e,t[7]*=e,t[2]*=e,t[5]*=e,t[8]*=e,this}determinant(){let e=this.elements,t=e[0],n=e[1],s=e[2],r=e[3],a=e[4],o=e[5],l=e[6],c=e[7],h=e[8];return t*a*h-t*o*c-n*r*h+n*o*l+s*r*c-s*a*l}invert(){let e=this.elements,t=e[0],n=e[1],s=e[2],r=e[3],a=e[4],o=e[5],l=e[6],c=e[7],h=e[8],f=h*a-o*c,u=o*l-h*r,d=c*r-a*l,g=t*f+n*u+s*d;if(g===0)return this.set(0,0,0,0,0,0,0,0,0);let b=1/g;return e[0]=f*b,e[1]=(s*c-h*n)*b,e[2]=(o*n-s*a)*b,e[3]=u*b,e[4]=(h*t-s*l)*b,e[5]=(s*r-o*t)*b,e[6]=d*b,e[7]=(n*l-c*t)*b,e[8]=(a*t-n*r)*b,this}transpose(){let e,t=this.elements;return e=t[1],t[1]=t[3],t[3]=e,e=t[2],t[2]=t[6],t[6]=e,e=t[5],t[5]=t[7],t[7]=e,this}getNormalMatrix(e){return this.setFromMatrix4(e).invert().transpose()}transposeIntoArray(e){let t=this.elements;return e[0]=t[0],e[1]=t[3],e[2]=t[6],e[3]=t[1],e[4]=t[4],e[5]=t[7],e[6]=t[2],e[7]=t[5],e[8]=t[8],this}setUvTransform(e,t,n,s,r,a,o){let l=Math.cos(r),c=Math.sin(r);return this.set(n*l,n*c,-n*(l*a+c*o)+a+e,-s*c,s*l,-s*(-c*a+l*o)+o+t,0,0,1),this}scale(e,t){return ki("Matrix3: .scale() is deprecated. Use .makeScale() instead."),this.premultiply(gl.makeScale(e,t)),this}rotate(e){return ki("Matrix3: .rotate() is deprecated. Use .makeRotation() instead."),this.premultiply(gl.makeRotation(-e)),this}translate(e,t){return ki("Matrix3: .translate() is deprecated. Use .makeTranslation() instead."),this.premultiply(gl.makeTranslation(e,t)),this}makeTranslation(e,t){return e.isVector2?this.set(1,0,e.x,0,1,e.y,0,0,1):this.set(1,0,e,0,1,t,0,0,1),this}makeRotation(e){let t=Math.cos(e),n=Math.sin(e);return this.set(t,-n,0,n,t,0,0,0,1),this}makeScale(e,t){return this.set(e,0,0,0,t,0,0,0,1),this}equals(e){let t=this.elements,n=e.elements;for(let s=0;s<9;s++)if(t[s]!==n[s])return!1;return!0}fromArray(e,t=0){for(let n=0;n<9;n++)this.elements[n]=e[n+t];return this}toArray(e=[],t=0){let n=this.elements;return e[t]=n[0],e[t+1]=n[1],e[t+2]=n[2],e[t+3]=n[3],e[t+4]=n[4],e[t+5]=n[5],e[t+6]=n[6],e[t+7]=n[7],e[t+8]=n[8],e}clone(){return new this.constructor().fromArray(this.elements)}},gl=new st,zc=new st().set(.4123908,.3575843,.1804808,.212639,.7151687,.0721923,.0193308,.1191948,.9505322),Vc=new st().set(3.2409699,-1.5373832,-.4986108,-.9692436,1.8759675,.0415551,.0556301,-.203977,1.0569715);function dd(){let i={enabled:!0,workingColorSpace:ir,spaces:{},convert:function(s,r,a){return this.enabled===!1||r===a||!r||!a||(this.spaces[r].transfer===St&&(s.r=ri(s.r),s.g=ri(s.g),s.b=ri(s.b)),this.spaces[r].primaries!==this.spaces[a].primaries&&(s.applyMatrix3(this.spaces[r].toXYZ),s.applyMatrix3(this.spaces[a].fromXYZ)),this.spaces[a].transfer===St&&(s.r=fs(s.r),s.g=fs(s.g),s.b=fs(s.b))),s},workingToColorSpace:function(s,r){return this.convert(s,this.workingColorSpace,r)},colorSpaceToWorking:function(s,r){return this.convert(s,r,this.workingColorSpace)},getPrimaries:function(s){return this.spaces[s].primaries},getTransfer:function(s){return s===li?sr:this.spaces[s].transfer},getToneMappingMode:function(s){return this.spaces[s].outputColorSpaceConfig.toneMappingMode||"standard"},getLuminanceCoefficients:function(s,r=this.workingColorSpace){return s.fromArray(this.spaces[r].luminanceCoefficients)},define:function(s){Object.assign(this.spaces,s)},_getMatrix:function(s,r,a){return s.copy(this.spaces[r].toXYZ).multiply(this.spaces[a].fromXYZ)},_getDrawingBufferColorSpace:function(s){return this.spaces[s].outputColorSpaceConfig.drawingBufferColorSpace},_getUnpackColorSpace:function(s=this.workingColorSpace){return this.spaces[s].workingColorSpaceConfig.unpackColorSpace},fromWorkingColorSpace:function(s,r){return ki("ColorManagement: .fromWorkingColorSpace() has been renamed to .workingToColorSpace()."),i.workingToColorSpace(s,r)},toWorkingColorSpace:function(s,r){return ki("ColorManagement: .toWorkingColorSpace() has been renamed to .colorSpaceToWorking()."),i.colorSpaceToWorking(s,r)}},e=[.64,.33,.3,.6,.15,.06],t=[.2126,.7152,.0722],n=[.3127,.329];return i.define({[ir]:{primaries:e,whitePoint:n,transfer:sr,toXYZ:zc,fromXYZ:Vc,luminanceCoefficients:t,workingColorSpaceConfig:{unpackColorSpace:cn},outputColorSpaceConfig:{drawingBufferColorSpace:cn}},[cn]:{primaries:e,whitePoint:n,transfer:St,toXYZ:zc,fromXYZ:Vc,luminanceCoefficients:t,outputColorSpaceConfig:{drawingBufferColorSpace:cn}}}),i}var pt=dd();function ri(i){return i<.04045?i*.0773993808:Math.pow(i*.9478672986+.0521327014,2.4)}function fs(i){return i<.0031308?i*12.92:1.055*Math.pow(i,.41666)-.055}var Ki,ka=class{static getDataURL(e,t="image/png"){if(/^data:/i.test(e.src)||typeof HTMLCanvasElement>"u")return e.src;let n;if(e instanceof HTMLCanvasElement)n=e;else{Ki===void 0&&(Ki=rr("canvas")),Ki.width=e.width,Ki.height=e.height;let s=Ki.getContext("2d");e instanceof ImageData?s.putImageData(e,0,0):s.drawImage(e,0,0,e.width,e.height),n=Ki}return n.toDataURL(t)}static sRGBToLinear(e){if(typeof HTMLImageElement<"u"&&e instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&e instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&e instanceof ImageBitmap){let t=rr("canvas");t.width=e.width,t.height=e.height;let n=t.getContext("2d");n.drawImage(e,0,0,e.width,e.height);let s=n.getImageData(0,0,e.width,e.height),r=s.data;for(let a=0;a<r.length;a++)r[a]=ri(r[a]/255)*255;return n.putImageData(s,0,0),t}else if(e.data){let t=e.data.slice(0);for(let n=0;n<t.length;n++)t instanceof Uint8Array||t instanceof Uint8ClampedArray?t[n]=Math.floor(ri(t[n]/255)*255):t[n]=ri(t[n]);return{data:t,width:e.width,height:e.height}}else return je("ImageUtils.sRGBToLinear(): Unsupported image type. No color space conversion applied."),e}},fd=0,xs=class{constructor(e=null){this.isTextureSource=!0,Object.defineProperty(this,"id",{value:fd++}),this.uuid=Ls(),this.data=e,this.dataReady=!0,this.version=0}getSize(e){let t=this.data;return typeof HTMLVideoElement<"u"&&t instanceof HTMLVideoElement?e.set(t.videoWidth,t.videoHeight,0):typeof VideoFrame<"u"&&t instanceof VideoFrame?e.set(t.displayWidth,t.displayHeight,0):t!==null?e.set(t.width,t.height,t.depth||0):e.set(0,0,0),e}set needsUpdate(e){e===!0&&this.version++}toJSON(e){let t=e===void 0||typeof e=="string";if(!t&&e.images[this.uuid]!==void 0)return e.images[this.uuid];let n={uuid:this.uuid,url:""},s=this.data;if(s!==null){let r;if(Array.isArray(s)){r=[];for(let a=0,o=s.length;a<o;a++)s[a].isDataTexture?r.push(_l(s[a].image)):r.push(_l(s[a]))}else r=_l(s);n.url=r}return t||(e.images[this.uuid]=n),n}};function _l(i){return typeof HTMLImageElement<"u"&&i instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&i instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&i instanceof ImageBitmap?ka.getDataURL(i):i.data?{data:Array.from(i.data),width:i.width,height:i.height,type:i.data.constructor.name}:(je("Texture: Unable to serialize Texture."),{})}var pd=0,xl=new U,mn=class i extends $n{constructor(e=i.DEFAULT_IMAGE,t=i.DEFAULT_MAPPING,n=qn,s=qn,r=Qt,a=wi,o=In,l=xn,c=i.DEFAULT_ANISOTROPY,h=li){super(),this.isTexture=!0,Object.defineProperty(this,"id",{value:pd++}),this.uuid=Ls(),this.name="",this.source=new xs(e),this.mipmaps=[],this.mapping=t,this.channel=0,this.wrapS=n,this.wrapT=s,this.magFilter=r,this.minFilter=a,this.anisotropy=c,this.format=o,this.internalFormat=null,this.type=l,this.offset=new De(0,0),this.repeat=new De(1,1),this.center=new De(0,0),this.rotation=0,this.matrixAutoUpdate=!0,this.matrix=new st,this.generateMipmaps=!0,this.premultiplyAlpha=!1,this.flipY=!0,this.unpackAlignment=4,this.colorSpace=h,this.userData={},this.updateRanges=[],this.version=0,this.onUpdate=null,this.renderTarget=null,this.isRenderTargetTexture=!1,this.isArrayTexture=!!(e&&e.depth&&e.depth>1),this.pmremVersion=0,this.normalized=!1}get width(){return this.source.getSize(xl).x}get height(){return this.source.getSize(xl).y}get depth(){return this.source.getSize(xl).z}get image(){return this.source.data}set image(e){this.source.data=e}updateMatrix(){this.matrix.setUvTransform(this.offset.x,this.offset.y,this.repeat.x,this.repeat.y,this.rotation,this.center.x,this.center.y)}addUpdateRange(e,t){this.updateRanges.push({start:e,count:t})}clearUpdateRanges(){this.updateRanges.length=0}clone(){return new this.constructor().copy(this)}copy(e){return this.name=e.name,this.source=e.source,this.mipmaps=e.mipmaps.slice(0),this.mapping=e.mapping,this.channel=e.channel,this.wrapS=e.wrapS,this.wrapT=e.wrapT,this.magFilter=e.magFilter,this.minFilter=e.minFilter,this.anisotropy=e.anisotropy,this.format=e.format,this.internalFormat=e.internalFormat,this.type=e.type,this.normalized=e.normalized,this.offset.copy(e.offset),this.repeat.copy(e.repeat),this.center.copy(e.center),this.rotation=e.rotation,this.matrixAutoUpdate=e.matrixAutoUpdate,this.matrix.copy(e.matrix),this.generateMipmaps=e.generateMipmaps,this.premultiplyAlpha=e.premultiplyAlpha,this.flipY=e.flipY,this.unpackAlignment=e.unpackAlignment,this.colorSpace=e.colorSpace,this.renderTarget=e.renderTarget,this.isRenderTargetTexture=e.isRenderTargetTexture,this.isArrayTexture=e.isArrayTexture,this.userData=JSON.parse(JSON.stringify(e.userData)),this.needsUpdate=!0,this}setValues(e){for(let t in e){let n=e[t];if(n===void 0){je(`Texture.setValues(): parameter '${t}' has value of undefined.`);continue}let s=this[t];if(s===void 0){je(`Texture.setValues(): property '${t}' does not exist.`);continue}s&&n&&s.isVector2&&n.isVector2||s&&n&&s.isVector3&&n.isVector3||s&&n&&s.isMatrix3&&n.isMatrix3?s.copy(n):this[t]=n}}toJSON(e){let t=e===void 0||typeof e=="string";if(!t&&e.textures[this.uuid]!==void 0)return e.textures[this.uuid];let n={metadata:{version:4.7,type:"Texture",generator:"Texture.toJSON"},uuid:this.uuid,name:this.name,image:this.source.toJSON(e).uuid,mapping:this.mapping,channel:this.channel,repeat:[this.repeat.x,this.repeat.y],offset:[this.offset.x,this.offset.y],center:[this.center.x,this.center.y],rotation:this.rotation,wrap:[this.wrapS,this.wrapT],format:this.format,internalFormat:this.internalFormat,type:this.type,normalized:this.normalized,colorSpace:this.colorSpace,minFilter:this.minFilter,magFilter:this.magFilter,anisotropy:this.anisotropy,flipY:this.flipY,generateMipmaps:this.generateMipmaps,premultiplyAlpha:this.premultiplyAlpha,unpackAlignment:this.unpackAlignment};return Object.keys(this.userData).length>0&&(n.userData=this.userData),t||(e.textures[this.uuid]=n),n}dispose(){this.dispatchEvent({type:"dispose"})}transformUv(e){if(this.mapping!==tc)return e;if(e.applyMatrix3(this.matrix),e.x<0||e.x>1)switch(this.wrapS){case Da:e.x=e.x-Math.floor(e.x);break;case qn:e.x=e.x<0?0:1;break;case Ua:Math.abs(Math.floor(e.x)%2)===1?e.x=Math.ceil(e.x)-e.x:e.x=e.x-Math.floor(e.x);break}if(e.y<0||e.y>1)switch(this.wrapT){case Da:e.y=e.y-Math.floor(e.y);break;case qn:e.y=e.y<0?0:1;break;case Ua:Math.abs(Math.floor(e.y)%2)===1?e.y=Math.ceil(e.y)-e.y:e.y=e.y-Math.floor(e.y);break}return this.flipY&&(e.y=1-e.y),e}set needsUpdate(e){e===!0&&(this.version++,this.source.needsUpdate=!0)}set needsPMREMUpdate(e){e===!0&&this.pmremVersion++}};mn.DEFAULT_IMAGE=null;mn.DEFAULT_MAPPING=tc;mn.DEFAULT_ANISOTROPY=1;var Ut=class i{static{i.prototype.isVector4=!0}constructor(e=0,t=0,n=0,s=1){this.x=e,this.y=t,this.z=n,this.w=s}get width(){return this.z}set width(e){this.z=e}get height(){return this.w}set height(e){this.w=e}set(e,t,n,s){return this.x=e,this.y=t,this.z=n,this.w=s,this}setScalar(e){return this.x=e,this.y=e,this.z=e,this.w=e,this}setX(e){return this.x=e,this}setY(e){return this.y=e,this}setZ(e){return this.z=e,this}setW(e){return this.w=e,this}setComponent(e,t){switch(e){case 0:this.x=t;break;case 1:this.y=t;break;case 2:this.z=t;break;case 3:this.w=t;break;default:throw new Error("THREE.Vector4: index is out of range: "+e)}return this}getComponent(e){switch(e){case 0:return this.x;case 1:return this.y;case 2:return this.z;case 3:return this.w;default:throw new Error("THREE.Vector4: index is out of range: "+e)}}clone(){return new this.constructor(this.x,this.y,this.z,this.w)}copy(e){return this.x=e.x,this.y=e.y,this.z=e.z,this.w=e.w!==void 0?e.w:1,this}add(e){return this.x+=e.x,this.y+=e.y,this.z+=e.z,this.w+=e.w,this}addScalar(e){return this.x+=e,this.y+=e,this.z+=e,this.w+=e,this}addVectors(e,t){return this.x=e.x+t.x,this.y=e.y+t.y,this.z=e.z+t.z,this.w=e.w+t.w,this}addScaledVector(e,t){return this.x+=e.x*t,this.y+=e.y*t,this.z+=e.z*t,this.w+=e.w*t,this}sub(e){return this.x-=e.x,this.y-=e.y,this.z-=e.z,this.w-=e.w,this}subScalar(e){return this.x-=e,this.y-=e,this.z-=e,this.w-=e,this}subVectors(e,t){return this.x=e.x-t.x,this.y=e.y-t.y,this.z=e.z-t.z,this.w=e.w-t.w,this}multiply(e){return this.x*=e.x,this.y*=e.y,this.z*=e.z,this.w*=e.w,this}multiplyScalar(e){return this.x*=e,this.y*=e,this.z*=e,this.w*=e,this}applyMatrix4(e){let t=this.x,n=this.y,s=this.z,r=this.w,a=e.elements;return this.x=a[0]*t+a[4]*n+a[8]*s+a[12]*r,this.y=a[1]*t+a[5]*n+a[9]*s+a[13]*r,this.z=a[2]*t+a[6]*n+a[10]*s+a[14]*r,this.w=a[3]*t+a[7]*n+a[11]*s+a[15]*r,this}divide(e){return this.x/=e.x,this.y/=e.y,this.z/=e.z,this.w/=e.w,this}divideScalar(e){return this.multiplyScalar(1/e)}setAxisAngleFromQuaternion(e){this.w=2*Math.acos(e.w);let t=Math.sqrt(1-e.w*e.w);return t<1e-4?(this.x=1,this.y=0,this.z=0):(this.x=e.x/t,this.y=e.y/t,this.z=e.z/t),this}setAxisAngleFromRotationMatrix(e){let t,n,s,r,l=e.elements,c=l[0],h=l[4],f=l[8],u=l[1],d=l[5],g=l[9],b=l[2],m=l[6],p=l[10];if(Math.abs(h-u)<.01&&Math.abs(f-b)<.01&&Math.abs(g-m)<.01){if(Math.abs(h+u)<.1&&Math.abs(f+b)<.1&&Math.abs(g+m)<.1&&Math.abs(c+d+p-3)<.1)return this.set(1,0,0,0),this;t=Math.PI;let C=(c+1)/2,y=(d+1)/2,w=(p+1)/2,T=(h+u)/4,I=(f+b)/4,x=(g+m)/4;return C>y&&C>w?C<.01?(n=0,s=.707106781,r=.707106781):(n=Math.sqrt(C),s=T/n,r=I/n):y>w?y<.01?(n=.707106781,s=0,r=.707106781):(s=Math.sqrt(y),n=T/s,r=x/s):w<.01?(n=.707106781,s=.707106781,r=0):(r=Math.sqrt(w),n=I/r,s=x/r),this.set(n,s,r,t),this}let E=Math.sqrt((m-g)*(m-g)+(f-b)*(f-b)+(u-h)*(u-h));return Math.abs(E)<.001&&(E=1),this.x=(m-g)/E,this.y=(f-b)/E,this.z=(u-h)/E,this.w=Math.acos((c+d+p-1)/2),this}setFromMatrixPosition(e){let t=e.elements;return this.x=t[12],this.y=t[13],this.z=t[14],this.w=t[15],this}min(e){return this.x=Math.min(this.x,e.x),this.y=Math.min(this.y,e.y),this.z=Math.min(this.z,e.z),this.w=Math.min(this.w,e.w),this}max(e){return this.x=Math.max(this.x,e.x),this.y=Math.max(this.y,e.y),this.z=Math.max(this.z,e.z),this.w=Math.max(this.w,e.w),this}clamp(e,t){return this.x=mt(this.x,e.x,t.x),this.y=mt(this.y,e.y,t.y),this.z=mt(this.z,e.z,t.z),this.w=mt(this.w,e.w,t.w),this}clampScalar(e,t){return this.x=mt(this.x,e,t),this.y=mt(this.y,e,t),this.z=mt(this.z,e,t),this.w=mt(this.w,e,t),this}clampLength(e,t){let n=this.length();return this.divideScalar(n||1).multiplyScalar(mt(n,e,t))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this.z=Math.floor(this.z),this.w=Math.floor(this.w),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this.z=Math.ceil(this.z),this.w=Math.ceil(this.w),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this.z=Math.round(this.z),this.w=Math.round(this.w),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this.z=Math.trunc(this.z),this.w=Math.trunc(this.w),this}negate(){return this.x=-this.x,this.y=-this.y,this.z=-this.z,this.w=-this.w,this}dot(e){return this.x*e.x+this.y*e.y+this.z*e.z+this.w*e.w}lengthSq(){return this.x*this.x+this.y*this.y+this.z*this.z+this.w*this.w}length(){return Math.sqrt(this.x*this.x+this.y*this.y+this.z*this.z+this.w*this.w)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)+Math.abs(this.z)+Math.abs(this.w)}normalize(){return this.divideScalar(this.length()||1)}setLength(e){return this.normalize().multiplyScalar(e)}lerp(e,t){return this.x+=(e.x-this.x)*t,this.y+=(e.y-this.y)*t,this.z+=(e.z-this.z)*t,this.w+=(e.w-this.w)*t,this}lerpVectors(e,t,n){return this.x=e.x+(t.x-e.x)*n,this.y=e.y+(t.y-e.y)*n,this.z=e.z+(t.z-e.z)*n,this.w=e.w+(t.w-e.w)*n,this}equals(e){return e.x===this.x&&e.y===this.y&&e.z===this.z&&e.w===this.w}fromArray(e,t=0){return this.x=e[t],this.y=e[t+1],this.z=e[t+2],this.w=e[t+3],this}toArray(e=[],t=0){return e[t]=this.x,e[t+1]=this.y,e[t+2]=this.z,e[t+3]=this.w,e}fromBufferAttribute(e,t){return this.x=e.getX(t),this.y=e.getY(t),this.z=e.getZ(t),this.w=e.getW(t),this}random(){return this.x=ht(),this.y=ht(),this.z=ht(),this.w=ht(),this}*[Symbol.iterator](){yield this.x,yield this.y,yield this.z,yield this.w}},Oa=class extends $n{constructor(e=1,t=1,n={}){super(),n=Object.assign({generateMipmaps:!1,internalFormat:null,minFilter:Qt,depthBuffer:!0,stencilBuffer:!1,resolveColorBuffer:!0,resolveDepthBuffer:!0,resolveStencilBuffer:!0,storeMultisampledColorBuffer:!0,storeMultisampledDepthBuffer:!0,storeMultisampledStencilBuffer:!0,depthTexture:null,samples:0,count:1,depth:1,multiview:!1,useArrayDepthTexture:!1},n),this.isRenderTarget=!0,this.width=e,this.height=t,this.depth=n.depth,this.scissor=new Ut(0,0,e,t),this.scissorTest=!1,this.viewport=new Ut(0,0,e,t),this.textures=[];let s={width:e,height:t,depth:n.depth},r=new mn(s),a=n.count;for(let o=0;o<a;o++)this.textures[o]=r.clone(),this.textures[o].isRenderTargetTexture=!0,this.textures[o].renderTarget=this;this._setTextureOptions(n),this.depthBuffer=n.depthBuffer,this.stencilBuffer=n.stencilBuffer,this.resolveColorBuffer=n.resolveColorBuffer,this.resolveDepthBuffer=n.resolveDepthBuffer,this.resolveStencilBuffer=n.resolveStencilBuffer,this.storeMultisampledColorBuffer=n.storeMultisampledColorBuffer,this.storeMultisampledDepthBuffer=n.storeMultisampledDepthBuffer,this.storeMultisampledStencilBuffer=n.storeMultisampledStencilBuffer,this._depthTexture=null,this.depthTexture=n.depthTexture,this.samples=n.samples,this.multiview=n.multiview,this.useArrayDepthTexture=n.useArrayDepthTexture}_setTextureOptions(e={}){let t={minFilter:Qt,generateMipmaps:!1,flipY:!1,internalFormat:null};e.mapping!==void 0&&(t.mapping=e.mapping),e.wrapS!==void 0&&(t.wrapS=e.wrapS),e.wrapT!==void 0&&(t.wrapT=e.wrapT),e.wrapR!==void 0&&(t.wrapR=e.wrapR),e.magFilter!==void 0&&(t.magFilter=e.magFilter),e.minFilter!==void 0&&(t.minFilter=e.minFilter),e.format!==void 0&&(t.format=e.format),e.type!==void 0&&(t.type=e.type),e.anisotropy!==void 0&&(t.anisotropy=e.anisotropy),e.colorSpace!==void 0&&(t.colorSpace=e.colorSpace),e.flipY!==void 0&&(t.flipY=e.flipY),e.generateMipmaps!==void 0&&(t.generateMipmaps=e.generateMipmaps),e.internalFormat!==void 0&&(t.internalFormat=e.internalFormat);for(let n=0;n<this.textures.length;n++)this.textures[n].setValues(t)}get texture(){return this.textures[0]}set texture(e){this.textures[0]=e}set depthTexture(e){this._depthTexture!==null&&this._depthTexture.renderTarget===this&&(this._depthTexture.renderTarget=null),e!==null&&e.renderTarget===null&&(e.renderTarget=this),this._depthTexture=e}get depthTexture(){return this._depthTexture}setSize(e,t,n=1){if(this.width!==e||this.height!==t||this.depth!==n){this.width=e,this.height=t,this.depth=n;for(let s=0,r=this.textures.length;s<r;s++)this.textures[s].image.width=e,this.textures[s].image.height=t,this.textures[s].image.depth=n,this.textures[s].isData3DTexture!==!0&&(this.textures[s].isArrayTexture=this.textures[s].image.depth>1);this.dispose()}this.viewport.set(0,0,e,t),this.scissor.set(0,0,e,t)}clone(){return new this.constructor().copy(this)}copy(e){this.width=e.width,this.height=e.height,this.depth=e.depth,this.scissor.copy(e.scissor),this.scissorTest=e.scissorTest,this.viewport.copy(e.viewport),this.textures.length=0;for(let t=0,n=e.textures.length;t<n;t++){this.textures[t]=e.textures[t].clone(),this.textures[t].isRenderTargetTexture=!0,this.textures[t].renderTarget=this;let s=Object.assign({},e.textures[t].image);this.textures[t].source=new xs(s)}if(this.depthBuffer=e.depthBuffer,this.stencilBuffer=e.stencilBuffer,this.resolveColorBuffer=e.resolveColorBuffer,this.resolveDepthBuffer=e.resolveDepthBuffer,this.resolveStencilBuffer=e.resolveStencilBuffer,this.storeMultisampledColorBuffer=e.storeMultisampledColorBuffer,this.storeMultisampledDepthBuffer=e.storeMultisampledDepthBuffer,this.storeMultisampledStencilBuffer=e.storeMultisampledStencilBuffer,e.depthTexture!==null)if(e.depthTexture.renderTarget===e){let t=e.depthTexture.clone();t.renderTarget=null,this.depthTexture=t}else this.depthTexture=e.depthTexture;return this.samples=e.samples,this.multiview=e.multiview,this.useArrayDepthTexture=e.useArrayDepthTexture,this}dispose(){this.dispatchEvent({type:"dispose"})}},Vt=class extends Oa{constructor(e=1,t=1,n={}){super(e,t,n),this.isWebGLRenderTarget=!0}},ar=class extends mn{constructor(e=null,t=1,n=1,s=1){super(null),this.isDataArrayTexture=!0,this.image={data:e,width:t,height:n,depth:s},this.magFilter=Yt,this.minFilter=Yt,this.wrapR=qn,this.generateMipmaps=!1,this.flipY=!1,this.unpackAlignment=1,this.layerUpdates=new Set}copy(e){return super.copy(e),this.wrapR=e.wrapR,this}addLayerUpdate(e){this.layerUpdates.add(e)}clearLayerUpdates(){this.layerUpdates.clear()}};var Ba=class extends mn{constructor(e=null,t=1,n=1,s=1){super(null),this.isData3DTexture=!0,this.image={data:e,width:t,height:n,depth:s},this.magFilter=Yt,this.minFilter=Yt,this.wrapR=qn,this.generateMipmaps=!1,this.flipY=!1,this.unpackAlignment=1}copy(e){return super.copy(e),this.wrapR=e.wrapR,this}};var xt=class i{static{i.prototype.isMatrix4=!0}constructor(e,t,n,s,r,a,o,l,c,h,f,u,d,g,b,m){this.elements=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1],e!==void 0&&this.set(e,t,n,s,r,a,o,l,c,h,f,u,d,g,b,m)}set(e,t,n,s,r,a,o,l,c,h,f,u,d,g,b,m){let p=this.elements;return p[0]=e,p[4]=t,p[8]=n,p[12]=s,p[1]=r,p[5]=a,p[9]=o,p[13]=l,p[2]=c,p[6]=h,p[10]=f,p[14]=u,p[3]=d,p[7]=g,p[11]=b,p[15]=m,this}identity(){return this.set(1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1),this}clone(){return new i().fromArray(this.elements)}copy(e){let t=this.elements,n=e.elements;return t[0]=n[0],t[1]=n[1],t[2]=n[2],t[3]=n[3],t[4]=n[4],t[5]=n[5],t[6]=n[6],t[7]=n[7],t[8]=n[8],t[9]=n[9],t[10]=n[10],t[11]=n[11],t[12]=n[12],t[13]=n[13],t[14]=n[14],t[15]=n[15],this}copyPosition(e){let t=this.elements,n=e.elements;return t[12]=n[12],t[13]=n[13],t[14]=n[14],this}setFromMatrix3(e){let t=e.elements;return this.set(t[0],t[3],t[6],0,t[1],t[4],t[7],0,t[2],t[5],t[8],0,0,0,0,1),this}extractBasis(e,t,n){return this.determinantAffine()===0?(e.set(1,0,0),t.set(0,1,0),n.set(0,0,1),this):(e.setFromMatrixColumn(this,0),t.setFromMatrixColumn(this,1),n.setFromMatrixColumn(this,2),this)}makeBasis(e,t,n){return this.set(e.x,t.x,n.x,0,e.y,t.y,n.y,0,e.z,t.z,n.z,0,0,0,0,1),this}extractRotation(e){if(e.determinantAffine()===0)return this.identity();let t=this.elements,n=e.elements,s=1/Qi.setFromMatrixColumn(e,0).length(),r=1/Qi.setFromMatrixColumn(e,1).length(),a=1/Qi.setFromMatrixColumn(e,2).length();return t[0]=n[0]*s,t[1]=n[1]*s,t[2]=n[2]*s,t[3]=0,t[4]=n[4]*r,t[5]=n[5]*r,t[6]=n[6]*r,t[7]=0,t[8]=n[8]*a,t[9]=n[9]*a,t[10]=n[10]*a,t[11]=0,t[12]=0,t[13]=0,t[14]=0,t[15]=1,this}makeRotationFromEuler(e){let t=this.elements,n=e.x,s=e.y,r=e.z,a=Math.cos(n),o=Math.sin(n),l=Math.cos(s),c=Math.sin(s),h=Math.cos(r),f=Math.sin(r);if(e.order==="XYZ"){let u=a*h,d=a*f,g=o*h,b=o*f;t[0]=l*h,t[4]=-l*f,t[8]=c,t[1]=d+g*c,t[5]=u-b*c,t[9]=-o*l,t[2]=b-u*c,t[6]=g+d*c,t[10]=a*l}else if(e.order==="YXZ"){let u=l*h,d=l*f,g=c*h,b=c*f;t[0]=u+b*o,t[4]=g*o-d,t[8]=a*c,t[1]=a*f,t[5]=a*h,t[9]=-o,t[2]=d*o-g,t[6]=b+u*o,t[10]=a*l}else if(e.order==="ZXY"){let u=l*h,d=l*f,g=c*h,b=c*f;t[0]=u-b*o,t[4]=-a*f,t[8]=g+d*o,t[1]=d+g*o,t[5]=a*h,t[9]=b-u*o,t[2]=-a*c,t[6]=o,t[10]=a*l}else if(e.order==="ZYX"){let u=a*h,d=a*f,g=o*h,b=o*f;t[0]=l*h,t[4]=g*c-d,t[8]=u*c+b,t[1]=l*f,t[5]=b*c+u,t[9]=d*c-g,t[2]=-c,t[6]=o*l,t[10]=a*l}else if(e.order==="YZX"){let u=a*l,d=a*c,g=o*l,b=o*c;t[0]=l*h,t[4]=b-u*f,t[8]=g*f+d,t[1]=f,t[5]=a*h,t[9]=-o*h,t[2]=-c*h,t[6]=d*f+g,t[10]=u-b*f}else if(e.order==="XZY"){let u=a*l,d=a*c,g=o*l,b=o*c;t[0]=l*h,t[4]=-f,t[8]=c*h,t[1]=u*f+b,t[5]=a*h,t[9]=d*f-g,t[2]=g*f-d,t[6]=o*h,t[10]=b*f+u}return t[3]=0,t[7]=0,t[11]=0,t[12]=0,t[13]=0,t[14]=0,t[15]=1,this}makeRotationFromQuaternion(e){return this.compose(md,e,gd)}lookAt(e,t,n){let s=this.elements;return yn.subVectors(e,t),yn.lengthSq()===0&&(yn.z=1),yn.normalize(),fi.crossVectors(n,yn),fi.lengthSq()===0&&(Math.abs(n.z)===1?yn.x+=1e-4:yn.z+=1e-4,yn.normalize(),fi.crossVectors(n,yn)),fi.normalize(),ta.crossVectors(yn,fi),s[0]=fi.x,s[4]=ta.x,s[8]=yn.x,s[1]=fi.y,s[5]=ta.y,s[9]=yn.y,s[2]=fi.z,s[6]=ta.z,s[10]=yn.z,this}multiply(e){return this.multiplyMatrices(this,e)}premultiply(e){return this.multiplyMatrices(e,this)}multiplyMatrices(e,t){let n=e.elements,s=t.elements,r=this.elements,a=n[0],o=n[4],l=n[8],c=n[12],h=n[1],f=n[5],u=n[9],d=n[13],g=n[2],b=n[6],m=n[10],p=n[14],E=n[3],C=n[7],y=n[11],w=n[15],T=s[0],I=s[4],x=s[8],A=s[12],D=s[1],k=s[5],G=s[9],Y=s[13],F=s[2],$=s[6],te=s[10],re=s[14],Z=s[3],Q=s[7],ce=s[11],se=s[15];return r[0]=a*T+o*D+l*F+c*Z,r[4]=a*I+o*k+l*$+c*Q,r[8]=a*x+o*G+l*te+c*ce,r[12]=a*A+o*Y+l*re+c*se,r[1]=h*T+f*D+u*F+d*Z,r[5]=h*I+f*k+u*$+d*Q,r[9]=h*x+f*G+u*te+d*ce,r[13]=h*A+f*Y+u*re+d*se,r[2]=g*T+b*D+m*F+p*Z,r[6]=g*I+b*k+m*$+p*Q,r[10]=g*x+b*G+m*te+p*ce,r[14]=g*A+b*Y+m*re+p*se,r[3]=E*T+C*D+y*F+w*Z,r[7]=E*I+C*k+y*$+w*Q,r[11]=E*x+C*G+y*te+w*ce,r[15]=E*A+C*Y+y*re+w*se,this}multiplyScalar(e){let t=this.elements;return t[0]*=e,t[4]*=e,t[8]*=e,t[12]*=e,t[1]*=e,t[5]*=e,t[9]*=e,t[13]*=e,t[2]*=e,t[6]*=e,t[10]*=e,t[14]*=e,t[3]*=e,t[7]*=e,t[11]*=e,t[15]*=e,this}determinant(){let e=this.elements,t=e[0],n=e[4],s=e[8],r=e[12],a=e[1],o=e[5],l=e[9],c=e[13],h=e[2],f=e[6],u=e[10],d=e[14],g=e[3],b=e[7],m=e[11],p=e[15],E=l*d-c*u,C=o*d-c*f,y=o*u-l*f,w=a*d-c*h,T=a*u-l*h,I=a*f-o*h;return t*(b*E-m*C+p*y)-n*(g*E-m*w+p*T)+s*(g*C-b*w+p*I)-r*(g*y-b*T+m*I)}determinantAffine(){let e=this.elements,t=e[0],n=e[4],s=e[8],r=e[1],a=e[5],o=e[9],l=e[2],c=e[6],h=e[10];return t*(a*h-o*c)-n*(r*h-o*l)+s*(r*c-a*l)}transpose(){let e=this.elements,t;return t=e[1],e[1]=e[4],e[4]=t,t=e[2],e[2]=e[8],e[8]=t,t=e[6],e[6]=e[9],e[9]=t,t=e[3],e[3]=e[12],e[12]=t,t=e[7],e[7]=e[13],e[13]=t,t=e[11],e[11]=e[14],e[14]=t,this}setPosition(e,t,n){let s=this.elements;return e.isVector3?(s[12]=e.x,s[13]=e.y,s[14]=e.z):(s[12]=e,s[13]=t,s[14]=n),this}invert(){let e=this.elements,t=e[0],n=e[1],s=e[2],r=e[3],a=e[4],o=e[5],l=e[6],c=e[7],h=e[8],f=e[9],u=e[10],d=e[11],g=e[12],b=e[13],m=e[14],p=e[15],E=t*o-n*a,C=t*l-s*a,y=t*c-r*a,w=n*l-s*o,T=n*c-r*o,I=s*c-r*l,x=h*b-f*g,A=h*m-u*g,D=h*p-d*g,k=f*m-u*b,G=f*p-d*b,Y=u*p-d*m,F=E*Y-C*G+y*k+w*D-T*A+I*x;if(F===0)return this.set(0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0);let $=1/F;return e[0]=(o*Y-l*G+c*k)*$,e[1]=(s*G-n*Y-r*k)*$,e[2]=(b*I-m*T+p*w)*$,e[3]=(u*T-f*I-d*w)*$,e[4]=(l*D-a*Y-c*A)*$,e[5]=(t*Y-s*D+r*A)*$,e[6]=(m*y-g*I-p*C)*$,e[7]=(h*I-u*y+d*C)*$,e[8]=(a*G-o*D+c*x)*$,e[9]=(n*D-t*G-r*x)*$,e[10]=(g*T-b*y+p*E)*$,e[11]=(f*y-h*T-d*E)*$,e[12]=(o*A-a*k-l*x)*$,e[13]=(t*k-n*A+s*x)*$,e[14]=(b*C-g*w-m*E)*$,e[15]=(h*w-f*C+u*E)*$,this}scale(e){let t=this.elements,n=e.x,s=e.y,r=e.z;return t[0]*=n,t[4]*=s,t[8]*=r,t[1]*=n,t[5]*=s,t[9]*=r,t[2]*=n,t[6]*=s,t[10]*=r,t[3]*=n,t[7]*=s,t[11]*=r,this}getMaxScaleOnAxis(){let e=this.elements,t=e[0]*e[0]+e[1]*e[1]+e[2]*e[2],n=e[4]*e[4]+e[5]*e[5]+e[6]*e[6],s=e[8]*e[8]+e[9]*e[9]+e[10]*e[10];return Math.sqrt(Math.max(t,n,s))}makeTranslation(e,t,n){return e.isVector3?this.set(1,0,0,e.x,0,1,0,e.y,0,0,1,e.z,0,0,0,1):this.set(1,0,0,e,0,1,0,t,0,0,1,n,0,0,0,1),this}makeRotationX(e){let t=Math.cos(e),n=Math.sin(e);return this.set(1,0,0,0,0,t,-n,0,0,n,t,0,0,0,0,1),this}makeRotationY(e){let t=Math.cos(e),n=Math.sin(e);return this.set(t,0,n,0,0,1,0,0,-n,0,t,0,0,0,0,1),this}makeRotationZ(e){let t=Math.cos(e),n=Math.sin(e);return this.set(t,-n,0,0,n,t,0,0,0,0,1,0,0,0,0,1),this}makeRotationAxis(e,t){let n=Math.cos(t),s=Math.sin(t),r=1-n,a=e.x,o=e.y,l=e.z,c=r*a,h=r*o;return this.set(c*a+n,c*o-s*l,c*l+s*o,0,c*o+s*l,h*o+n,h*l-s*a,0,c*l-s*o,h*l+s*a,r*l*l+n,0,0,0,0,1),this}makeScale(e,t,n){return this.set(e,0,0,0,0,t,0,0,0,0,n,0,0,0,0,1),this}makeShear(e,t,n,s,r,a){return this.set(1,n,r,0,e,1,a,0,t,s,1,0,0,0,0,1),this}compose(e,t,n){let s=this.elements,r=t._x,a=t._y,o=t._z,l=t._w,c=r+r,h=a+a,f=o+o,u=r*c,d=r*h,g=r*f,b=a*h,m=a*f,p=o*f,E=l*c,C=l*h,y=l*f,w=n.x,T=n.y,I=n.z;return s[0]=(1-(b+p))*w,s[1]=(d+y)*w,s[2]=(g-C)*w,s[3]=0,s[4]=(d-y)*T,s[5]=(1-(u+p))*T,s[6]=(m+E)*T,s[7]=0,s[8]=(g+C)*I,s[9]=(m-E)*I,s[10]=(1-(u+b))*I,s[11]=0,s[12]=e.x,s[13]=e.y,s[14]=e.z,s[15]=1,this}decompose(e,t,n){let s=this.elements;e.x=s[12],e.y=s[13],e.z=s[14];let r=this.determinantAffine();if(r===0)return n.set(1,1,1),t.identity(),this;let a=Qi.set(s[0],s[1],s[2]).length(),o=Qi.set(s[4],s[5],s[6]).length(),l=Qi.set(s[8],s[9],s[10]).length();r<0&&(a=-a),Nn.copy(this);let c=1/a,h=1/o,f=1/l;return Nn.elements[0]*=c,Nn.elements[1]*=c,Nn.elements[2]*=c,Nn.elements[4]*=h,Nn.elements[5]*=h,Nn.elements[6]*=h,Nn.elements[8]*=f,Nn.elements[9]*=f,Nn.elements[10]*=f,t.setFromRotationMatrix(Nn),n.x=a,n.y=o,n.z=l,this}makePerspective(e,t,n,s,r,a,o=kn,l=!1){let c=this.elements,h=2*r/(t-e),f=2*r/(n-s),u=(t+e)/(t-e),d=(n+s)/(n-s),g,b;if(l)g=r/(a-r),b=a*r/(a-r);else if(o===kn)g=-(a+r)/(a-r),b=-2*a*r/(a-r);else if(o===ms)g=-a/(a-r),b=-a*r/(a-r);else throw new Error("THREE.Matrix4.makePerspective(): Invalid coordinate system: "+o);return c[0]=h,c[4]=0,c[8]=u,c[12]=0,c[1]=0,c[5]=f,c[9]=d,c[13]=0,c[2]=0,c[6]=0,c[10]=g,c[14]=b,c[3]=0,c[7]=0,c[11]=-1,c[15]=0,this}makeOrthographic(e,t,n,s,r,a,o=kn,l=!1){let c=this.elements,h=2/(t-e),f=2/(n-s),u=-(t+e)/(t-e),d=-(n+s)/(n-s),g,b;if(l)g=1/(a-r),b=a/(a-r);else if(o===kn)g=-2/(a-r),b=-(a+r)/(a-r);else if(o===ms)g=-1/(a-r),b=-r/(a-r);else throw new Error("THREE.Matrix4.makeOrthographic(): Invalid coordinate system: "+o);return c[0]=h,c[4]=0,c[8]=0,c[12]=u,c[1]=0,c[5]=f,c[9]=0,c[13]=d,c[2]=0,c[6]=0,c[10]=g,c[14]=b,c[3]=0,c[7]=0,c[11]=0,c[15]=1,this}equals(e){let t=this.elements,n=e.elements;for(let s=0;s<16;s++)if(t[s]!==n[s])return!1;return!0}fromArray(e,t=0){for(let n=0;n<16;n++)this.elements[n]=e[n+t];return this}toArray(e=[],t=0){let n=this.elements;return e[t]=n[0],e[t+1]=n[1],e[t+2]=n[2],e[t+3]=n[3],e[t+4]=n[4],e[t+5]=n[5],e[t+6]=n[6],e[t+7]=n[7],e[t+8]=n[8],e[t+9]=n[9],e[t+10]=n[10],e[t+11]=n[11],e[t+12]=n[12],e[t+13]=n[13],e[t+14]=n[14],e[t+15]=n[15],e}},Qi=new U,Nn=new xt,md=new U(0,0,0),gd=new U(1,1,1),fi=new U,ta=new U,yn=new U,Hc=new xt,Gc=new Gt,wn=class i{constructor(e=0,t=0,n=0,s=i.DEFAULT_ORDER){this.isEuler=!0,this._x=e,this._y=t,this._z=n,this._order=s}get x(){return this._x}set x(e){this._x=e,this._onChangeCallback()}get y(){return this._y}set y(e){this._y=e,this._onChangeCallback()}get z(){return this._z}set z(e){this._z=e,this._onChangeCallback()}get order(){return this._order}set order(e){this._order=e,this._onChangeCallback()}set(e,t,n,s=this._order){return this._x=e,this._y=t,this._z=n,this._order=s,this._onChangeCallback(),this}clone(){return new this.constructor(this._x,this._y,this._z,this._order)}copy(e){return this._x=e._x,this._y=e._y,this._z=e._z,this._order=e._order,this._onChangeCallback(),this}setFromRotationMatrix(e,t=this._order,n=!0){let s=e.elements,r=s[0],a=s[4],o=s[8],l=s[1],c=s[5],h=s[9],f=s[2],u=s[6],d=s[10];switch(t){case"XYZ":this._y=Math.asin(mt(o,-1,1)),Math.abs(o)<.9999999?(this._x=Math.atan2(-h,d),this._z=Math.atan2(-a,r)):(this._x=Math.atan2(u,c),this._z=0);break;case"YXZ":this._x=Math.asin(-mt(h,-1,1)),Math.abs(h)<.9999999?(this._y=Math.atan2(o,d),this._z=Math.atan2(l,c)):(this._y=Math.atan2(-f,r),this._z=0);break;case"ZXY":this._x=Math.asin(mt(u,-1,1)),Math.abs(u)<.9999999?(this._y=Math.atan2(-f,d),this._z=Math.atan2(-a,c)):(this._y=0,this._z=Math.atan2(l,r));break;case"ZYX":this._y=Math.asin(-mt(f,-1,1)),Math.abs(f)<.9999999?(this._x=Math.atan2(u,d),this._z=Math.atan2(l,r)):(this._x=0,this._z=Math.atan2(-a,c));break;case"YZX":this._z=Math.asin(mt(l,-1,1)),Math.abs(l)<.9999999?(this._x=Math.atan2(-h,c),this._y=Math.atan2(-f,r)):(this._x=0,this._y=Math.atan2(o,d));break;case"XZY":this._z=Math.asin(-mt(a,-1,1)),Math.abs(a)<.9999999?(this._x=Math.atan2(u,c),this._y=Math.atan2(o,r)):(this._x=Math.atan2(-h,d),this._y=0);break;default:je("Euler: .setFromRotationMatrix() encountered an unknown order: "+t)}return this._order=t,n===!0&&this._onChangeCallback(),this}setFromQuaternion(e,t,n){return Hc.makeRotationFromQuaternion(e),this.setFromRotationMatrix(Hc,t,n)}setFromVector3(e,t=this._order){return this.set(e.x,e.y,e.z,t)}reorder(e){return Gc.setFromEuler(this),this.setFromQuaternion(Gc,e)}equals(e){return e._x===this._x&&e._y===this._y&&e._z===this._z&&e._order===this._order}fromArray(e){return this._x=e[0],this._y=e[1],this._z=e[2],e[3]!==void 0&&(this._order=e[3]),this._onChangeCallback(),this}toArray(e=[],t=0){return e[t]=this._x,e[t+1]=this._y,e[t+2]=this._z,e[t+3]=this._order,e}_onChange(e){return this._onChangeCallback=e,this}_onChangeCallback(){}*[Symbol.iterator](){yield this._x,yield this._y,yield this._z,yield this._order}};wn.DEFAULT_ORDER="XYZ";var vs=class{constructor(){this.mask=1}set(e){this.mask=(1<<e|0)>>>0}enable(e){this.mask|=1<<e|0}enableAll(){this.mask=-1}toggle(e){this.mask^=1<<e|0}disable(e){this.mask&=~(1<<e|0)}disableAll(){this.mask=0}test(e){return(this.mask&e.mask)!==0}isEnabled(e){return(this.mask&(1<<e|0))!==0}},_d=0,Wc=new U,es=new Gt,ei=new xt,na=new U,qs=new U,xd=new U,vd=new Gt,qc=new U(1,0,0),Xc=new U(0,1,0),$c=new U(0,0,1),Yc={type:"added"},yd={type:"removed"},ts={type:"childadded",child:null},vl={type:"childremoved",child:null},Ht=class i extends $n{constructor(){super(),this.isObject3D=!0,Object.defineProperty(this,"id",{value:_d++}),this.uuid=Ls(),this.name="",this.type="Object3D",this.parent=null,this.children=[],this.up=i.DEFAULT_UP.clone();let e=new U,t=new wn,n=new Gt,s=new U(1,1,1);function r(){n.setFromEuler(t,!1)}function a(){t.setFromQuaternion(n,void 0,!1)}t._onChange(r),n._onChange(a),Object.defineProperties(this,{position:{configurable:!0,enumerable:!0,value:e},rotation:{configurable:!0,enumerable:!0,value:t},quaternion:{configurable:!0,enumerable:!0,value:n},scale:{configurable:!0,enumerable:!0,value:s},modelViewMatrix:{value:new xt},normalMatrix:{value:new st}}),this.matrix=new xt,this.matrixWorld=new xt,this.matrixAutoUpdate=i.DEFAULT_MATRIX_AUTO_UPDATE,this.matrixWorldAutoUpdate=i.DEFAULT_MATRIX_WORLD_AUTO_UPDATE,this.matrixWorldNeedsUpdate=!1,this.layers=new vs,this.visible=!0,this.castShadow=!1,this.receiveShadow=!1,this.frustumCulled=!0,this.renderOrder=0,this.animations=[],this.customDepthMaterial=void 0,this.customDistanceMaterial=void 0,this.static=!1,this.userData={},this.pivot=null}onBeforeShadow(){}onAfterShadow(){}onBeforeRender(){}onAfterRender(){}applyMatrix4(e){this.matrixAutoUpdate&&this.updateMatrix(),this.matrix.premultiply(e),this.matrix.decompose(this.position,this.quaternion,this.scale)}applyQuaternion(e){return this.quaternion.premultiply(e),this}setRotationFromAxisAngle(e,t){this.quaternion.setFromAxisAngle(e,t)}setRotationFromEuler(e){this.quaternion.setFromEuler(e,!0)}setRotationFromMatrix(e){this.quaternion.setFromRotationMatrix(e)}setRotationFromQuaternion(e){this.quaternion.copy(e)}rotateOnAxis(e,t){return es.setFromAxisAngle(e,t),this.quaternion.multiply(es),this}rotateOnWorldAxis(e,t){return es.setFromAxisAngle(e,t),this.quaternion.premultiply(es),this}rotateX(e){return this.rotateOnAxis(qc,e)}rotateY(e){return this.rotateOnAxis(Xc,e)}rotateZ(e){return this.rotateOnAxis($c,e)}translateOnAxis(e,t){return Wc.copy(e).applyQuaternion(this.quaternion),this.position.add(Wc.multiplyScalar(t)),this}translateX(e){return this.translateOnAxis(qc,e)}translateY(e){return this.translateOnAxis(Xc,e)}translateZ(e){return this.translateOnAxis($c,e)}localToWorld(e){return this.updateWorldMatrix(!0,!1),e.applyMatrix4(this.matrixWorld)}worldToLocal(e){return this.updateWorldMatrix(!0,!1),e.applyMatrix4(ei.copy(this.matrixWorld).invert())}lookAt(e,t,n){e.isVector3?na.copy(e):na.set(e,t,n);let s=this.parent;this.updateWorldMatrix(!0,!1),qs.setFromMatrixPosition(this.matrixWorld),this.isCamera||this.isLight?ei.lookAt(qs,na,this.up):ei.lookAt(na,qs,this.up),this.quaternion.setFromRotationMatrix(ei),s&&(ei.extractRotation(s.matrixWorld),es.setFromRotationMatrix(ei),this.quaternion.premultiply(es.invert()))}add(e){if(arguments.length>1){for(let t=0;t<arguments.length;t++)this.add(arguments[t]);return this}return e===this?(nt("Object3D.add: object can't be added as a child of itself.",e),this):(e&&e.isObject3D?(e.removeFromParent(),e.parent=this,this.children.push(e),e.dispatchEvent(Yc),ts.child=e,this.dispatchEvent(ts),ts.child=null):nt("Object3D.add: object not an instance of THREE.Object3D.",e),this)}remove(e){if(arguments.length>1){for(let n=0;n<arguments.length;n++)this.remove(arguments[n]);return this}let t=this.children.indexOf(e);return t!==-1&&(e.parent=null,this.children.splice(t,1),e.dispatchEvent(yd),vl.child=e,this.dispatchEvent(vl),vl.child=null),this}removeFromParent(){let e=this.parent;return e!==null&&e.remove(this),this}clear(){return this.remove(...this.children)}attach(e){return this.updateWorldMatrix(!0,!1),ei.copy(this.matrixWorld).invert(),e.parent!==null&&(e.parent.updateWorldMatrix(!0,!1),ei.multiply(e.parent.matrixWorld)),e.applyMatrix4(ei),e.removeFromParent(),e.parent=this,this.children.push(e),e.updateWorldMatrix(!1,!0),e.dispatchEvent(Yc),ts.child=e,this.dispatchEvent(ts),ts.child=null,this}getObjectById(e){return this.getObjectByProperty("id",e)}getObjectByName(e){return this.getObjectByProperty("name",e)}getObjectByProperty(e,t){if(this[e]===t)return this;for(let n=0,s=this.children.length;n<s;n++){let a=this.children[n].getObjectByProperty(e,t);if(a!==void 0)return a}}getObjectsByProperty(e,t,n=[]){this[e]===t&&n.push(this);let s=this.children;for(let r=0,a=s.length;r<a;r++)s[r].getObjectsByProperty(e,t,n);return n}getWorldPosition(e){return this.updateWorldMatrix(!0,!1),e.setFromMatrixPosition(this.matrixWorld)}getWorldQuaternion(e){return this.updateWorldMatrix(!0,!1),this.matrixWorld.decompose(qs,e,xd),e}getWorldScale(e){return this.updateWorldMatrix(!0,!1),this.matrixWorld.decompose(qs,vd,e),e}getWorldDirection(e){this.updateWorldMatrix(!0,!1);let t=this.matrixWorld.elements;return e.set(t[8],t[9],t[10]).normalize()}raycast(){}intersectsFrustum(){}traverse(e){e(this);let t=this.children;for(let n=0,s=t.length;n<s;n++)t[n].traverse(e)}traverseVisible(e){if(this.visible===!1)return;e(this);let t=this.children;for(let n=0,s=t.length;n<s;n++)t[n].traverseVisible(e)}traverseAncestors(e){let t=this.parent;t!==null&&(e(t),t.traverseAncestors(e))}updateMatrix(){this.matrix.compose(this.position,this.quaternion,this.scale);let e=this.pivot;if(e!==null){let t=e.x,n=e.y,s=e.z,r=this.matrix.elements;r[12]+=t-r[0]*t-r[4]*n-r[8]*s,r[13]+=n-r[1]*t-r[5]*n-r[9]*s,r[14]+=s-r[2]*t-r[6]*n-r[10]*s}this.matrixWorldNeedsUpdate=!0}updateMatrixWorld(e){this.matrixAutoUpdate&&this.updateMatrix(),(this.matrixWorldNeedsUpdate||e)&&(this.matrixWorldAutoUpdate===!0&&(this.parent===null?this.matrixWorld.copy(this.matrix):this.matrixWorld.multiplyMatrices(this.parent.matrixWorld,this.matrix)),this.matrixWorldNeedsUpdate=!1,e=!0);let t=this.children;for(let n=0,s=t.length;n<s;n++)t[n].updateMatrixWorld(e)}updateWorldMatrix(e,t,n=!1){let s=this.parent;if(e===!0&&s!==null&&s.updateWorldMatrix(!0,!1),this.matrixAutoUpdate&&this.updateMatrix(),(this.matrixWorldNeedsUpdate||n)&&(this.matrixWorldAutoUpdate===!0&&(this.parent===null?this.matrixWorld.copy(this.matrix):this.matrixWorld.multiplyMatrices(this.parent.matrixWorld,this.matrix)),this.matrixWorldNeedsUpdate=!1,n=!0),t===!0){let r=this.children;for(let a=0,o=r.length;a<o;a++)r[a].updateWorldMatrix(!1,!0,n)}}toJSON(e){let t=e===void 0||typeof e=="string",n={};t&&(e={geometries:{},materials:{},textures:{},images:{},shapes:{},skeletons:{},animations:{},nodes:{}},n.metadata={version:4.7,type:"Object",generator:"Object3D.toJSON"});let s={};s.uuid=this.uuid,s.type=this.type,s.name=this.name,s.castShadow=this.castShadow,s.receiveShadow=this.receiveShadow,s.visible=this.visible,s.frustumCulled=this.frustumCulled,s.renderOrder=this.renderOrder,s.static=this.static,s.matrixAutoUpdate=this.matrixAutoUpdate,Object.keys(this.userData).length>0&&(s.userData=this.userData),s.layers=this.layers.mask,s.matrix=this.matrix.toArray(),s.up=this.up.toArray(),this.pivot!==null&&(s.pivot=this.pivot.toArray()),this.morphTargetDictionary!==void 0&&(s.morphTargetDictionary=Object.assign({},this.morphTargetDictionary)),this.morphTargetInfluences!==void 0&&(s.morphTargetInfluences=this.morphTargetInfluences.slice()),this.isInstancedMesh&&(s.type="InstancedMesh",s.count=this.count,s.instanceMatrix=this.instanceMatrix.toJSON(),this.instanceColor!==null&&(s.instanceColor=this.instanceColor.toJSON())),this.isBatchedMesh&&(s.type="BatchedMesh",s.perObjectFrustumCulled=this.perObjectFrustumCulled,s.sortObjects=this.sortObjects,s.drawRanges=this._drawRanges,s.reservedRanges=this._reservedRanges,s.geometryInfo=this._geometryInfo.map(o=>({...o,boundingBox:o.boundingBox?o.boundingBox.toJSON():void 0,boundingSphere:o.boundingSphere?o.boundingSphere.toJSON():void 0})),s.instanceInfo=this._instanceInfo.map(o=>({...o})),s.availableInstanceIds=this._availableInstanceIds.slice(),s.availableGeometryIds=this._availableGeometryIds.slice(),s.nextIndexStart=this._nextIndexStart,s.nextVertexStart=this._nextVertexStart,s.geometryCount=this._geometryCount,s.maxInstanceCount=this._maxInstanceCount,s.maxVertexCount=this._maxVertexCount,s.maxIndexCount=this._maxIndexCount,s.geometryInitialized=this._geometryInitialized,s.matricesTexture=this._matricesTexture.toJSON(e),s.indirectTexture=this._indirectTexture.toJSON(e),this._colorsTexture!==null&&(s.colorsTexture=this._colorsTexture.toJSON(e)),this.boundingSphere!==null&&(s.boundingSphere=this.boundingSphere.toJSON()),this.boundingBox!==null&&(s.boundingBox=this.boundingBox.toJSON()));function r(o,l){return o[l.uuid]===void 0&&(o[l.uuid]=l.toJSON(e)),l.uuid}if(this.isScene)this.background&&(this.background.isColor?s.background=this.background.toJSON():this.background.isTexture&&(s.background=this.background.toJSON(e).uuid)),this.environment&&this.environment.isTexture&&this.environment.isRenderTargetTexture!==!0&&(s.environment=this.environment.toJSON(e).uuid);else if(this.isMesh||this.isLine||this.isPoints){s.geometry=r(e.geometries,this.geometry);let o=this.geometry.parameters;if(o!==void 0&&o.shapes!==void 0){let l=o.shapes;if(Array.isArray(l))for(let c=0,h=l.length;c<h;c++){let f=l[c];r(e.shapes,f)}else r(e.shapes,l)}}if(this.isSkinnedMesh&&(s.bindMode=this.bindMode,s.bindMatrix=this.bindMatrix.toArray(),this.skeleton!==void 0&&(r(e.skeletons,this.skeleton),s.skeleton=this.skeleton.uuid)),this.material!==void 0)if(Array.isArray(this.material)){let o=[];for(let l=0,c=this.material.length;l<c;l++)o.push(r(e.materials,this.material[l]));s.material=o}else s.material=r(e.materials,this.material);if(this.children.length>0){s.children=[];for(let o=0;o<this.children.length;o++)s.children.push(this.children[o].toJSON(e).object)}if(this.animations.length>0){s.animations=[];for(let o=0;o<this.animations.length;o++){let l=this.animations[o];s.animations.push(r(e.animations,l))}}if(t){let o=a(e.geometries),l=a(e.materials),c=a(e.textures),h=a(e.images),f=a(e.shapes),u=a(e.skeletons),d=a(e.animations),g=a(e.nodes);o.length>0&&(n.geometries=o),l.length>0&&(n.materials=l),c.length>0&&(n.textures=c),h.length>0&&(n.images=h),f.length>0&&(n.shapes=f),u.length>0&&(n.skeletons=u),d.length>0&&(n.animations=d),g.length>0&&(n.nodes=g)}return n.object=s,n;function a(o){let l=[];for(let c in o){let h=o[c];delete h.metadata,l.push(h)}return l}}clone(e){return new this.constructor().copy(this,e)}copy(e,t=!0){if(this.name=e.name,this.up.copy(e.up),this.position.copy(e.position),this.rotation.order=e.rotation.order,this.quaternion.copy(e.quaternion),this.scale.copy(e.scale),this.pivot=e.pivot!==null?e.pivot.clone():null,this.matrix.copy(e.matrix),this.matrixWorld.copy(e.matrixWorld),this.matrixAutoUpdate=e.matrixAutoUpdate,this.matrixWorldAutoUpdate=e.matrixWorldAutoUpdate,this.matrixWorldNeedsUpdate=e.matrixWorldNeedsUpdate,this.layers.mask=e.layers.mask,this.visible=e.visible,this.castShadow=e.castShadow,this.receiveShadow=e.receiveShadow,this.frustumCulled=e.frustumCulled,this.renderOrder=e.renderOrder,this.static=e.static,this.animations=e.animations.slice(),this.userData=JSON.parse(JSON.stringify(e.userData)),t===!0)for(let n=0;n<e.children.length;n++){let s=e.children[n];this.add(s.clone())}return this}dispose(){this.dispatchEvent({type:"dispose"})}};Ht.DEFAULT_UP=new U(0,1,0);Ht.DEFAULT_MATRIX_AUTO_UPDATE=!0;Ht.DEFAULT_MATRIX_WORLD_AUTO_UPDATE=!0;var zt=class extends Ht{constructor(){super(),this.isGroup=!0,this.type="Group"}},bd={type:"move"},ys=class{constructor(){this._targetRay=null,this._grip=null,this._hand=null}getHandSpace(){return this._hand===null&&(this._hand=new zt,this._hand.matrixAutoUpdate=!1,this._hand.visible=!1,this._hand.joints={},this._hand.inputState={pinching:!1}),this._hand}getTargetRaySpace(){return this._targetRay===null&&(this._targetRay=new zt,this._targetRay.matrixAutoUpdate=!1,this._targetRay.visible=!1,this._targetRay.hasLinearVelocity=!1,this._targetRay.linearVelocity=new U,this._targetRay.hasAngularVelocity=!1,this._targetRay.angularVelocity=new U),this._targetRay}getGripSpace(){return this._grip===null&&(this._grip=new zt,this._grip.matrixAutoUpdate=!1,this._grip.visible=!1,this._grip.hasLinearVelocity=!1,this._grip.linearVelocity=new U,this._grip.hasAngularVelocity=!1,this._grip.angularVelocity=new U,this._grip.eventsEnabled=!1),this._grip}dispatchEvent(e){return this._targetRay!==null&&this._targetRay.dispatchEvent(e),this._grip!==null&&this._grip.dispatchEvent(e),this._hand!==null&&this._hand.dispatchEvent(e),this}connect(e){if(e&&e.hand){let t=this._hand;if(t)for(let n of e.hand.values())this._getHandJoint(t,n)}return this.dispatchEvent({type:"connected",data:e}),this}disconnect(e){return this.dispatchEvent({type:"disconnected",data:e}),this._targetRay!==null&&(this._targetRay.visible=!1),this._grip!==null&&(this._grip.visible=!1),this._hand!==null&&(this._hand.visible=!1),this}update(e,t,n){let s=null,r=null,a=null,o=this._targetRay,l=this._grip,c=this._hand;if(e&&t.session.visibilityState!=="visible-blurred"){if(c&&e.hand){a=!0;for(let b of e.hand.values()){let m=t.getJointPose(b,n),p=this._getHandJoint(c,b);m!==null&&(p.matrix.fromArray(m.transform.matrix),p.matrix.decompose(p.position,p.rotation,p.scale),p.matrixWorldNeedsUpdate=!0,p.jointRadius=m.radius),p.visible=m!==null}let h=c.joints["index-finger-tip"],f=c.joints["thumb-tip"],u=h.position.distanceTo(f.position),d=.02,g=.005;c.inputState.pinching&&u>d+g?(c.inputState.pinching=!1,this.dispatchEvent({type:"pinchend",handedness:e.handedness,target:this})):!c.inputState.pinching&&u<=d-g&&(c.inputState.pinching=!0,this.dispatchEvent({type:"pinchstart",handedness:e.handedness,target:this}))}else l!==null&&e.gripSpace&&(r=t.getPose(e.gripSpace,n),r!==null&&(l.matrix.fromArray(r.transform.matrix),l.matrix.decompose(l.position,l.rotation,l.scale),l.matrixWorldNeedsUpdate=!0,r.linearVelocity?(l.hasLinearVelocity=!0,l.linearVelocity.copy(r.linearVelocity)):l.hasLinearVelocity=!1,r.angularVelocity?(l.hasAngularVelocity=!0,l.angularVelocity.copy(r.angularVelocity)):l.hasAngularVelocity=!1,l.eventsEnabled&&l.dispatchEvent({type:"gripUpdated",data:e,target:this})));o!==null&&(s=t.getPose(e.targetRaySpace,n),s===null&&r!==null&&(s=r),s!==null&&(o.matrix.fromArray(s.transform.matrix),o.matrix.decompose(o.position,o.rotation,o.scale),o.matrixWorldNeedsUpdate=!0,s.linearVelocity?(o.hasLinearVelocity=!0,o.linearVelocity.copy(s.linearVelocity)):o.hasLinearVelocity=!1,s.angularVelocity?(o.hasAngularVelocity=!0,o.angularVelocity.copy(s.angularVelocity)):o.hasAngularVelocity=!1,this.dispatchEvent(bd)))}return o!==null&&(o.visible=s!==null),l!==null&&(l.visible=r!==null),c!==null&&(c.visible=a!==null),this}_getHandJoint(e,t){if(e.joints[t.jointName]===void 0){let n=new zt;n.matrixAutoUpdate=!1,n.visible=!1,e.joints[t.jointName]=n,e.add(n)}return e.joints[t.jointName]}},eh={aliceblue:15792383,antiquewhite:16444375,aqua:65535,aquamarine:8388564,azure:15794175,beige:16119260,bisque:16770244,black:0,blanchedalmond:16772045,blue:255,blueviolet:9055202,brown:10824234,burlywood:14596231,cadetblue:6266528,chartreuse:8388352,chocolate:13789470,coral:16744272,cornflowerblue:6591981,cornsilk:16775388,crimson:14423100,cyan:65535,darkblue:139,darkcyan:35723,darkgoldenrod:12092939,darkgray:11119017,darkgreen:25600,darkgrey:11119017,darkkhaki:12433259,darkmagenta:9109643,darkolivegreen:5597999,darkorange:16747520,darkorchid:10040012,darkred:9109504,darksalmon:15308410,darkseagreen:9419919,darkslateblue:4734347,darkslategray:3100495,darkslategrey:3100495,darkturquoise:52945,darkviolet:9699539,deeppink:16716947,deepskyblue:49151,dimgray:6908265,dimgrey:6908265,dodgerblue:2003199,firebrick:11674146,floralwhite:16775920,forestgreen:2263842,fuchsia:16711935,gainsboro:14474460,ghostwhite:16316671,gold:16766720,goldenrod:14329120,gray:8421504,green:32768,greenyellow:11403055,grey:8421504,honeydew:15794160,hotpink:16738740,indianred:13458524,indigo:4915330,ivory:16777200,khaki:15787660,lavender:15132410,lavenderblush:16773365,lawngreen:8190976,lemonchiffon:16775885,lightblue:11393254,lightcoral:15761536,lightcyan:14745599,lightgoldenrodyellow:16448210,lightgray:13882323,lightgreen:9498256,lightgrey:13882323,lightpink:16758465,lightsalmon:16752762,lightseagreen:2142890,lightskyblue:8900346,lightslategray:7833753,lightslategrey:7833753,lightsteelblue:11584734,lightyellow:16777184,lime:65280,limegreen:3329330,linen:16445670,magenta:16711935,maroon:8388608,mediumaquamarine:6737322,mediumblue:205,mediumorchid:12211667,mediumpurple:9662683,mediumseagreen:3978097,mediumslateblue:8087790,mediumspringgreen:64154,mediumturquoise:4772300,mediumvioletred:13047173,midnightblue:1644912,mintcream:16121850,mistyrose:16770273,moccasin:16770229,navajowhite:16768685,navy:128,oldlace:16643558,olive:8421376,olivedrab:7048739,orange:16753920,orangered:16729344,orchid:14315734,palegoldenrod:15657130,palegreen:10025880,paleturquoise:11529966,palevioletred:14381203,papayawhip:16773077,peachpuff:16767673,peru:13468991,pink:16761035,plum:14524637,powderblue:11591910,purple:8388736,rebeccapurple:6697881,red:16711680,rosybrown:12357519,royalblue:4286945,saddlebrown:9127187,salmon:16416882,sandybrown:16032864,seagreen:3050327,seashell:16774638,sienna:10506797,silver:12632256,skyblue:8900331,slateblue:6970061,slategray:7372944,slategrey:7372944,snow:16775930,springgreen:65407,steelblue:4620980,tan:13808780,teal:32896,thistle:14204888,tomato:16737095,turquoise:4251856,violet:15631086,wheat:16113331,white:16777215,whitesmoke:16119285,yellow:16776960,yellowgreen:10145074},pi={h:0,s:0,l:0},ia={h:0,s:0,l:0};function yl(i,e,t){return t<0&&(t+=1),t>1&&(t-=1),t<1/6?i+(e-i)*6*t:t<1/2?e:t<2/3?i+(e-i)*6*(2/3-t):i}var Qe=class{constructor(e,t,n){return this.isColor=!0,this.r=1,this.g=1,this.b=1,this.set(e,t,n)}set(e,t,n){if(t===void 0&&n===void 0){let s=e;s&&s.isColor?this.copy(s):typeof s=="number"?this.setHex(s):typeof s=="string"&&this.setStyle(s)}else this.setRGB(e,t,n);return this}setScalar(e){return this.r=e,this.g=e,this.b=e,this}setHex(e,t=cn){return e=Math.floor(e),this.r=(e>>16&255)/255,this.g=(e>>8&255)/255,this.b=(e&255)/255,pt.colorSpaceToWorking(this,t),this}setRGB(e,t,n,s=pt.workingColorSpace){return this.r=e,this.g=t,this.b=n,pt.colorSpaceToWorking(this,s),this}setHSL(e,t,n,s=pt.workingColorSpace){if(e=hc(e,1),t=mt(t,0,1),n=mt(n,0,1),t===0)this.r=this.g=this.b=n;else{let r=n<=.5?n*(1+t):n+t-n*t,a=2*n-r;this.r=yl(a,r,e+1/3),this.g=yl(a,r,e),this.b=yl(a,r,e-1/3)}return pt.colorSpaceToWorking(this,s),this}setStyle(e,t=cn){function n(r){r!==void 0&&parseFloat(r)<1&&je("Color: Alpha component of "+e+" will be ignored.")}let s;if(s=/^(\w+)\(([^\)]*)\)/.exec(e)){let r,a=s[1],o=s[2];switch(a){case"rgb":case"rgba":if(r=/^\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(o))return n(r[4]),this.setRGB(Math.min(255,parseInt(r[1],10))/255,Math.min(255,parseInt(r[2],10))/255,Math.min(255,parseInt(r[3],10))/255,t);if(r=/^\s*(\d+)\%\s*,\s*(\d+)\%\s*,\s*(\d+)\%\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(o))return n(r[4]),this.setRGB(Math.min(100,parseInt(r[1],10))/100,Math.min(100,parseInt(r[2],10))/100,Math.min(100,parseInt(r[3],10))/100,t);break;case"hsl":case"hsla":if(r=/^\s*(\d*\.?\d+)\s*,\s*(\d*\.?\d+)\%\s*,\s*(\d*\.?\d+)\%\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(o))return n(r[4]),this.setHSL(parseFloat(r[1])/360,parseFloat(r[2])/100,parseFloat(r[3])/100,t);break;default:je("Color: Unknown color model "+e)}}else if(s=/^\#([A-Fa-f\d]+)$/.exec(e)){let r=s[1],a=r.length;if(a===3)return this.setRGB(parseInt(r.charAt(0),16)/15,parseInt(r.charAt(1),16)/15,parseInt(r.charAt(2),16)/15,t);if(a===6)return this.setHex(parseInt(r,16),t);je("Color: Invalid hex color "+e)}else if(e&&e.length>0)return this.setColorName(e,t);return this}setColorName(e,t=cn){let n=eh[e.toLowerCase()];return n!==void 0?this.setHex(n,t):je("Color: Unknown color "+e),this}clone(){return new this.constructor(this.r,this.g,this.b)}copy(e){return this.r=e.r,this.g=e.g,this.b=e.b,this}copySRGBToLinear(e){return this.r=ri(e.r),this.g=ri(e.g),this.b=ri(e.b),this}copyLinearToSRGB(e){return this.r=fs(e.r),this.g=fs(e.g),this.b=fs(e.b),this}convertSRGBToLinear(){return this.copySRGBToLinear(this),this}convertLinearToSRGB(){return this.copyLinearToSRGB(this),this}getHex(e=cn){return pt.workingToColorSpace(an.copy(this),e),Math.round(mt(an.r*255,0,255))*65536+Math.round(mt(an.g*255,0,255))*256+Math.round(mt(an.b*255,0,255))}getHexString(e=cn){return("000000"+this.getHex(e).toString(16)).slice(-6)}getHSL(e,t=pt.workingColorSpace){pt.workingToColorSpace(an.copy(this),t);let n=an.r,s=an.g,r=an.b,a=Math.max(n,s,r),o=Math.min(n,s,r),l,c,h=(o+a)/2;if(o===a)l=0,c=0;else{let f=a-o;switch(c=h<=.5?f/(a+o):f/(2-a-o),a){case n:l=(s-r)/f+(s<r?6:0);break;case s:l=(r-n)/f+2;break;case r:l=(n-s)/f+4;break}l/=6}return e.h=l,e.s=c,e.l=h,e}getRGB(e,t=pt.workingColorSpace){return pt.workingToColorSpace(an.copy(this),t),e.r=an.r,e.g=an.g,e.b=an.b,e}getStyle(e=cn){pt.workingToColorSpace(an.copy(this),e);let t=an.r,n=an.g,s=an.b;return e!==cn?`color(${e} ${t.toFixed(3)} ${n.toFixed(3)} ${s.toFixed(3)})`:`rgb(${Math.round(t*255)},${Math.round(n*255)},${Math.round(s*255)})`}offsetHSL(e,t,n){return this.getHSL(pi),this.setHSL(pi.h+e,pi.s+t,pi.l+n)}add(e){return this.r+=e.r,this.g+=e.g,this.b+=e.b,this}addColors(e,t){return this.r=e.r+t.r,this.g=e.g+t.g,this.b=e.b+t.b,this}addScalar(e){return this.r+=e,this.g+=e,this.b+=e,this}sub(e){return this.r=Math.max(0,this.r-e.r),this.g=Math.max(0,this.g-e.g),this.b=Math.max(0,this.b-e.b),this}multiply(e){return this.r*=e.r,this.g*=e.g,this.b*=e.b,this}multiplyScalar(e){return this.r*=e,this.g*=e,this.b*=e,this}lerp(e,t){return this.r+=(e.r-this.r)*t,this.g+=(e.g-this.g)*t,this.b+=(e.b-this.b)*t,this}lerpColors(e,t,n){return this.r=e.r+(t.r-e.r)*n,this.g=e.g+(t.g-e.g)*n,this.b=e.b+(t.b-e.b)*n,this}lerpHSL(e,t){this.getHSL(pi),e.getHSL(ia);let n=Qs(pi.h,ia.h,t),s=Qs(pi.s,ia.s,t),r=Qs(pi.l,ia.l,t);return this.setHSL(n,s,r),this}setFromVector3(e){return this.r=e.x,this.g=e.y,this.b=e.z,this}applyMatrix3(e){let t=this.r,n=this.g,s=this.b,r=e.elements;return this.r=r[0]*t+r[3]*n+r[6]*s,this.g=r[1]*t+r[4]*n+r[7]*s,this.b=r[2]*t+r[5]*n+r[8]*s,this}equals(e){return e.r===this.r&&e.g===this.g&&e.b===this.b}fromArray(e,t=0){return this.r=e[t],this.g=e[t+1],this.b=e[t+2],this}toArray(e=[],t=0){return e[t]=this.r,e[t+1]=this.g,e[t+2]=this.b,e}fromBufferAttribute(e,t){return this.r=e.getX(t),this.g=e.getY(t),this.b=e.getZ(t),this}toJSON(){return this.getHex()}*[Symbol.iterator](){yield this.r,yield this.g,yield this.b}},an=new Qe;Qe.NAMES=eh;var or=class i{constructor(e,t=25e-5){this.isFogExp2=!0,this.name="",this.color=new Qe(e),this.density=t}clone(){return new i(this.color,this.density)}toJSON(){return{type:"FogExp2",name:this.name,color:this.color.getHex(),density:this.density}}};var Oi=class extends Ht{constructor(){super(),this.isScene=!0,this.type="Scene",this.background=null,this.environment=null,this.fog=null,this.backgroundBlurriness=0,this.backgroundIntensity=1,this.backgroundRotation=new wn,this.environmentIntensity=1,this.environmentRotation=new wn,this.overrideMaterial=null,typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("observe",{detail:this}))}copy(e,t){return super.copy(e,t),e.background!==null&&(this.background=e.background.clone()),e.environment!==null&&(this.environment=e.environment.clone()),e.fog!==null&&(this.fog=e.fog.clone()),this.backgroundBlurriness=e.backgroundBlurriness,this.backgroundIntensity=e.backgroundIntensity,this.backgroundRotation.copy(e.backgroundRotation),this.environmentIntensity=e.environmentIntensity,this.environmentRotation.copy(e.environmentRotation),e.overrideMaterial!==null&&(this.overrideMaterial=e.overrideMaterial.clone()),this.matrixAutoUpdate=e.matrixAutoUpdate,this}toJSON(e){let t=super.toJSON(e);return this.fog!==null&&(t.object.fog=this.fog.toJSON()),t.object.backgroundBlurriness=this.backgroundBlurriness,t.object.backgroundIntensity=this.backgroundIntensity,t.object.backgroundRotation=this.backgroundRotation.toArray(),t.object.environmentIntensity=this.environmentIntensity,t.object.environmentRotation=this.environmentRotation.toArray(),t}},Dn=new U,ti=new U,bl=new U,ni=new U,ns=new U,is=new U,Zc=new U,Ml=new U,Sl=new U,Tl=new U,El=new Ut,wl=new Ut,Al=new Ut,xi=class i{constructor(e=new U,t=new U,n=new U){this.a=e,this.b=t,this.c=n}static getNormal(e,t,n,s){s.subVectors(n,t),Dn.subVectors(e,t),s.cross(Dn);let r=s.lengthSq();return r>0?s.multiplyScalar(1/Math.sqrt(r)):s.set(0,0,0)}static getBarycoord(e,t,n,s,r){Dn.subVectors(s,t),ti.subVectors(n,t),bl.subVectors(e,t);let a=Dn.dot(Dn),o=Dn.dot(ti),l=Dn.dot(bl),c=ti.dot(ti),h=ti.dot(bl),f=a*c-o*o;if(f===0)return r.set(0,0,0),null;let u=1/f,d=(c*l-o*h)*u,g=(a*h-o*l)*u;return r.set(1-d-g,g,d)}static containsPoint(e,t,n,s){return this.getBarycoord(e,t,n,s,ni)===null?!1:ni.x>=0&&ni.y>=0&&ni.x+ni.y<=1}static getInterpolation(e,t,n,s,r,a,o,l){return this.getBarycoord(e,t,n,s,ni)===null?(l.x=0,l.y=0,"z"in l&&(l.z=0),"w"in l&&(l.w=0),null):(l.setScalar(0),l.addScaledVector(r,ni.x),l.addScaledVector(a,ni.y),l.addScaledVector(o,ni.z),l)}static getInterpolatedAttribute(e,t,n,s,r,a){return El.setScalar(0),wl.setScalar(0),Al.setScalar(0),El.fromBufferAttribute(e,t),wl.fromBufferAttribute(e,n),Al.fromBufferAttribute(e,s),a.setScalar(0),a.addScaledVector(El,r.x),a.addScaledVector(wl,r.y),a.addScaledVector(Al,r.z),a}static isFrontFacing(e,t,n,s){return Dn.subVectors(n,t),ti.subVectors(e,t),Dn.cross(ti).dot(s)<0}set(e,t,n){return this.a.copy(e),this.b.copy(t),this.c.copy(n),this}setFromPointsAndIndices(e,t,n,s){return this.a.copy(e[t]),this.b.copy(e[n]),this.c.copy(e[s]),this}setFromAttributeAndIndices(e,t,n,s){return this.a.fromBufferAttribute(e,t),this.b.fromBufferAttribute(e,n),this.c.fromBufferAttribute(e,s),this}clone(){return new this.constructor().copy(this)}copy(e){return this.a.copy(e.a),this.b.copy(e.b),this.c.copy(e.c),this}getArea(){return Dn.subVectors(this.c,this.b),ti.subVectors(this.a,this.b),Dn.cross(ti).length()*.5}getMidpoint(e){return e.addVectors(this.a,this.b).add(this.c).multiplyScalar(1/3)}getNormal(e){return i.getNormal(this.a,this.b,this.c,e)}getPlane(e){return e.setFromCoplanarPoints(this.a,this.b,this.c)}getBarycoord(e,t){return i.getBarycoord(e,this.a,this.b,this.c,t)}getInterpolation(e,t,n,s,r){return i.getInterpolation(e,this.a,this.b,this.c,t,n,s,r)}containsPoint(e){return i.containsPoint(e,this.a,this.b,this.c)}isFrontFacing(e){return i.isFrontFacing(this.a,this.b,this.c,e)}intersectsBox(e){return e.intersectsTriangle(this)}closestPointToPoint(e,t){let n=this.a,s=this.b,r=this.c,a,o;ns.subVectors(s,n),is.subVectors(r,n),Ml.subVectors(e,n);let l=ns.dot(Ml),c=is.dot(Ml);if(l<=0&&c<=0)return t.copy(n);Sl.subVectors(e,s);let h=ns.dot(Sl),f=is.dot(Sl);if(h>=0&&f<=h)return t.copy(s);let u=l*f-h*c;if(u<=0&&l>=0&&h<=0)return a=l/(l-h),t.copy(n).addScaledVector(ns,a);Tl.subVectors(e,r);let d=ns.dot(Tl),g=is.dot(Tl);if(g>=0&&d<=g)return t.copy(r);let b=d*c-l*g;if(b<=0&&c>=0&&g<=0)return o=c/(c-g),t.copy(n).addScaledVector(is,o);let m=h*g-d*f;if(m<=0&&f-h>=0&&d-g>=0)return Zc.subVectors(r,s),o=(f-h)/(f-h+(d-g)),t.copy(s).addScaledVector(Zc,o);let p=1/(m+b+u);return a=b*p,o=u*p,t.copy(n).addScaledVector(ns,a).addScaledVector(is,o)}equals(e){return e.a.equals(this.a)&&e.b.equals(this.b)&&e.c.equals(this.c)}},Yn=class{constructor(e=new U(1/0,1/0,1/0),t=new U(-1/0,-1/0,-1/0)){this.isBox3=!0,this.min=e,this.max=t}set(e,t){return this.min.copy(e),this.max.copy(t),this}setFromArray(e){this.makeEmpty();for(let t=0,n=e.length;t<n;t+=3)this.expandByPoint(Un.fromArray(e,t));return this}setFromBufferAttribute(e){this.makeEmpty();for(let t=0,n=e.count;t<n;t++)this.expandByPoint(Un.fromBufferAttribute(e,t));return this}setFromPoints(e){this.makeEmpty();for(let t=0,n=e.length;t<n;t++)this.expandByPoint(e[t]);return this}setFromCenterAndSize(e,t){let n=Un.copy(t).multiplyScalar(.5);return this.min.copy(e).sub(n),this.max.copy(e).add(n),this}setFromObject(e,t=!1){return this.makeEmpty(),this.expandByObject(e,t)}clone(){return new this.constructor().copy(this)}copy(e){return this.min.copy(e.min),this.max.copy(e.max),this}makeEmpty(){return this.min.x=this.min.y=this.min.z=1/0,this.max.x=this.max.y=this.max.z=-1/0,this}isEmpty(){return this.max.x<this.min.x||this.max.y<this.min.y||this.max.z<this.min.z}getCenter(e){return this.isEmpty()?e.set(0,0,0):e.addVectors(this.min,this.max).multiplyScalar(.5)}getSize(e){return this.isEmpty()?e.set(0,0,0):e.subVectors(this.max,this.min)}expandByPoint(e){return this.min.min(e),this.max.max(e),this}expandByVector(e){return this.min.sub(e),this.max.add(e),this}expandByScalar(e){return this.min.addScalar(-e),this.max.addScalar(e),this}expandByObject(e,t=!1){e.updateWorldMatrix(!1,!1);let n=e.geometry;if(n!==void 0){let r=n.getAttribute("position");if(t===!0&&r!==void 0&&e.isInstancedMesh!==!0)for(let a=0,o=r.count;a<o;a++)e.isMesh===!0?e.getVertexPosition(a,Un):Un.fromBufferAttribute(r,a),Un.applyMatrix4(e.matrixWorld),this.expandByPoint(Un);else e.boundingBox!==void 0?(e.boundingBox===null&&e.computeBoundingBox(),sa.copy(e.boundingBox)):(n.boundingBox===null&&n.computeBoundingBox(),sa.copy(n.boundingBox)),sa.applyMatrix4(e.matrixWorld),this.union(sa)}let s=e.children;for(let r=0,a=s.length;r<a;r++)this.expandByObject(s[r],t);return this}containsPoint(e){return e.x>=this.min.x&&e.x<=this.max.x&&e.y>=this.min.y&&e.y<=this.max.y&&e.z>=this.min.z&&e.z<=this.max.z}containsBox(e){return this.min.x<=e.min.x&&e.max.x<=this.max.x&&this.min.y<=e.min.y&&e.max.y<=this.max.y&&this.min.z<=e.min.z&&e.max.z<=this.max.z}getParameter(e,t){return t.set((e.x-this.min.x)/(this.max.x-this.min.x),(e.y-this.min.y)/(this.max.y-this.min.y),(e.z-this.min.z)/(this.max.z-this.min.z))}intersectsBox(e){return e.max.x>=this.min.x&&e.min.x<=this.max.x&&e.max.y>=this.min.y&&e.min.y<=this.max.y&&e.max.z>=this.min.z&&e.min.z<=this.max.z}intersectsSphere(e){return this.clampPoint(e.center,Un),Un.distanceToSquared(e.center)<=e.radius*e.radius}intersectsPlane(e){let t,n;return e.normal.x>0?(t=e.normal.x*this.min.x,n=e.normal.x*this.max.x):(t=e.normal.x*this.max.x,n=e.normal.x*this.min.x),e.normal.y>0?(t+=e.normal.y*this.min.y,n+=e.normal.y*this.max.y):(t+=e.normal.y*this.max.y,n+=e.normal.y*this.min.y),e.normal.z>0?(t+=e.normal.z*this.min.z,n+=e.normal.z*this.max.z):(t+=e.normal.z*this.max.z,n+=e.normal.z*this.min.z),t<=-e.constant&&n>=-e.constant}intersectsTriangle(e){if(this.isEmpty())return!1;this.getCenter(Xs),ra.subVectors(this.max,Xs),ss.subVectors(e.a,Xs),rs.subVectors(e.b,Xs),as.subVectors(e.c,Xs),mi.subVectors(rs,ss),gi.subVectors(as,rs),Ni.subVectors(ss,as);let t=[0,-mi.z,mi.y,0,-gi.z,gi.y,0,-Ni.z,Ni.y,mi.z,0,-mi.x,gi.z,0,-gi.x,Ni.z,0,-Ni.x,-mi.y,mi.x,0,-gi.y,gi.x,0,-Ni.y,Ni.x,0];return!Cl(t,ss,rs,as,ra)||(t=[1,0,0,0,1,0,0,0,1],!Cl(t,ss,rs,as,ra))?!1:(aa.crossVectors(mi,gi),t=[aa.x,aa.y,aa.z],Cl(t,ss,rs,as,ra))}clampPoint(e,t){return t.copy(e).clamp(this.min,this.max)}distanceToPoint(e){return this.clampPoint(e,Un).distanceTo(e)}getBoundingSphere(e){return this.isEmpty()?e.makeEmpty():(this.getCenter(e.center),e.radius=this.getSize(Un).length()*.5),e}intersect(e){return this.min.max(e.min),this.max.min(e.max),this.isEmpty()&&this.makeEmpty(),this}union(e){return this.min.min(e.min),this.max.max(e.max),this}applyMatrix4(e){return this.isEmpty()?this:(ii[0].set(this.min.x,this.min.y,this.min.z).applyMatrix4(e),ii[1].set(this.min.x,this.min.y,this.max.z).applyMatrix4(e),ii[2].set(this.min.x,this.max.y,this.min.z).applyMatrix4(e),ii[3].set(this.min.x,this.max.y,this.max.z).applyMatrix4(e),ii[4].set(this.max.x,this.min.y,this.min.z).applyMatrix4(e),ii[5].set(this.max.x,this.min.y,this.max.z).applyMatrix4(e),ii[6].set(this.max.x,this.max.y,this.min.z).applyMatrix4(e),ii[7].set(this.max.x,this.max.y,this.max.z).applyMatrix4(e),this.setFromPoints(ii),this)}translate(e){return this.min.add(e),this.max.add(e),this}equals(e){return e.min.equals(this.min)&&e.max.equals(this.max)}toJSON(){return{min:this.min.toArray(),max:this.max.toArray()}}fromJSON(e){return this.min.fromArray(e.min),this.max.fromArray(e.max),this}},ii=[new U,new U,new U,new U,new U,new U,new U,new U],Un=new U,sa=new Yn,ss=new U,rs=new U,as=new U,mi=new U,gi=new U,Ni=new U,Xs=new U,ra=new U,aa=new U,Di=new U;function Cl(i,e,t,n,s){for(let r=0,a=i.length-3;r<=a;r+=3){Di.fromArray(i,r);let o=s.x*Math.abs(Di.x)+s.y*Math.abs(Di.y)+s.z*Math.abs(Di.z),l=e.dot(Di),c=t.dot(Di),h=n.dot(Di);if(Math.max(-Math.max(l,c,h),Math.min(l,c,h))>o)return!1}return!0}var Bt=new U,oa=new De,Md=0,Kt=class extends $n{constructor(e,t,n=!1){if(super(),Array.isArray(e))throw new TypeError("THREE.BufferAttribute: array should be a Typed Array.");this.isBufferAttribute=!0,Object.defineProperty(this,"id",{value:Md++}),this.name="",this.array=e,this.itemSize=t,this.count=e!==void 0?e.length/t:0,this.normalized=n,this.usage=Zu,this.updateRanges=[],this.gpuType=Pn,this.version=0}onUploadCallback(){}set needsUpdate(e){e===!0&&this.version++}setUsage(e){return this.usage=e,this}addUpdateRange(e,t){this.updateRanges.push({start:e,count:t})}clearUpdateRanges(){this.updateRanges.length=0}copy(e){return this.name=e.name,this.array=new e.array.constructor(e.array),this.itemSize=e.itemSize,this.count=e.count,this.normalized=e.normalized,this.usage=e.usage,this.gpuType=e.gpuType,this}copyAt(e,t,n){e*=this.itemSize,n*=t.itemSize;for(let s=0,r=this.itemSize;s<r;s++)this.array[e+s]=t.array[n+s];return this}copyArray(e){return this.array.set(e),this}applyMatrix3(e){if(this.itemSize===2)for(let t=0,n=this.count;t<n;t++)oa.fromBufferAttribute(this,t),oa.applyMatrix3(e),this.setXY(t,oa.x,oa.y);else if(this.itemSize===3)for(let t=0,n=this.count;t<n;t++)Bt.fromBufferAttribute(this,t),Bt.applyMatrix3(e),this.setXYZ(t,Bt.x,Bt.y,Bt.z);return this}applyMatrix4(e){for(let t=0,n=this.count;t<n;t++)Bt.fromBufferAttribute(this,t),Bt.applyMatrix4(e),this.setXYZ(t,Bt.x,Bt.y,Bt.z);return this}applyNormalMatrix(e){for(let t=0,n=this.count;t<n;t++)Bt.fromBufferAttribute(this,t),Bt.applyNormalMatrix(e),this.setXYZ(t,Bt.x,Bt.y,Bt.z);return this}transformDirection(e){for(let t=0,n=this.count;t<n;t++)Bt.fromBufferAttribute(this,t),Bt.transformDirection(e),this.setXYZ(t,Bt.x,Bt.y,Bt.z);return this}set(e,t=0){return this.array.set(e,t),this}getComponent(e,t){let n=this.array[e*this.itemSize+t];return this.normalized&&(n=ds(n,this.array)),n}setComponent(e,t,n){return this.normalized&&(n=ln(n,this.array)),this.array[e*this.itemSize+t]=n,this}getX(e){let t=this.array[e*this.itemSize];return this.normalized&&(t=ds(t,this.array)),t}setX(e,t){return this.normalized&&(t=ln(t,this.array)),this.array[e*this.itemSize]=t,this}getY(e){let t=this.array[e*this.itemSize+1];return this.normalized&&(t=ds(t,this.array)),t}setY(e,t){return this.normalized&&(t=ln(t,this.array)),this.array[e*this.itemSize+1]=t,this}getZ(e){let t=this.array[e*this.itemSize+2];return this.normalized&&(t=ds(t,this.array)),t}setZ(e,t){return this.normalized&&(t=ln(t,this.array)),this.array[e*this.itemSize+2]=t,this}getW(e){let t=this.array[e*this.itemSize+3];return this.normalized&&(t=ds(t,this.array)),t}setW(e,t){return this.normalized&&(t=ln(t,this.array)),this.array[e*this.itemSize+3]=t,this}setXY(e,t,n){return e*=this.itemSize,this.normalized&&(t=ln(t,this.array),n=ln(n,this.array)),this.array[e+0]=t,this.array[e+1]=n,this}setXYZ(e,t,n,s){return e*=this.itemSize,this.normalized&&(t=ln(t,this.array),n=ln(n,this.array),s=ln(s,this.array)),this.array[e+0]=t,this.array[e+1]=n,this.array[e+2]=s,this}setXYZW(e,t,n,s,r){return e*=this.itemSize,this.normalized&&(t=ln(t,this.array),n=ln(n,this.array),s=ln(s,this.array),r=ln(r,this.array)),this.array[e+0]=t,this.array[e+1]=n,this.array[e+2]=s,this.array[e+3]=r,this}onUpload(e){return this.onUploadCallback=e,this}clone(){return new this.constructor(this.array,this.itemSize).copy(this)}toJSON(){let e={itemSize:this.itemSize,type:this.array.constructor.name,array:Array.from(this.array),normalized:this.normalized};return e.name=this.name,e.usage=this.usage,e.gpuType=this.gpuType,e}dispose(){this.dispatchEvent({type:"dispose"})}};var lr=class extends Kt{constructor(e,t,n){super(new Uint16Array(e),t,n)}};var cr=class extends Kt{constructor(e,t,n){super(new Uint32Array(e),t,n)}};var yt=class extends Kt{constructor(e,t,n){super(new Float32Array(e),t,n)}},Sd=new Yn,$s=new U,Rl=new U,Zn=class{constructor(e=new U,t=-1){this.isSphere=!0,this.center=e,this.radius=t}set(e,t){return this.center.copy(e),this.radius=t,this}setFromPoints(e,t){let n=this.center;t!==void 0?n.copy(t):Sd.setFromPoints(e).getCenter(n);let s=0;for(let r=0,a=e.length;r<a;r++)s=Math.max(s,n.distanceToSquared(e[r]));return this.radius=Math.sqrt(s),this}copy(e){return this.center.copy(e.center),this.radius=e.radius,this}isEmpty(){return this.radius<0}makeEmpty(){return this.center.set(0,0,0),this.radius=-1,this}containsPoint(e){return e.distanceToSquared(this.center)<=this.radius*this.radius}distanceToPoint(e){return e.distanceTo(this.center)-this.radius}intersectsSphere(e){let t=this.radius+e.radius;return e.center.distanceToSquared(this.center)<=t*t}intersectsBox(e){return e.intersectsSphere(this)}intersectsPlane(e){return Math.abs(e.distanceToPoint(this.center))<=this.radius}clampPoint(e,t){let n=this.center.distanceToSquared(e);return t.copy(e),n>this.radius*this.radius&&(t.sub(this.center).normalize(),t.multiplyScalar(this.radius).add(this.center)),t}getBoundingBox(e){return this.isEmpty()?(e.makeEmpty(),e):(e.set(this.center,this.center),e.expandByScalar(this.radius),e)}applyMatrix4(e){return this.center.applyMatrix4(e),this.radius=this.radius*e.getMaxScaleOnAxis(),this}translate(e){return this.center.add(e),this}expandByPoint(e){if(this.isEmpty())return this.center.copy(e),this.radius=0,this;$s.subVectors(e,this.center);let t=$s.lengthSq();if(t>this.radius*this.radius){let n=Math.sqrt(t),s=(n-this.radius)*.5;this.center.addScaledVector($s,s/n),this.radius+=s}return this}union(e){return e.isEmpty()?this:this.isEmpty()?(this.copy(e),this):(this.center.equals(e.center)===!0?this.radius=Math.max(this.radius,e.radius):(Rl.subVectors(e.center,this.center).setLength(e.radius),this.expandByPoint($s.copy(e.center).add(Rl)),this.expandByPoint($s.copy(e.center).sub(Rl))),this)}equals(e){return e.center.equals(this.center)&&e.radius===this.radius}clone(){return new this.constructor().copy(this)}toJSON(){return{radius:this.radius,center:this.center.toArray()}}fromJSON(e){return this.radius=e.radius,this.center.fromArray(e.center),this}},Td=0,En=new xt,Pl=new Ht,os=new U,bn=new Yn,Ys=new Yn,$t=new U,Rt=class i extends $n{constructor(){super(),this.isBufferGeometry=!0,Object.defineProperty(this,"id",{value:Td++}),this.uuid=Ls(),this.name="",this.type="BufferGeometry",this.index=null,this.indirect=null,this.indirectOffset=0,this.attributes={},this.morphAttributes={},this.morphTargetsRelative=!1,this.groups=[],this.boundingBox=null,this.boundingSphere=null,this.drawRange={start:0,count:1/0},this.userData={},this._transformed=!1}getIndex(){return this.index}setIndex(e){return Array.isArray(e)?this.index=new(Yh(e)?cr:lr)(e,1):this.index=e,this}setIndirect(e,t=0){return this.indirect=e,this.indirectOffset=t,this}getIndirect(){return this.indirect}getAttribute(e){return this.attributes[e]}setAttribute(e,t){return this.attributes[e]=t,this}deleteAttribute(e){return delete this.attributes[e],this}hasAttribute(e){return this.attributes[e]!==void 0}addGroup(e,t,n=0){this.groups.push({start:e,count:t,materialIndex:n})}clearGroups(){this.groups=[]}setDrawRange(e,t){this.drawRange.start=e,this.drawRange.count=t}applyMatrix4(e){let t=this.attributes.position;t!==void 0&&(t.applyMatrix4(e),t.needsUpdate=!0);let n=this.attributes.normal;if(n!==void 0){let r=new st().getNormalMatrix(e);n.applyNormalMatrix(r),n.needsUpdate=!0}let s=this.attributes.tangent;return s!==void 0&&(s.transformDirection(e),s.needsUpdate=!0),this.boundingBox!==null&&this.computeBoundingBox(),this.boundingSphere!==null&&this.computeBoundingSphere(),this._transformed=!0,this}applyQuaternion(e){return En.makeRotationFromQuaternion(e),this.applyMatrix4(En),this}rotateX(e){return En.makeRotationX(e),this.applyMatrix4(En),this}rotateY(e){return En.makeRotationY(e),this.applyMatrix4(En),this}rotateZ(e){return En.makeRotationZ(e),this.applyMatrix4(En),this}translate(e,t,n){return En.makeTranslation(e,t,n),this.applyMatrix4(En),this}scale(e,t,n){return En.makeScale(e,t,n),this.applyMatrix4(En),this}lookAt(e){return Pl.lookAt(e),Pl.updateMatrix(),this.applyMatrix4(Pl.matrix),this}center(){return this.computeBoundingBox(),this.boundingBox.getCenter(os).negate(),this.translate(os.x,os.y,os.z),this}setFromPoints(e){let t=this.getAttribute("position");if(t===void 0){let n=[];for(let s=0,r=e.length;s<r;s++){let a=e[s];n.push(a.x,a.y,a.z||0)}this.setAttribute("position",new yt(n,3))}else{let n=Math.min(e.length,t.count);for(let s=0;s<n;s++){let r=e[s];t.setXYZ(s,r.x,r.y,r.z||0)}e.length>t.count&&je("BufferGeometry: Buffer size too small for points data. Use .dispose() and create a new geometry."),t.needsUpdate=!0}return this}computeBoundingBox(){this.boundingBox===null&&(this.boundingBox=new Yn);let e=this.attributes.position,t=this.morphAttributes.position;if(e&&e.isGLBufferAttribute){nt("BufferGeometry.computeBoundingBox(): GLBufferAttribute requires a manual bounding box.",this),this.boundingBox.set(new U(-1/0,-1/0,-1/0),new U(1/0,1/0,1/0));return}if(e!==void 0){if(this.boundingBox.setFromBufferAttribute(e),t)for(let n=0,s=t.length;n<s;n++){let r=t[n];bn.setFromBufferAttribute(r),this.morphTargetsRelative?($t.addVectors(this.boundingBox.min,bn.min),this.boundingBox.expandByPoint($t),$t.addVectors(this.boundingBox.max,bn.max),this.boundingBox.expandByPoint($t)):(this.boundingBox.expandByPoint(bn.min),this.boundingBox.expandByPoint(bn.max))}}else this.boundingBox.makeEmpty();(isNaN(this.boundingBox.min.x)||isNaN(this.boundingBox.min.y)||isNaN(this.boundingBox.min.z))&&nt('BufferGeometry.computeBoundingBox(): Computed min/max have NaN values. The "position" attribute is likely to have NaN values.',this)}computeBoundingSphere(){this.boundingSphere===null&&(this.boundingSphere=new Zn);let e=this.attributes.position,t=this.morphAttributes.position;if(e&&e.isGLBufferAttribute){nt("BufferGeometry.computeBoundingSphere(): GLBufferAttribute requires a manual bounding sphere.",this),this.boundingSphere.set(new U,1/0);return}if(e){let n=this.boundingSphere.center;if(bn.setFromBufferAttribute(e),t)for(let r=0,a=t.length;r<a;r++){let o=t[r];Ys.setFromBufferAttribute(o),this.morphTargetsRelative?($t.addVectors(bn.min,Ys.min),bn.expandByPoint($t),$t.addVectors(bn.max,Ys.max),bn.expandByPoint($t)):(bn.expandByPoint(Ys.min),bn.expandByPoint(Ys.max))}bn.getCenter(n);let s=0;for(let r=0,a=e.count;r<a;r++)$t.fromBufferAttribute(e,r),s=Math.max(s,n.distanceToSquared($t));if(t)for(let r=0,a=t.length;r<a;r++){let o=t[r],l=this.morphTargetsRelative;for(let c=0,h=o.count;c<h;c++)$t.fromBufferAttribute(o,c),l&&(os.fromBufferAttribute(e,c),$t.add(os)),s=Math.max(s,n.distanceToSquared($t))}this.boundingSphere.radius=Math.sqrt(s),isNaN(this.boundingSphere.radius)&&nt('BufferGeometry.computeBoundingSphere(): Computed radius is NaN. The "position" attribute is likely to have NaN values.',this)}}computeTangents(){let e=this.index,t=this.attributes;if(e===null||t.position===void 0||t.normal===void 0||t.uv===void 0){nt("BufferGeometry: .computeTangents() failed. Missing required attributes (index, position, normal or uv)");return}let n=t.position,s=t.normal,r=t.uv,a=this.getAttribute("tangent");(a===void 0||a.count!==n.count)&&(a=new Kt(new Float32Array(4*n.count),4),this.setAttribute("tangent",a));let o=[],l=[];for(let x=0;x<n.count;x++)o[x]=new U,l[x]=new U;let c=new U,h=new U,f=new U,u=new De,d=new De,g=new De,b=new U,m=new U;function p(x,A,D){c.fromBufferAttribute(n,x),h.fromBufferAttribute(n,A),f.fromBufferAttribute(n,D),u.fromBufferAttribute(r,x),d.fromBufferAttribute(r,A),g.fromBufferAttribute(r,D),h.sub(c),f.sub(c),d.sub(u),g.sub(u);let k=1/(d.x*g.y-g.x*d.y);isFinite(k)&&(b.copy(h).multiplyScalar(g.y).addScaledVector(f,-d.y).multiplyScalar(k),m.copy(f).multiplyScalar(d.x).addScaledVector(h,-g.x).multiplyScalar(k),o[x].add(b),o[A].add(b),o[D].add(b),l[x].add(m),l[A].add(m),l[D].add(m))}let E=this.groups;E.length===0&&(E=[{start:0,count:e.count}]);for(let x=0,A=E.length;x<A;++x){let D=E[x],k=D.start,G=D.count;for(let Y=k,F=k+G;Y<F;Y+=3)p(e.getX(Y+0),e.getX(Y+1),e.getX(Y+2))}let C=new U,y=new U,w=new U,T=new U;function I(x){w.fromBufferAttribute(s,x),T.copy(w);let A=o[x];C.copy(A),C.sub(w.multiplyScalar(w.dot(A))).normalize(),y.crossVectors(T,A);let k=y.dot(l[x])<0?-1:1;a.setXYZW(x,C.x,C.y,C.z,k)}for(let x=0,A=E.length;x<A;++x){let D=E[x],k=D.start,G=D.count;for(let Y=k,F=k+G;Y<F;Y+=3)I(e.getX(Y+0)),I(e.getX(Y+1)),I(e.getX(Y+2))}this._transformed=!0}computeVertexNormals(){let e=this.index,t=this.getAttribute("position");if(t!==void 0){let n=this.getAttribute("normal");if(n===void 0||n.count!==t.count)n=new Kt(new Float32Array(t.count*3),3),this.setAttribute("normal",n);else for(let u=0,d=n.count;u<d;u++)n.setXYZ(u,0,0,0);let s=new U,r=new U,a=new U,o=new U,l=new U,c=new U,h=new U,f=new U;if(e)for(let u=0,d=e.count;u<d;u+=3){let g=e.getX(u+0),b=e.getX(u+1),m=e.getX(u+2);s.fromBufferAttribute(t,g),r.fromBufferAttribute(t,b),a.fromBufferAttribute(t,m),h.subVectors(a,r),f.subVectors(s,r),h.cross(f),o.fromBufferAttribute(n,g),l.fromBufferAttribute(n,b),c.fromBufferAttribute(n,m),o.add(h),l.add(h),c.add(h),n.setXYZ(g,o.x,o.y,o.z),n.setXYZ(b,l.x,l.y,l.z),n.setXYZ(m,c.x,c.y,c.z)}else for(let u=0,d=t.count;u<d;u+=3)s.fromBufferAttribute(t,u+0),r.fromBufferAttribute(t,u+1),a.fromBufferAttribute(t,u+2),h.subVectors(a,r),f.subVectors(s,r),h.cross(f),n.setXYZ(u+0,h.x,h.y,h.z),n.setXYZ(u+1,h.x,h.y,h.z),n.setXYZ(u+2,h.x,h.y,h.z);this.normalizeNormals(),n.needsUpdate=!0}}normalizeNormals(){let e=this.attributes.normal;for(let t=0,n=e.count;t<n;t++)$t.fromBufferAttribute(e,t),$t.normalize(),e.setXYZ(t,$t.x,$t.y,$t.z)}toNonIndexed(){function e(o,l){let c=o.array,h=o.itemSize,f=o.normalized,u=new c.constructor(l.length*h),d=0,g=0;for(let b=0,m=l.length;b<m;b++){o.isInterleavedBufferAttribute?d=l[b]*o.data.stride+o.offset:d=l[b]*h;for(let p=0;p<h;p++)u[g++]=c[d++]}return new Kt(u,h,f)}if(this.index===null)return je("BufferGeometry.toNonIndexed(): BufferGeometry is already non-indexed."),this;let t=new i,n=this.index.array,s=this.attributes;for(let o in s){let l=s[o],c=e(l,n);t.setAttribute(o,c)}let r=this.morphAttributes;for(let o in r){let l=[],c=r[o];for(let h=0,f=c.length;h<f;h++){let u=c[h],d=e(u,n);l.push(d)}t.morphAttributes[o]=l}t.morphTargetsRelative=this.morphTargetsRelative;let a=this.groups;for(let o=0,l=a.length;o<l;o++){let c=a[o];t.addGroup(c.start,c.count,c.materialIndex)}return t}toJSON(){let e={metadata:{version:4.7,type:"BufferGeometry",generator:"BufferGeometry.toJSON"}};if(e.uuid=this.uuid,e.type=this.parameters!==void 0&&this._transformed===!0?"BufferGeometry":this.type,e.name=this.name,Object.keys(this.userData).length>0&&(e.userData=this.userData),this.parameters!==void 0&&this._transformed!==!0){let l=this.parameters;for(let c in l)l[c]!==void 0&&(e[c]=l[c]);return e}e.data={attributes:{}};let t=this.index;t!==null&&(e.data.index={type:t.array.constructor.name,array:Array.prototype.slice.call(t.array)});let n=this.attributes;for(let l in n){let c=n[l];e.data.attributes[l]=c.toJSON(e.data)}let s={},r=!1;for(let l in this.morphAttributes){let c=this.morphAttributes[l],h=[];for(let f=0,u=c.length;f<u;f++){let d=c[f];h.push(d.toJSON(e.data))}h.length>0&&(s[l]=h,r=!0)}r&&(e.data.morphAttributes=s,e.data.morphTargetsRelative=this.morphTargetsRelative);let a=this.groups;a.length>0&&(e.data.groups=JSON.parse(JSON.stringify(a)));let o=this.boundingSphere;return o!==null&&(e.data.boundingSphere=o.toJSON()),e}clone(){return new this.constructor().copy(this)}copy(e){this.index=null,this.attributes={},this.morphAttributes={},this.groups=[],this.boundingBox=null,this.boundingSphere=null;let t={};this.name=e.name;let n=e.index;n!==null&&this.setIndex(n.clone());let s=e.attributes;for(let c in s){let h=s[c];this.setAttribute(c,h.clone(t))}let r=e.morphAttributes;for(let c in r){let h=[],f=r[c];for(let u=0,d=f.length;u<d;u++)h.push(f[u].clone(t));this.morphAttributes[c]=h}this.morphTargetsRelative=e.morphTargetsRelative;let a=e.groups;for(let c=0,h=a.length;c<h;c++){let f=a[c];this.addGroup(f.start,f.count,f.materialIndex)}let o=e.boundingBox;o!==null&&(this.boundingBox=o.clone());let l=e.boundingSphere;return l!==null&&(this.boundingSphere=l.clone()),this.drawRange.start=e.drawRange.start,this.drawRange.count=e.drawRange.count,this.userData=e.userData,this._transformed=e._transformed,this}dispose(){this.dispatchEvent({type:"dispose"})}};var Il=new U,Ed=new U,wd=new st,Fn=class{constructor(e=new U(1,0,0),t=0){this.isPlane=!0,this.normal=e,this.constant=t}set(e,t){return this.normal.copy(e),this.constant=t,this}setComponents(e,t,n,s){return this.normal.set(e,t,n),this.constant=s,this}setFromNormalAndCoplanarPoint(e,t){return this.normal.copy(e),this.constant=-t.dot(this.normal),this}setFromCoplanarPoints(e,t,n){let s=Il.subVectors(n,t).cross(Ed.subVectors(e,t)).normalize();return this.setFromNormalAndCoplanarPoint(s,e),this}copy(e){return this.normal.copy(e.normal),this.constant=e.constant,this}normalize(){let e=1/this.normal.length();return this.normal.multiplyScalar(e),this.constant*=e,this}negate(){return this.constant*=-1,this.normal.negate(),this}distanceToPoint(e){return this.normal.dot(e)+this.constant}distanceToSphere(e){return this.distanceToPoint(e.center)-e.radius}projectPoint(e,t){return t.copy(e).addScaledVector(this.normal,-this.distanceToPoint(e))}intersectLine(e,t,n=!0){let s=e.delta(Il),r=this.normal.dot(s);if(r===0)return this.distanceToPoint(e.start)===0?t.copy(e.start):null;let a=-(e.start.dot(this.normal)+this.constant)/r;return n===!0&&(a<0||a>1)?null:t.copy(e.start).addScaledVector(s,a)}intersectsLine(e){let t=this.distanceToPoint(e.start),n=this.distanceToPoint(e.end);return t<0&&n>0||n<0&&t>0}intersectsBox(e){return e.intersectsPlane(this)}intersectsSphere(e){return e.intersectsPlane(this)}coplanarPoint(e){return e.copy(this.normal).multiplyScalar(-this.constant)}applyMatrix4(e,t){let n=t||wd.getNormalMatrix(e),s=this.coplanarPoint(Il).applyMatrix4(e),r=this.normal.applyMatrix3(n).normalize();return this.constant=-s.dot(r),this}translate(e){return this.constant-=e.dot(this.normal),this}equals(e){return e.normal.equals(this.normal)&&e.constant===this.constant}clone(){return new this.constructor().copy(this)}toJSON(){return{normal:this.normal.toArray(),constant:this.constant}}fromJSON(e){return this.normal.fromArray(e.normal),this.constant=e.constant,this}},Ad=0,On=class extends $n{constructor(){super(),this.isMaterial=!0,Object.defineProperty(this,"id",{value:Ad++}),this.uuid=Ls(),this.name="",this.type="Material",this.blending=Rs,this.side=Ti,this.vertexColors=!1,this.opacity=1,this.transparent=!1,this.alphaHash=!1,this.blendSrc=Ql,this.blendDst=ec,this.blendEquation=Wi,this.blendSrcAlpha=null,this.blendDstAlpha=null,this.blendEquationAlpha=null,this.blendColor=new Qe(0,0,0),this.blendAlpha=0,this.depthFunc=ps,this.depthTest=!0,this.depthWrite=!0,this.stencilWriteMask=255,this.stencilFunc=Hu,this.stencilRef=0,this.stencilFuncMask=255,this.stencilFail=wa,this.stencilZFail=wa,this.stencilZPass=wa,this.stencilWrite=!1,this.clippingPlanes=null,this.clipIntersection=!1,this.clipShadows=!1,this.shadowSide=null,this.colorWrite=!0,this.precision=null,this.polygonOffset=!1,this.polygonOffsetFactor=0,this.polygonOffsetUnits=0,this.dithering=!1,this.alphaToCoverage=!1,this.premultipliedAlpha=!1,this.forceSinglePass=!1,this.allowOverride=!0,this.visible=!0,this.toneMapped=!0,this.userData={},this.version=0,this._alphaTest=0}get alphaTest(){return this._alphaTest}set alphaTest(e){this._alphaTest>0!=e>0&&this.version++,this._alphaTest=e}onBeforeRender(){}onBeforeCompile(){}customProgramCacheKey(){return this.onBeforeCompile.toString()}setValues(e){if(e!==void 0)for(let t in e){let n=e[t];if(n===void 0){je(`Material: parameter '${t}' has value of undefined.`);continue}let s=this[t];if(s===void 0){je(`Material: '${t}' is not a property of THREE.${this.type}.`);continue}s&&s.isColor?s.set(n):s&&s.isVector2&&n&&n.isVector2||s&&s.isEuler&&n&&n.isEuler||s&&s.isVector3&&n&&n.isVector3?s.copy(n):this[t]=n}}toJSON(e){let t=e===void 0||typeof e=="string";t&&(e={textures:{},images:{}});let n={metadata:{version:4.7,type:"Material",generator:"Material.toJSON"}};n.uuid=this.uuid,n.type=this.type,n.blending=this.blending,n.side=this.side,n.shadowSide=this.shadowSide,n.vertexColors=this.vertexColors,n.opacity=this.opacity,n.transparent=this.transparent,n.blendSrc=this.blendSrc,n.blendDst=this.blendDst,n.blendEquation=this.blendEquation,n.blendSrcAlpha=this.blendSrcAlpha,n.blendDstAlpha=this.blendDstAlpha,n.blendEquationAlpha=this.blendEquationAlpha,n.blendColor=this.blendColor.getHex(),n.blendAlpha=this.blendAlpha,n.depthFunc=this.depthFunc,n.depthTest=this.depthTest,n.depthWrite=this.depthWrite,n.colorWrite=this.colorWrite,n.clipIntersection=this.clipIntersection,n.clipShadows=this.clipShadows,n.stencilWriteMask=this.stencilWriteMask,n.stencilFunc=this.stencilFunc,n.stencilRef=this.stencilRef,n.stencilFuncMask=this.stencilFuncMask,n.stencilFail=this.stencilFail,n.stencilZFail=this.stencilZFail,n.stencilZPass=this.stencilZPass,n.stencilWrite=this.stencilWrite,n.polygonOffset=this.polygonOffset,n.polygonOffsetFactor=this.polygonOffsetFactor,n.polygonOffsetUnits=this.polygonOffsetUnits,n.dithering=this.dithering,n.alphaTest=this.alphaTest,n.alphaHash=this.alphaHash,n.alphaToCoverage=this.alphaToCoverage,n.premultipliedAlpha=this.premultipliedAlpha,n.forceSinglePass=this.forceSinglePass,n.allowOverride=this.allowOverride,n.visible=this.visible,n.toneMapped=this.toneMapped,n.name=this.name,this.color&&this.color.isColor&&(n.color=this.color.getHex()),this.roughness!==void 0&&(n.roughness=this.roughness),this.metalness!==void 0&&(n.metalness=this.metalness),this.sheen!==void 0&&(n.sheen=this.sheen),this.sheenColor&&this.sheenColor.isColor&&(n.sheenColor=this.sheenColor.getHex()),this.sheenRoughness!==void 0&&(n.sheenRoughness=this.sheenRoughness),this.emissive&&this.emissive.isColor&&(n.emissive=this.emissive.getHex()),this.emissiveIntensity!==void 0&&(n.emissiveIntensity=this.emissiveIntensity),this.specular&&this.specular.isColor&&(n.specular=this.specular.getHex()),this.specularIntensity!==void 0&&(n.specularIntensity=this.specularIntensity),this.specularColor&&this.specularColor.isColor&&(n.specularColor=this.specularColor.getHex()),this.shininess!==void 0&&(n.shininess=this.shininess),this.clearcoat!==void 0&&(n.clearcoat=this.clearcoat),this.clearcoatRoughness!==void 0&&(n.clearcoatRoughness=this.clearcoatRoughness),this.clearcoatMap&&this.clearcoatMap.isTexture&&(n.clearcoatMap=this.clearcoatMap.toJSON(e).uuid),this.clearcoatRoughnessMap&&this.clearcoatRoughnessMap.isTexture&&(n.clearcoatRoughnessMap=this.clearcoatRoughnessMap.toJSON(e).uuid),this.clearcoatNormalMap&&this.clearcoatNormalMap.isTexture&&(n.clearcoatNormalMap=this.clearcoatNormalMap.toJSON(e).uuid,n.clearcoatNormalScale=this.clearcoatNormalScale.toArray()),this.sheenColorMap&&this.sheenColorMap.isTexture&&(n.sheenColorMap=this.sheenColorMap.toJSON(e).uuid),this.sheenRoughnessMap&&this.sheenRoughnessMap.isTexture&&(n.sheenRoughnessMap=this.sheenRoughnessMap.toJSON(e).uuid),this.dispersion!==void 0&&(n.dispersion=this.dispersion),this.retroreflectivity!==void 0&&(n.retroreflectivity=this.retroreflectivity),this.iridescence!==void 0&&(n.iridescence=this.iridescence),this.iridescenceIOR!==void 0&&(n.iridescenceIOR=this.iridescenceIOR),this.iridescenceThicknessRange!==void 0&&(n.iridescenceThicknessRange=this.iridescenceThicknessRange),this.iridescenceMap&&this.iridescenceMap.isTexture&&(n.iridescenceMap=this.iridescenceMap.toJSON(e).uuid),this.iridescenceThicknessMap&&this.iridescenceThicknessMap.isTexture&&(n.iridescenceThicknessMap=this.iridescenceThicknessMap.toJSON(e).uuid),this.anisotropy!==void 0&&(n.anisotropy=this.anisotropy),this.anisotropyRotation!==void 0&&(n.anisotropyRotation=this.anisotropyRotation),this.anisotropyMap&&this.anisotropyMap.isTexture&&(n.anisotropyMap=this.anisotropyMap.toJSON(e).uuid),this.map&&this.map.isTexture&&(n.map=this.map.toJSON(e).uuid),this.matcap&&this.matcap.isTexture&&(n.matcap=this.matcap.toJSON(e).uuid),this.alphaMap&&this.alphaMap.isTexture&&(n.alphaMap=this.alphaMap.toJSON(e).uuid),this.lightMap&&this.lightMap.isTexture&&(n.lightMap=this.lightMap.toJSON(e).uuid,n.lightMapIntensity=this.lightMapIntensity),this.aoMap&&this.aoMap.isTexture&&(n.aoMap=this.aoMap.toJSON(e).uuid,n.aoMapIntensity=this.aoMapIntensity),this.bumpMap&&this.bumpMap.isTexture&&(n.bumpMap=this.bumpMap.toJSON(e).uuid,n.bumpScale=this.bumpScale),this.normalMap&&this.normalMap.isTexture&&(n.normalMap=this.normalMap.toJSON(e).uuid,n.normalMapType=this.normalMapType,n.normalScale=this.normalScale.toArray()),this.displacementMap&&this.displacementMap.isTexture&&(n.displacementMap=this.displacementMap.toJSON(e).uuid,n.displacementScale=this.displacementScale,n.displacementBias=this.displacementBias),this.roughnessMap&&this.roughnessMap.isTexture&&(n.roughnessMap=this.roughnessMap.toJSON(e).uuid),this.metalnessMap&&this.metalnessMap.isTexture&&(n.metalnessMap=this.metalnessMap.toJSON(e).uuid),this.emissiveMap&&this.emissiveMap.isTexture&&(n.emissiveMap=this.emissiveMap.toJSON(e).uuid),this.specularMap&&this.specularMap.isTexture&&(n.specularMap=this.specularMap.toJSON(e).uuid),this.specularIntensityMap&&this.specularIntensityMap.isTexture&&(n.specularIntensityMap=this.specularIntensityMap.toJSON(e).uuid),this.specularColorMap&&this.specularColorMap.isTexture&&(n.specularColorMap=this.specularColorMap.toJSON(e).uuid),this.envMap&&this.envMap.isTexture&&(n.envMap=this.envMap.toJSON(e).uuid,this.combine!==void 0&&(n.combine=this.combine)),this.envMapRotation!==void 0&&(n.envMapRotation=this.envMapRotation.toArray()),this.envMapIntensity!==void 0&&(n.envMapIntensity=this.envMapIntensity),this.reflectivity!==void 0&&(n.reflectivity=this.reflectivity),this.refractionRatio!==void 0&&(n.refractionRatio=this.refractionRatio),this.gradientMap&&this.gradientMap.isTexture&&(n.gradientMap=this.gradientMap.toJSON(e).uuid),this.transmission!==void 0&&(n.transmission=this.transmission),this.transmissionMap&&this.transmissionMap.isTexture&&(n.transmissionMap=this.transmissionMap.toJSON(e).uuid),this.thickness!==void 0&&(n.thickness=this.thickness),this.thicknessMap&&this.thicknessMap.isTexture&&(n.thicknessMap=this.thicknessMap.toJSON(e).uuid),this.attenuationDistance!==void 0&&(n.attenuationDistance=this.attenuationDistance),this.attenuationColor!==void 0&&(n.attenuationColor=this.attenuationColor.getHex()),this.size!==void 0&&(n.size=this.size),this.sizeAttenuation!==void 0&&(n.sizeAttenuation=this.sizeAttenuation),Array.isArray(this.clippingPlanes)&&this.clippingPlanes.length>0&&(n.clippingPlanes=this.clippingPlanes.map(r=>r.toJSON())),this.rotation!==void 0&&(n.rotation=this.rotation),this.depthPacking!==void 0&&(n.depthPacking=this.depthPacking),this.linewidth!==void 0&&(n.linewidth=this.linewidth),this.linecap!==void 0&&(n.linecap=this.linecap),this.linejoin!==void 0&&(n.linejoin=this.linejoin),this.dashSize!==void 0&&(n.dashSize=this.dashSize),this.gapSize!==void 0&&(n.gapSize=this.gapSize),this.scale!==void 0&&(n.scale=this.scale),this.wireframe!==void 0&&(n.wireframe=this.wireframe),this.wireframeLinewidth!==void 0&&(n.wireframeLinewidth=this.wireframeLinewidth),this.wireframeLinecap!==void 0&&(n.wireframeLinecap=this.wireframeLinecap),this.wireframeLinejoin!==void 0&&(n.wireframeLinejoin=this.wireframeLinejoin),this.flatShading!==void 0&&(n.flatShading=this.flatShading),this.fog!==void 0&&(n.fog=this.fog),Object.keys(this.userData).length>0&&(n.userData=this.userData);function s(r){let a=[];for(let o in r){let l=r[o];delete l.metadata,a.push(l)}return a}if(t){let r=s(e.textures),a=s(e.images);r.length>0&&(n.textures=r),a.length>0&&(n.images=a)}return n}fromJSON(e,t){if(e.uuid!==void 0&&(this.uuid=e.uuid),e.name!==void 0&&(this.name=e.name),e.color!==void 0&&this.color!==void 0&&this.color.setHex(e.color),e.roughness!==void 0&&(this.roughness=e.roughness),e.metalness!==void 0&&(this.metalness=e.metalness),e.sheen!==void 0&&(this.sheen=e.sheen),e.sheenColor!==void 0&&(this.sheenColor=new Qe().setHex(e.sheenColor)),e.sheenRoughness!==void 0&&(this.sheenRoughness=e.sheenRoughness),e.emissive!==void 0&&this.emissive!==void 0&&this.emissive.setHex(e.emissive),e.specular!==void 0&&this.specular!==void 0&&this.specular.setHex(e.specular),e.specularIntensity!==void 0&&(this.specularIntensity=e.specularIntensity),e.specularColor!==void 0&&this.specularColor!==void 0&&this.specularColor.setHex(e.specularColor),e.shininess!==void 0&&(this.shininess=e.shininess),e.clearcoat!==void 0&&(this.clearcoat=e.clearcoat),e.clearcoatRoughness!==void 0&&(this.clearcoatRoughness=e.clearcoatRoughness),e.dispersion!==void 0&&(this.dispersion=e.dispersion),e.retroreflectivity!==void 0&&(this.retroreflectivity=e.retroreflectivity),e.iridescence!==void 0&&(this.iridescence=e.iridescence),e.iridescenceIOR!==void 0&&(this.iridescenceIOR=e.iridescenceIOR),e.iridescenceThicknessRange!==void 0&&(this.iridescenceThicknessRange=e.iridescenceThicknessRange),e.transmission!==void 0&&(this.transmission=e.transmission),e.thickness!==void 0&&(this.thickness=e.thickness),e.attenuationDistance!==void 0&&(this.attenuationDistance=e.attenuationDistance),e.attenuationColor!==void 0&&this.attenuationColor!==void 0&&this.attenuationColor.setHex(e.attenuationColor),e.anisotropy!==void 0&&(this.anisotropy=e.anisotropy),e.anisotropyRotation!==void 0&&(this.anisotropyRotation=e.anisotropyRotation),e.fog!==void 0&&(this.fog=e.fog),e.flatShading!==void 0&&(this.flatShading=e.flatShading),e.blending!==void 0&&(this.blending=e.blending),e.combine!==void 0&&(this.combine=e.combine),e.side!==void 0&&(this.side=e.side),e.shadowSide!==void 0&&(this.shadowSide=e.shadowSide),e.opacity!==void 0&&(this.opacity=e.opacity),e.transparent!==void 0&&(this.transparent=e.transparent),e.alphaTest!==void 0&&(this.alphaTest=e.alphaTest),e.alphaHash!==void 0&&(this.alphaHash=e.alphaHash),e.depthFunc!==void 0&&(this.depthFunc=e.depthFunc),e.depthTest!==void 0&&(this.depthTest=e.depthTest),e.depthWrite!==void 0&&(this.depthWrite=e.depthWrite),e.colorWrite!==void 0&&(this.colorWrite=e.colorWrite),e.clippingPlanes!==void 0&&(this.clippingPlanes=e.clippingPlanes.map(n=>new Fn().fromJSON(n))),e.clipIntersection!==void 0&&(this.clipIntersection=e.clipIntersection),e.clipShadows!==void 0&&(this.clipShadows=e.clipShadows),e.depthPacking!==void 0&&(this.depthPacking=e.depthPacking),e.blendSrc!==void 0&&(this.blendSrc=e.blendSrc),e.blendDst!==void 0&&(this.blendDst=e.blendDst),e.blendEquation!==void 0&&(this.blendEquation=e.blendEquation),e.blendSrcAlpha!==void 0&&(this.blendSrcAlpha=e.blendSrcAlpha),e.blendDstAlpha!==void 0&&(this.blendDstAlpha=e.blendDstAlpha),e.blendEquationAlpha!==void 0&&(this.blendEquationAlpha=e.blendEquationAlpha),e.blendColor!==void 0&&this.blendColor!==void 0&&this.blendColor.setHex(e.blendColor),e.blendAlpha!==void 0&&(this.blendAlpha=e.blendAlpha),e.stencilWriteMask!==void 0&&(this.stencilWriteMask=e.stencilWriteMask),e.stencilFunc!==void 0&&(this.stencilFunc=e.stencilFunc),e.stencilRef!==void 0&&(this.stencilRef=e.stencilRef),e.stencilFuncMask!==void 0&&(this.stencilFuncMask=e.stencilFuncMask),e.stencilFail!==void 0&&(this.stencilFail=e.stencilFail),e.stencilZFail!==void 0&&(this.stencilZFail=e.stencilZFail),e.stencilZPass!==void 0&&(this.stencilZPass=e.stencilZPass),e.stencilWrite!==void 0&&(this.stencilWrite=e.stencilWrite),e.wireframe!==void 0&&(this.wireframe=e.wireframe),e.wireframeLinewidth!==void 0&&(this.wireframeLinewidth=e.wireframeLinewidth),e.wireframeLinecap!==void 0&&(this.wireframeLinecap=e.wireframeLinecap),e.wireframeLinejoin!==void 0&&(this.wireframeLinejoin=e.wireframeLinejoin),e.rotation!==void 0&&(this.rotation=e.rotation),e.linewidth!==void 0&&(this.linewidth=e.linewidth),e.linecap!==void 0&&(this.linecap=e.linecap),e.linejoin!==void 0&&(this.linejoin=e.linejoin),e.dashSize!==void 0&&(this.dashSize=e.dashSize),e.gapSize!==void 0&&(this.gapSize=e.gapSize),e.scale!==void 0&&(this.scale=e.scale),e.polygonOffset!==void 0&&(this.polygonOffset=e.polygonOffset),e.polygonOffsetFactor!==void 0&&(this.polygonOffsetFactor=e.polygonOffsetFactor),e.polygonOffsetUnits!==void 0&&(this.polygonOffsetUnits=e.polygonOffsetUnits),e.dithering!==void 0&&(this.dithering=e.dithering),e.alphaToCoverage!==void 0&&(this.alphaToCoverage=e.alphaToCoverage),e.premultipliedAlpha!==void 0&&(this.premultipliedAlpha=e.premultipliedAlpha),e.forceSinglePass!==void 0&&(this.forceSinglePass=e.forceSinglePass),e.allowOverride!==void 0&&(this.allowOverride=e.allowOverride),e.visible!==void 0&&(this.visible=e.visible),e.toneMapped!==void 0&&(this.toneMapped=e.toneMapped),e.userData!==void 0&&(this.userData=e.userData),e.vertexColors!==void 0&&(typeof e.vertexColors=="number"?this.vertexColors=e.vertexColors>0:this.vertexColors=e.vertexColors),e.size!==void 0&&(this.size=e.size),e.sizeAttenuation!==void 0&&(this.sizeAttenuation=e.sizeAttenuation),e.map!==void 0&&(this.map=t[e.map]||null),e.matcap!==void 0&&(this.matcap=t[e.matcap]||null),e.alphaMap!==void 0&&(this.alphaMap=t[e.alphaMap]||null),e.bumpMap!==void 0&&(this.bumpMap=t[e.bumpMap]||null),e.bumpScale!==void 0&&(this.bumpScale=e.bumpScale),e.normalMap!==void 0&&(this.normalMap=t[e.normalMap]||null),e.normalMapType!==void 0&&(this.normalMapType=e.normalMapType),e.normalScale!==void 0){let n=e.normalScale;Array.isArray(n)===!1&&(n=[n,n]),this.normalScale=new De().fromArray(n)}return e.displacementMap!==void 0&&(this.displacementMap=t[e.displacementMap]||null),e.displacementScale!==void 0&&(this.displacementScale=e.displacementScale),e.displacementBias!==void 0&&(this.displacementBias=e.displacementBias),e.roughnessMap!==void 0&&(this.roughnessMap=t[e.roughnessMap]||null),e.metalnessMap!==void 0&&(this.metalnessMap=t[e.metalnessMap]||null),e.emissiveMap!==void 0&&(this.emissiveMap=t[e.emissiveMap]||null),e.emissiveIntensity!==void 0&&(this.emissiveIntensity=e.emissiveIntensity),e.specularMap!==void 0&&(this.specularMap=t[e.specularMap]||null),e.specularIntensityMap!==void 0&&(this.specularIntensityMap=t[e.specularIntensityMap]||null),e.specularColorMap!==void 0&&(this.specularColorMap=t[e.specularColorMap]||null),e.envMap!==void 0&&(this.envMap=t[e.envMap]||null),e.envMapRotation!==void 0&&this.envMapRotation.fromArray(e.envMapRotation),e.envMapIntensity!==void 0&&(this.envMapIntensity=e.envMapIntensity),e.reflectivity!==void 0&&(this.reflectivity=e.reflectivity),e.refractionRatio!==void 0&&(this.refractionRatio=e.refractionRatio),e.lightMap!==void 0&&(this.lightMap=t[e.lightMap]||null),e.lightMapIntensity!==void 0&&(this.lightMapIntensity=e.lightMapIntensity),e.aoMap!==void 0&&(this.aoMap=t[e.aoMap]||null),e.aoMapIntensity!==void 0&&(this.aoMapIntensity=e.aoMapIntensity),e.gradientMap!==void 0&&(this.gradientMap=t[e.gradientMap]||null),e.clearcoatMap!==void 0&&(this.clearcoatMap=t[e.clearcoatMap]||null),e.clearcoatRoughnessMap!==void 0&&(this.clearcoatRoughnessMap=t[e.clearcoatRoughnessMap]||null),e.clearcoatNormalMap!==void 0&&(this.clearcoatNormalMap=t[e.clearcoatNormalMap]||null),e.clearcoatNormalScale!==void 0&&(this.clearcoatNormalScale=new De().fromArray(e.clearcoatNormalScale)),e.iridescenceMap!==void 0&&(this.iridescenceMap=t[e.iridescenceMap]||null),e.iridescenceThicknessMap!==void 0&&(this.iridescenceThicknessMap=t[e.iridescenceThicknessMap]||null),e.transmissionMap!==void 0&&(this.transmissionMap=t[e.transmissionMap]||null),e.thicknessMap!==void 0&&(this.thicknessMap=t[e.thicknessMap]||null),e.anisotropyMap!==void 0&&(this.anisotropyMap=t[e.anisotropyMap]||null),e.sheenColorMap!==void 0&&(this.sheenColorMap=t[e.sheenColorMap]||null),e.sheenRoughnessMap!==void 0&&(this.sheenRoughnessMap=t[e.sheenRoughnessMap]||null),this}clone(){return new this.constructor().copy(this)}copy(e){this.name=e.name,this.blending=e.blending,this.side=e.side,this.vertexColors=e.vertexColors,this.opacity=e.opacity,this.transparent=e.transparent,this.blendSrc=e.blendSrc,this.blendDst=e.blendDst,this.blendEquation=e.blendEquation,this.blendSrcAlpha=e.blendSrcAlpha,this.blendDstAlpha=e.blendDstAlpha,this.blendEquationAlpha=e.blendEquationAlpha,this.blendColor.copy(e.blendColor),this.blendAlpha=e.blendAlpha,this.depthFunc=e.depthFunc,this.depthTest=e.depthTest,this.depthWrite=e.depthWrite,this.stencilWriteMask=e.stencilWriteMask,this.stencilFunc=e.stencilFunc,this.stencilRef=e.stencilRef,this.stencilFuncMask=e.stencilFuncMask,this.stencilFail=e.stencilFail,this.stencilZFail=e.stencilZFail,this.stencilZPass=e.stencilZPass,this.stencilWrite=e.stencilWrite;let t=e.clippingPlanes,n=null;if(t!==null){let s=t.length;n=new Array(s);for(let r=0;r!==s;++r)n[r]=t[r].clone()}return this.clippingPlanes=n,this.clipIntersection=e.clipIntersection,this.clipShadows=e.clipShadows,this.shadowSide=e.shadowSide,this.colorWrite=e.colorWrite,this.precision=e.precision,this.polygonOffset=e.polygonOffset,this.polygonOffsetFactor=e.polygonOffsetFactor,this.polygonOffsetUnits=e.polygonOffsetUnits,this.dithering=e.dithering,this.alphaTest=e.alphaTest,this.alphaHash=e.alphaHash,this.alphaToCoverage=e.alphaToCoverage,this.premultipliedAlpha=e.premultipliedAlpha,this.forceSinglePass=e.forceSinglePass,this.allowOverride=e.allowOverride,this.visible=e.visible,this.toneMapped=e.toneMapped,this.userData=JSON.parse(JSON.stringify(e.userData)),this}dispose(){this.dispatchEvent({type:"dispose"})}set needsUpdate(e){e===!0&&this.version++}};var si=new U,Ll=new U,la=new U,ca=new U,Bi=class{constructor(e=new U,t=new U(0,0,-1)){this.origin=e,this.direction=t}set(e,t){return this.origin.copy(e),this.direction.copy(t),this}copy(e){return this.origin.copy(e.origin),this.direction.copy(e.direction),this}at(e,t){return t.copy(this.origin).addScaledVector(this.direction,e)}lookAt(e){return this.direction.copy(e).sub(this.origin).normalize(),this}recast(e){return this.origin.copy(this.at(e,si)),this}closestPointToPoint(e,t){t.subVectors(e,this.origin);let n=t.dot(this.direction);return n<0?t.copy(this.origin):t.copy(this.origin).addScaledVector(this.direction,n)}distanceToPoint(e){return Math.sqrt(this.distanceSqToPoint(e))}distanceSqToPoint(e){let t=si.subVectors(e,this.origin).dot(this.direction);return t<0?this.origin.distanceToSquared(e):(si.copy(this.origin).addScaledVector(this.direction,t),si.distanceToSquared(e))}distanceSqToSegment(e,t,n,s){Ll.copy(e).add(t).multiplyScalar(.5),la.copy(t).sub(e).normalize(),ca.copy(this.origin).sub(Ll);let r=e.distanceTo(t)*.5,a=-this.direction.dot(la),o=ca.dot(this.direction),l=-ca.dot(la),c=ca.lengthSq(),h=Math.abs(1-a*a),f,u,d,g;if(h>0)if(f=a*l-o,u=a*o-l,g=r*h,f>=0)if(u>=-g)if(u<=g){let b=1/h;f*=b,u*=b,d=f*(f+a*u+2*o)+u*(a*f+u+2*l)+c}else u=r,f=Math.max(0,-(a*u+o)),d=-f*f+u*(u+2*l)+c;else u=-r,f=Math.max(0,-(a*u+o)),d=-f*f+u*(u+2*l)+c;else u<=-g?(f=Math.max(0,-(-a*r+o)),u=f>0?-r:Math.min(Math.max(-r,-l),r),d=-f*f+u*(u+2*l)+c):u<=g?(f=0,u=Math.min(Math.max(-r,-l),r),d=u*(u+2*l)+c):(f=Math.max(0,-(a*r+o)),u=f>0?r:Math.min(Math.max(-r,-l),r),d=-f*f+u*(u+2*l)+c);else u=a>0?-r:r,f=Math.max(0,-(a*u+o)),d=-f*f+u*(u+2*l)+c;return n&&n.copy(this.origin).addScaledVector(this.direction,f),s&&s.copy(Ll).addScaledVector(la,u),d}intersectSphere(e,t){if(e.radius<0)return null;si.subVectors(e.center,this.origin);let n=si.dot(this.direction),s=si.dot(si)-n*n,r=e.radius*e.radius;if(s>r)return null;let a=Math.sqrt(r-s),o=n-a,l=n+a;return l<0?null:o<0?this.at(l,t):this.at(o,t)}intersectsSphere(e){return e.radius<0?!1:this.distanceSqToPoint(e.center)<=e.radius*e.radius}distanceToPlane(e){let t=e.normal.dot(this.direction);if(t===0)return e.distanceToPoint(this.origin)===0?0:null;let n=-(this.origin.dot(e.normal)+e.constant)/t;return n>=0?n:null}intersectPlane(e,t){let n=this.distanceToPlane(e);return n===null?null:this.at(n,t)}intersectsPlane(e){let t=e.distanceToPoint(this.origin);return t===0||e.normal.dot(this.direction)*t<0}intersectBox(e,t){let n,s,r,a,o,l,c=1/this.direction.x,h=1/this.direction.y,f=1/this.direction.z,u=this.origin;return c>=0?(n=(e.min.x-u.x)*c,s=(e.max.x-u.x)*c):(n=(e.max.x-u.x)*c,s=(e.min.x-u.x)*c),h>=0?(r=(e.min.y-u.y)*h,a=(e.max.y-u.y)*h):(r=(e.max.y-u.y)*h,a=(e.min.y-u.y)*h),n>a||r>s||((r>n||isNaN(n))&&(n=r),(a<s||isNaN(s))&&(s=a),f>=0?(o=(e.min.z-u.z)*f,l=(e.max.z-u.z)*f):(o=(e.max.z-u.z)*f,l=(e.min.z-u.z)*f),n>l||o>s)||((o>n||n!==n)&&(n=o),(l<s||s!==s)&&(s=l),s<0)?null:this.at(n>=0?n:s,t)}intersectsBox(e){return this.intersectBox(e,si)!==null}intersectTriangle(e,t,n,s,r){let a=this.origin,o=this.direction,l=o.x,c=o.y,h=o.z,f=e.x-a.x,u=e.y-a.y,d=e.z-a.z,g=t.x-a.x,b=t.y-a.y,m=t.z-a.z,p=n.x-a.x,E=n.y-a.y,C=n.z-a.z,y=Math.abs(l),w=Math.abs(c),T=Math.abs(h),I,x,A,D,k,G,Y,F,$,te,re,Z;if(y>=w&&y>=T?(A=l,G=f,$=g,Z=p,l>=0?(I=c,x=h,D=u,k=d,Y=b,F=m,te=E,re=C):(I=h,x=c,D=d,k=u,Y=m,F=b,te=C,re=E)):w>=T?(A=c,G=u,$=b,Z=E,c>=0?(I=h,x=l,D=d,k=f,Y=m,F=g,te=C,re=p):(I=l,x=h,D=f,k=d,Y=g,F=m,te=p,re=C)):(A=h,G=d,$=m,Z=C,h>=0?(I=l,x=c,D=f,k=u,Y=g,F=b,te=p,re=E):(I=c,x=l,D=u,k=f,Y=b,F=g,te=E,re=p)),A===0)return null;let Q=I/A,ce=x/A,se=1/A,Ge=D-Q*G,Ce=k-ce*G,ut=Y-Q*$,Ze=F-ce*$,Xe=te-Q*Z,ee=re-ce*Z,ne=Xe*Ze-ee*ut,xe=Ge*ee-Ce*Xe,Pe=ut*Ce-Ze*Ge;if(s){if(ne<0||xe<0||Pe<0)return null}else if((ne<0||xe<0||Pe<0)&&(ne>0||xe>0||Pe>0))return null;let Re=ne+xe+Pe;if(Re===0)return null;let Je=se*(ne*G+xe*$+Pe*Z);return(Re>0?Je<0:Je>0)?null:this.at(Je/Re,r)}applyMatrix4(e){return this.origin.applyMatrix4(e),this.direction.transformDirection(e),this}equals(e){return e.origin.equals(this.origin)&&e.direction.equals(this.direction)}clone(){return new this.constructor().copy(this)}},un=class extends On{constructor(e){super(),this.isMeshBasicMaterial=!0,this.type="MeshBasicMaterial",this.color=new Qe(16777215),this.map=null,this.lightMap=null,this.lightMapIntensity=1,this.aoMap=null,this.aoMapIntensity=1,this.specularMap=null,this.alphaMap=null,this.envMap=null,this.envMapRotation=new wn,this.combine=uo,this.reflectivity=1,this.refractionRatio=.98,this.wireframe=!1,this.wireframeLinewidth=1,this.wireframeLinecap="round",this.wireframeLinejoin="round",this.fog=!0,this.setValues(e)}copy(e){return super.copy(e),this.color.copy(e.color),this.map=e.map,this.lightMap=e.lightMap,this.lightMapIntensity=e.lightMapIntensity,this.aoMap=e.aoMap,this.aoMapIntensity=e.aoMapIntensity,this.specularMap=e.specularMap,this.alphaMap=e.alphaMap,this.envMap=e.envMap,this.envMapRotation.copy(e.envMapRotation),this.combine=e.combine,this.reflectivity=e.reflectivity,this.refractionRatio=e.refractionRatio,this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this.wireframeLinecap=e.wireframeLinecap,this.wireframeLinejoin=e.wireframeLinejoin,this.fog=e.fog,this}},jc=new xt,Ui=new Bi,ua=new Zn,Jc=new U,ha=new U,da=new U,fa=new U,Nl=new U,pa=new U,Kc=new U,ma=new U,bt=class extends Ht{constructor(e=new Rt,t=new un){super(),this.isMesh=!0,this.type="Mesh",this.geometry=e,this.material=t,this.morphTargetDictionary=void 0,this.morphTargetInfluences=void 0,this.count=1,this.updateMorphTargets()}copy(e,t){return super.copy(e,t),e.morphTargetInfluences!==void 0&&(this.morphTargetInfluences=e.morphTargetInfluences.slice()),e.morphTargetDictionary!==void 0&&(this.morphTargetDictionary=Object.assign({},e.morphTargetDictionary)),this.material=Array.isArray(e.material)?e.material.slice():e.material,this.geometry=e.geometry,this}updateMorphTargets(){let t=this.geometry.morphAttributes,n=Object.keys(t);if(n.length>0){let s=t[n[0]];if(s!==void 0){this.morphTargetInfluences=[],this.morphTargetDictionary={};for(let r=0,a=s.length;r<a;r++){let o=s[r].name||String(r);this.morphTargetInfluences.push(0),this.morphTargetDictionary[o]=r}}}}getVertexPosition(e,t){let n=this.geometry,s=n.attributes.position,r=n.morphAttributes.position,a=n.morphTargetsRelative;t.fromBufferAttribute(s,e);let o=this.morphTargetInfluences;if(r&&o){pa.set(0,0,0);for(let l=0,c=r.length;l<c;l++){let h=o[l],f=r[l];h!==0&&(Nl.fromBufferAttribute(f,e),a?pa.addScaledVector(Nl,h):pa.addScaledVector(Nl.sub(t),h))}t.add(pa)}return t}intersectsFrustum(e){return e.intersectsObject(this)}raycast(e,t){let n=this.geometry,s=this.material,r=this.matrixWorld;s!==void 0&&(n.boundingSphere===null&&n.computeBoundingSphere(),ua.copy(n.boundingSphere),ua.applyMatrix4(r),Ui.copy(e.ray).recast(e.near),!(ua.containsPoint(Ui.origin)===!1&&(Ui.intersectSphere(ua,Jc)===null||Ui.origin.distanceToSquared(Jc)>(e.far-e.near)**2))&&(jc.copy(r).invert(),Ui.copy(e.ray).applyMatrix4(jc),!(n.boundingBox!==null&&Ui.intersectsBox(n.boundingBox)===!1)&&this._computeIntersections(e,t,Ui)))}_computeIntersections(e,t,n){let s,r=this.geometry,a=this.material,o=r.index,l=r.attributes.position,c=r.attributes.uv,h=r.attributes.uv1,f=r.attributes.normal,u=r.groups,d=r.drawRange;if(o!==null)if(Array.isArray(a))for(let g=0,b=u.length;g<b;g++){let m=u[g],p=a[m.materialIndex],E=Math.max(m.start,d.start),C=Math.min(o.count,Math.min(m.start+m.count,d.start+d.count));for(let y=E,w=C;y<w;y+=3){let T=o.getX(y),I=o.getX(y+1),x=o.getX(y+2);s=ga(this,p,e,n,c,h,f,T,I,x),s&&(s.faceIndex=Math.floor(y/3),s.face.materialIndex=m.materialIndex,t.push(s))}}else{let g=Math.max(0,d.start),b=Math.min(o.count,d.start+d.count);for(let m=g,p=b;m<p;m+=3){let E=o.getX(m),C=o.getX(m+1),y=o.getX(m+2);s=ga(this,a,e,n,c,h,f,E,C,y),s&&(s.faceIndex=Math.floor(m/3),t.push(s))}}else if(l!==void 0)if(Array.isArray(a))for(let g=0,b=u.length;g<b;g++){let m=u[g],p=a[m.materialIndex],E=Math.max(m.start,d.start),C=Math.min(l.count,Math.min(m.start+m.count,d.start+d.count));for(let y=E,w=C;y<w;y+=3){let T=y,I=y+1,x=y+2;s=ga(this,p,e,n,c,h,f,T,I,x),s&&(s.faceIndex=Math.floor(y/3),s.face.materialIndex=m.materialIndex,t.push(s))}}else{let g=Math.max(0,d.start),b=Math.min(l.count,d.start+d.count);for(let m=g,p=b;m<p;m+=3){let E=m,C=m+1,y=m+2;s=ga(this,a,e,n,c,h,f,E,C,y),s&&(s.faceIndex=Math.floor(m/3),t.push(s))}}}};function Cd(i,e,t,n,s,r,a,o){let l;if(e.side===en?l=n.intersectTriangle(a,r,s,!0,o):l=n.intersectTriangle(s,r,a,e.side===Ti,o),l===null)return null;ma.copy(o),ma.applyMatrix4(i.matrixWorld);let c=t.ray.origin.distanceTo(ma);return c<t.near||c>t.far?null:{distance:c,point:ma.clone(),object:i}}function ga(i,e,t,n,s,r,a,o,l,c){i.getVertexPosition(o,ha),i.getVertexPosition(l,da),i.getVertexPosition(c,fa);let h=Cd(i,e,t,n,ha,da,fa,Kc);if(h){let f=new U;xi.getBarycoord(Kc,ha,da,fa,f),s&&(h.uv=xi.getInterpolatedAttribute(s,o,l,c,f,new De)),r&&(h.uv1=xi.getInterpolatedAttribute(r,o,l,c,f,new De)),a&&(h.normal=xi.getInterpolatedAttribute(a,o,l,c,f,new U),h.normal.dot(n.direction)>0&&h.normal.multiplyScalar(-1));let u={a:o,b:l,c,normal:new U,materialIndex:0};xi.getNormal(ha,da,fa,u.normal),h.face=u,h.barycoord=f}return h}var ur=class extends mn{constructor(e=null,t=1,n=1,s,r,a,o,l,c=Yt,h=Yt,f,u){super(null,a,o,l,c,h,s,r,f,u),this.isDataTexture=!0,this.image={data:e,width:t,height:n},this.generateMipmaps=!1,this.flipY=!1,this.unpackAlignment=1}};var hr=class extends Kt{constructor(e,t,n,s=1){super(e,t,n),this.isInstancedBufferAttribute=!0,this.meshPerAttribute=s}copy(e){return super.copy(e),this.meshPerAttribute=e.meshPerAttribute,this}toJSON(){let e=super.toJSON();return e.meshPerAttribute=this.meshPerAttribute,e.isInstancedBufferAttribute=!0,e}},ls=new xt,Qc=new xt,_a=[],eu=new Yn,Rd=new xt,Zs=new bt,js=new Zn,gn=class extends bt{constructor(e,t,n){super(e,t),this.isInstancedMesh=!0,this.instanceMatrix=new hr(new Float32Array(n*16),16),this.instanceColor=null,this.morphTexture=null,this.count=n,this.boundingBox=null,this.boundingSphere=null;for(let s=0;s<n;s++)this.setMatrixAt(s,Rd)}computeBoundingBox(){let e=this.geometry,t=this.count;this.boundingBox===null&&(this.boundingBox=new Yn),e.boundingBox===null&&e.computeBoundingBox(),this.boundingBox.makeEmpty();for(let n=0;n<t;n++)this.getMatrixAt(n,ls),eu.copy(e.boundingBox).applyMatrix4(ls),this.boundingBox.union(eu)}computeBoundingSphere(){let e=this.geometry,t=this.count;this.boundingSphere===null&&(this.boundingSphere=new Zn),e.boundingSphere===null&&e.computeBoundingSphere(),this.boundingSphere.makeEmpty();for(let n=0;n<t;n++)this.getMatrixAt(n,ls),js.copy(e.boundingSphere).applyMatrix4(ls),this.boundingSphere.union(js)}copy(e,t){return super.copy(e,t),this.instanceMatrix.copy(e.instanceMatrix),e.morphTexture!==null&&(this.morphTexture=e.morphTexture.clone()),e.instanceColor!==null&&(this.instanceColor=e.instanceColor.clone()),this.count=e.count,e.boundingBox!==null&&(this.boundingBox=e.boundingBox.clone()),e.boundingSphere!==null&&(this.boundingSphere=e.boundingSphere.clone()),this}getColorAt(e,t){return this.instanceColor===null?t.setRGB(1,1,1):t.fromArray(this.instanceColor.array,e*3)}getMatrixAt(e,t){return t.fromArray(this.instanceMatrix.array,e*16)}getMorphAt(e,t){let n=t.morphTargetInfluences,s=this.morphTexture.source.data.data,r=n.length+1,a=e*r+1;for(let o=0;o<n.length;o++)n[o]=s[a+o]}raycast(e,t){let n=this.matrixWorld,s=this.count;if(Zs.geometry=this.geometry,Zs.material=this.material,Zs.material!==void 0&&(this.boundingSphere===null&&this.computeBoundingSphere(),js.copy(this.boundingSphere),js.applyMatrix4(n),e.ray.intersectsSphere(js)!==!1))for(let r=0;r<s;r++){this.getMatrixAt(r,ls),Qc.multiplyMatrices(n,ls),Zs.matrixWorld=Qc,Zs.raycast(e,_a);for(let a=0,o=_a.length;a<o;a++){let l=_a[a];l.instanceId=r,l.object=this,t.push(l)}_a.length=0}}setColorAt(e,t){return this.instanceColor===null&&(this.instanceColor=new hr(new Float32Array(this.instanceMatrix.count*3).fill(1),3)),t.toArray(this.instanceColor.array,e*3),this}setMatrixAt(e,t){return t.toArray(this.instanceMatrix.array,e*16),this}setMorphAt(e,t){let n=t.morphTargetInfluences,s=n.length+1;this.morphTexture===null&&(this.morphTexture=new ur(new Float32Array(s*this.count),s,this.count,xo,Pn));let r=this.morphTexture.source.data.data,a=0;for(let c=0;c<n.length;c++)a+=n[c];let o=this.geometry.morphTargetsRelative?1:1-a,l=s*e;return r[l]=o,r.set(n,l+1),this}updateMorphTargets(){}dispose(){super.dispose(),this.morphTexture!==null&&(this.morphTexture.dispose(),this.morphTexture=null)}},Fi=new Zn,Pd=new De(.5,.5),xa=new U,bs=class{constructor(e=new Fn,t=new Fn,n=new Fn,s=new Fn,r=new Fn,a=new Fn){this.planes=[e,t,n,s,r,a]}set(e,t,n,s,r,a){let o=this.planes;return o[0].copy(e),o[1].copy(t),o[2].copy(n),o[3].copy(s),o[4].copy(r),o[5].copy(a),this}copy(e){let t=this.planes;for(let n=0;n<6;n++)t[n].copy(e.planes[n]);return this}setFromProjectionMatrix(e,t=kn,n=!1){let s=this.planes,r=e.elements,a=r[0],o=r[1],l=r[2],c=r[3],h=r[4],f=r[5],u=r[6],d=r[7],g=r[8],b=r[9],m=r[10],p=r[11],E=r[12],C=r[13],y=r[14],w=r[15];if(s[0].setComponents(c-a,d-h,p-g,w-E).normalize(),s[1].setComponents(c+a,d+h,p+g,w+E).normalize(),s[2].setComponents(c+o,d+f,p+b,w+C).normalize(),s[3].setComponents(c-o,d-f,p-b,w-C).normalize(),n)s[4].setComponents(l,u,m,y).normalize(),s[5].setComponents(c-l,d-u,p-m,w-y).normalize();else if(s[4].setComponents(c-l,d-u,p-m,w-y).normalize(),t===kn)s[5].setComponents(c+l,d+u,p+m,w+y).normalize();else if(t===ms)s[5].setComponents(l,u,m,y).normalize();else throw new Error("THREE.Frustum.setFromProjectionMatrix(): Invalid coordinate system: "+t);return this}intersectsObject(e){if(e.boundingSphere!==void 0)e.boundingSphere===null&&e.computeBoundingSphere(),Fi.copy(e.boundingSphere).applyMatrix4(e.matrixWorld);else{let t=e.geometry;t.boundingSphere===null&&t.computeBoundingSphere(),Fi.copy(t.boundingSphere).applyMatrix4(e.matrixWorld)}return this.intersectsSphere(Fi)}intersectsSprite(e){Fi.center.set(0,0,0);let t=Pd.distanceTo(e.center);return Fi.radius=.7071067811865476+t,Fi.applyMatrix4(e.matrixWorld),this.intersectsSphere(Fi)}intersectsSphere(e){let t=this.planes,n=e.center,s=-e.radius;for(let r=0;r<6;r++)if(t[r].distanceToPoint(n)<s)return!1;return!0}intersectsBox(e){let t=this.planes;for(let n=0;n<6;n++){let s=t[n];if(xa.x=s.normal.x>0?e.max.x:e.min.x,xa.y=s.normal.y>0?e.max.y:e.min.y,xa.z=s.normal.z>0?e.max.z:e.min.z,s.distanceToPoint(xa)<0)return!1}return!0}containsPoint(e){let t=this.planes;for(let n=0;n<6;n++)if(t[n].distanceToPoint(e)<0)return!1;return!0}clone(){return new this.constructor().copy(this)}};var ai=class extends On{constructor(e){super(),this.isLineBasicMaterial=!0,this.type="LineBasicMaterial",this.color=new Qe(16777215),this.map=null,this.linewidth=1,this.linecap="round",this.linejoin="round",this.fog=!0,this.setValues(e)}copy(e){return super.copy(e),this.color.copy(e.color),this.map=e.map,this.linewidth=e.linewidth,this.linecap=e.linecap,this.linejoin=e.linejoin,this.fog=e.fog,this}},za=new U,Va=new U,tu=new xt,Js=new Bi,va=new Zn,Dl=new U,nu=new U,zi=class extends Ht{constructor(e=new Rt,t=new ai){super(),this.isLine=!0,this.type="Line",this.geometry=e,this.material=t,this.morphTargetDictionary=void 0,this.morphTargetInfluences=void 0,this.updateMorphTargets()}copy(e,t){return super.copy(e,t),this.material=Array.isArray(e.material)?e.material.slice():e.material,this.geometry=e.geometry,this}computeLineDistances(){let e=this.geometry;if(e.index===null){let t=e.attributes.position,n=[0];for(let s=1,r=t.count;s<r;s++)za.fromBufferAttribute(t,s-1),Va.fromBufferAttribute(t,s),n[s]=n[s-1],n[s]+=za.distanceTo(Va);e.setAttribute("lineDistance",new yt(n,1))}else je("Line.computeLineDistances(): Computation only possible with non-indexed BufferGeometry.");return this}intersectsFrustum(e){return e.intersectsObject(this)}raycast(e,t){let n=this.geometry,s=this.matrixWorld,r=e.params.Line.threshold,a=n.drawRange;if(n.boundingSphere===null&&n.computeBoundingSphere(),va.copy(n.boundingSphere),va.applyMatrix4(s),va.radius+=r,e.ray.intersectsSphere(va)===!1)return;tu.copy(s).invert(),Js.copy(e.ray).applyMatrix4(tu);let o=r/((this.scale.x+this.scale.y+this.scale.z)/3),l=o*o,c=this.isLineSegments?2:1,h=n.index,u=n.attributes.position;if(h!==null){let d=Math.max(0,a.start),g=Math.min(h.count,a.start+a.count);for(let b=d,m=g-1;b<m;b+=c){let p=h.getX(b),E=h.getX(b+1),C=ya(this,e,Js,l,p,E,b);C&&t.push(C)}if(this.isLineLoop){let b=h.getX(g-1),m=h.getX(d),p=ya(this,e,Js,l,b,m,g-1);p&&t.push(p)}}else{let d=Math.max(0,a.start),g=Math.min(u.count,a.start+a.count);for(let b=d,m=g-1;b<m;b+=c){let p=ya(this,e,Js,l,b,b+1,b);p&&t.push(p)}if(this.isLineLoop){let b=ya(this,e,Js,l,g-1,d,g-1);b&&t.push(b)}}}updateMorphTargets(){let t=this.geometry.morphAttributes,n=Object.keys(t);if(n.length>0){let s=t[n[0]];if(s!==void 0){this.morphTargetInfluences=[],this.morphTargetDictionary={};for(let r=0,a=s.length;r<a;r++){let o=s[r].name||String(r);this.morphTargetInfluences.push(0),this.morphTargetDictionary[o]=r}}}}};function ya(i,e,t,n,s,r,a){let o=i.geometry.attributes.position;if(za.fromBufferAttribute(o,s),Va.fromBufferAttribute(o,r),t.distanceSqToSegment(za,Va,Dl,nu)>n)return;Dl.applyMatrix4(i.matrixWorld);let c=e.ray.origin.distanceTo(Dl);if(!(c<e.near||c>e.far))return{distance:c,point:nu.clone().applyMatrix4(i.matrixWorld),index:a,face:null,faceIndex:null,barycoord:null,object:i}}var dr=class extends zi{constructor(e,t){super(e,t),this.isLineLoop=!0,this.type="LineLoop"}},Ms=class extends On{constructor(e){super(),this.isPointsMaterial=!0,this.type="PointsMaterial",this.color=new Qe(16777215),this.map=null,this.alphaMap=null,this.size=1,this.sizeAttenuation=!0,this.fog=!0,this.setValues(e)}copy(e){return super.copy(e),this.color.copy(e.color),this.map=e.map,this.alphaMap=e.alphaMap,this.size=e.size,this.sizeAttenuation=e.sizeAttenuation,this.fog=e.fog,this}},iu=new xt,Wl=new Bi,ba=new Zn,Ma=new U,fr=class extends Ht{constructor(e=new Rt,t=new Ms){super(),this.isPoints=!0,this.type="Points",this.geometry=e,this.material=t,this.morphTargetDictionary=void 0,this.morphTargetInfluences=void 0,this.updateMorphTargets()}copy(e,t){return super.copy(e,t),this.material=Array.isArray(e.material)?e.material.slice():e.material,this.geometry=e.geometry,this}intersectsFrustum(e){return e.intersectsObject(this)}raycast(e,t){let n=this.geometry,s=this.matrixWorld,r=e.params.Points.threshold,a=n.drawRange;if(n.boundingSphere===null&&n.computeBoundingSphere(),ba.copy(n.boundingSphere),ba.applyMatrix4(s),ba.radius+=r,e.ray.intersectsSphere(ba)===!1)return;iu.copy(s).invert(),Wl.copy(e.ray).applyMatrix4(iu);let o=r/((this.scale.x+this.scale.y+this.scale.z)/3),l=o*o,c=n.index,f=n.attributes.position;if(c!==null){let u=Math.max(0,a.start),d=Math.min(c.count,a.start+a.count);for(let g=u,b=d;g<b;g++){let m=c.getX(g);Ma.fromBufferAttribute(f,m),su(Ma,m,l,s,e,t,this)}}else{let u=Math.max(0,a.start),d=Math.min(f.count,a.start+a.count);for(let g=u,b=d;g<b;g++)Ma.fromBufferAttribute(f,g),su(Ma,g,l,s,e,t,this)}}updateMorphTargets(){let t=this.geometry.morphAttributes,n=Object.keys(t);if(n.length>0){let s=t[n[0]];if(s!==void 0){this.morphTargetInfluences=[],this.morphTargetDictionary={};for(let r=0,a=s.length;r<a;r++){let o=s[r].name||String(r);this.morphTargetInfluences.push(0),this.morphTargetDictionary[o]=r}}}}};function su(i,e,t,n,s,r,a){let o=Wl.distanceSqToPoint(i);if(o<t){let l=new U;Wl.closestPointToPoint(i,l),l.applyMatrix4(n);let c=s.ray.origin.distanceTo(l);if(c<s.near||c>s.far)return;r.push({distance:c,distanceToRay:Math.sqrt(o),point:l,index:e,face:null,faceIndex:null,barycoord:null,object:a})}}var pr=class extends mn{constructor(e=[],t=Ei,n,s,r,a,o,l,c,h){super(e,t,n,s,r,a,o,l,c,h),this.isCubeTexture=!0,this.flipY=!1}get images(){return this.image}set images(e){this.image=e}};var vi=class extends mn{constructor(e,t,n=Vn,s,r,a,o=Yt,l=Yt,c,h=Xn,f=1){if(h!==Xn&&h!==Ai)throw new Error("THREE.DepthTexture: format must be either THREE.DepthFormat or THREE.DepthStencilFormat");let u={width:e,height:t,depth:f};super(u,s,r,a,o,l,h,n,c),this.isDepthTexture=!0,this.flipY=!1,this.generateMipmaps=!1,this.compareFunction=null}copy(e){return super.copy(e),this.source=new xs(Object.assign({},e.image)),this.compareFunction=e.compareFunction,this}toJSON(e){let t=super.toJSON(e);return t.compareFunction=this.compareFunction,t}},Ha=class extends vi{constructor(e,t=Vn,n=Ei,s,r,a=Yt,o=Yt,l,c=Xn){let h={width:e,height:e,depth:1},f=[h,h,h,h,h,h];super(e,e,t,n,s,r,a,o,l,c),this.image=f,this.isCubeDepthTexture=!0,this.isCubeTexture=!0}get images(){return this.image}set images(e){this.image=e}},mr=class extends mn{constructor(e=null){super(),this.sourceTexture=e,this.isExternalTexture=!0}copy(e){return super.copy(e),this.sourceTexture=e.sourceTexture,this}},Bn=class i extends Rt{constructor(e=1,t=1,n=1,s=1,r=1,a=1){super(),this.type="BoxGeometry",this.parameters={width:e,height:t,depth:n,widthSegments:s,heightSegments:r,depthSegments:a};let o=this;s=Math.floor(s),r=Math.floor(r),a=Math.floor(a);let l=[],c=[],h=[],f=[],u=0,d=0;g("z","y","x",-1,-1,n,t,e,a,r,0),g("z","y","x",1,-1,n,t,-e,a,r,1),g("x","z","y",1,1,e,n,t,s,a,2),g("x","z","y",1,-1,e,n,-t,s,a,3),g("x","y","z",1,-1,e,t,n,s,r,4),g("x","y","z",-1,-1,e,t,-n,s,r,5),this.setIndex(l),this.setAttribute("position",new yt(c,3)),this.setAttribute("normal",new yt(h,3)),this.setAttribute("uv",new yt(f,2));function g(b,m,p,E,C,y,w,T,I,x,A){let D=y/I,k=w/x,G=y/2,Y=w/2,F=T/2,$=I+1,te=x+1,re=0,Z=0,Q=new U;for(let ce=0;ce<te;ce++){let se=ce*k-Y;for(let Ge=0;Ge<$;Ge++){let Ce=Ge*D-G;Q[b]=Ce*E,Q[m]=se*C,Q[p]=F,c.push(Q.x,Q.y,Q.z),Q[b]=0,Q[m]=0,Q[p]=T>0?1:-1,h.push(Q.x,Q.y,Q.z),f.push(Ge/I),f.push(1-ce/x),re+=1}}for(let ce=0;ce<x;ce++)for(let se=0;se<I;se++){let Ge=u+se+$*ce,Ce=u+se+$*(ce+1),ut=u+(se+1)+$*(ce+1),Ze=u+(se+1)+$*ce;l.push(Ge,Ce,Ze),l.push(Ce,ut,Ze),Z+=6}o.addGroup(d,Z,A),d+=Z,u+=re}}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}static fromJSON(e){return new i(e.width,e.height,e.depth,e.widthSegments,e.heightSegments,e.depthSegments)}};var jn=class i extends Rt{constructor(e=1,t=1,n=1,s=32,r=1,a=!1,o=0,l=Math.PI*2){super(),this.type="CylinderGeometry",this.parameters={radiusTop:e,radiusBottom:t,height:n,radialSegments:s,heightSegments:r,openEnded:a,thetaStart:o,thetaLength:l};let c=this;s=Math.floor(s),r=Math.floor(r);let h=[],f=[],u=[],d=[],g=0,b=[],m=n/2,p=0;E(),a===!1&&(e>0&&C(!0),t>0&&C(!1)),this.setIndex(h),this.setAttribute("position",new yt(f,3)),this.setAttribute("normal",new yt(u,3)),this.setAttribute("uv",new yt(d,2));function E(){let y=new U,w=new U,T=0,I=(t-e)/n;for(let x=0;x<=r;x++){let A=[],D=x/r,k=D*(t-e)+e;for(let G=0;G<=s;G++){let Y=G/s,F=Y*l+o,$=Math.sin(F),te=Math.cos(F);w.x=k*$,w.y=-D*n+m,w.z=k*te,f.push(w.x,w.y,w.z),y.set($,I,te).normalize(),u.push(y.x,y.y,y.z),d.push(Y,1-D),A.push(g++)}b.push(A)}for(let x=0;x<s;x++)for(let A=0;A<r;A++){let D=b[A][x],k=b[A+1][x],G=b[A+1][x+1],Y=b[A][x+1];(e>0||A!==0)&&(h.push(D,k,Y),T+=3),(t>0||A!==r-1)&&(h.push(k,G,Y),T+=3)}c.addGroup(p,T,0),p+=T}function C(y){let w=g,T=new De,I=new U,x=0,A=y===!0?e:t,D=y===!0?1:-1;for(let G=1;G<=s;G++)f.push(0,m*D,0),u.push(0,D,0),d.push(.5,.5),g++;let k=g;for(let G=0;G<=s;G++){let F=G/s*l+o,$=Math.cos(F),te=Math.sin(F);I.x=A*te,I.y=m*D,I.z=A*$,f.push(I.x,I.y,I.z),u.push(0,D,0),T.x=$*.5+.5,T.y=te*.5*D+.5,d.push(T.x,T.y),g++}for(let G=0;G<s;G++){let Y=w+G,F=k+G;y===!0?h.push(F,F+1,Y):h.push(F+1,F,Y),x+=3}c.addGroup(p,x,y===!0?1:2),p+=x}}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}static fromJSON(e){return new i(e.radiusTop,e.radiusBottom,e.height,e.radialSegments,e.heightSegments,e.openEnded,e.thetaStart,e.thetaLength)}},gr=class i extends jn{constructor(e=1,t=1,n=32,s=1,r=!1,a=0,o=Math.PI*2){super(0,e,t,n,s,r,a,o),this.type="ConeGeometry",this.parameters={radius:e,height:t,radialSegments:n,heightSegments:s,openEnded:r,thetaStart:a,thetaLength:o}}static fromJSON(e){return new i(e.radius,e.height,e.radialSegments,e.heightSegments,e.openEnded,e.thetaStart,e.thetaLength)}},Ss=class i extends Rt{constructor(e=[],t=[],n=1,s=0){super(),this.type="PolyhedronGeometry",this.parameters={vertices:e,indices:t,radius:n,detail:s};let r=[],a=[];o(s),c(n),h(),this.setAttribute("position",new yt(r,3)),this.setAttribute("normal",new yt(r.slice(),3)),this.setAttribute("uv",new yt(a,2)),s===0?this.computeVertexNormals():this.normalizeNormals();function o(E){let C=new U,y=new U,w=new U;for(let T=0;T<t.length;T+=3)d(t[T+0],C),d(t[T+1],y),d(t[T+2],w),l(C,y,w,E)}function l(E,C,y,w){let T=w+1,I=[];for(let x=0;x<=T;x++){I[x]=[];let A=E.clone().lerp(y,x/T),D=C.clone().lerp(y,x/T),k=T-x;for(let G=0;G<=k;G++)G===0&&x===T?I[x][G]=A:I[x][G]=A.clone().lerp(D,G/k)}for(let x=0;x<T;x++)for(let A=0;A<2*(T-x)-1;A++){let D=Math.floor(A/2);A%2===0?(u(I[x][D+1]),u(I[x+1][D]),u(I[x][D])):(u(I[x][D+1]),u(I[x+1][D+1]),u(I[x+1][D]))}}function c(E){let C=new U;for(let y=0;y<r.length;y+=3)C.x=r[y+0],C.y=r[y+1],C.z=r[y+2],C.normalize().multiplyScalar(E),r[y+0]=C.x,r[y+1]=C.y,r[y+2]=C.z}function h(){let E=new U;for(let C=0;C<r.length;C+=3){E.x=r[C+0],E.y=r[C+1],E.z=r[C+2];let y=m(E)/2/Math.PI+.5,w=p(E)/Math.PI+.5;a.push(y,1-w)}g(),f()}function f(){for(let E=0;E<a.length;E+=6){let C=a[E+0],y=a[E+2],w=a[E+4],T=Math.max(C,y,w),I=Math.min(C,y,w);T>.9&&I<.1&&(C<.2&&(a[E+0]+=1),y<.2&&(a[E+2]+=1),w<.2&&(a[E+4]+=1))}}function u(E){r.push(E.x,E.y,E.z)}function d(E,C){let y=E*3;C.x=e[y+0],C.y=e[y+1],C.z=e[y+2]}function g(){let E=new U,C=new U,y=new U,w=new U,T=new De,I=new De,x=new De;for(let A=0,D=0;A<r.length;A+=9,D+=6){E.set(r[A+0],r[A+1],r[A+2]),C.set(r[A+3],r[A+4],r[A+5]),y.set(r[A+6],r[A+7],r[A+8]),T.set(a[D+0],a[D+1]),I.set(a[D+2],a[D+3]),x.set(a[D+4],a[D+5]),w.copy(E).add(C).add(y).divideScalar(3);let k=m(w);b(T,D+0,E,k),b(I,D+2,C,k),b(x,D+4,y,k)}}function b(E,C,y,w){w<0&&E.x===1&&(a[C]=E.x-1),y.x===0&&y.z===0&&(a[C]=w/2/Math.PI+.5)}function m(E){return Math.atan2(E.z,-E.x)}function p(E){return Math.atan2(-E.y,Math.sqrt(E.x*E.x+E.z*E.z))}}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}static fromJSON(e){return new i(e.vertices,e.indices,e.radius,e.detail)}},_r=class i extends Ss{constructor(e=1,t=0){let n=(1+Math.sqrt(5))/2,s=1/n,r=[-1,-1,-1,-1,-1,1,-1,1,-1,-1,1,1,1,-1,-1,1,-1,1,1,1,-1,1,1,1,0,-s,-n,0,-s,n,0,s,-n,0,s,n,-s,-n,0,-s,n,0,s,-n,0,s,n,0,-n,0,-s,n,0,-s,-n,0,s,n,0,s],a=[3,11,7,3,7,15,3,15,13,7,19,17,7,17,6,7,6,15,17,4,8,17,8,10,17,10,6,8,0,16,8,16,2,8,2,10,0,12,1,0,1,18,0,18,16,6,10,2,6,2,13,6,13,15,2,16,18,2,18,3,2,3,13,18,1,9,18,9,11,18,11,3,4,14,12,4,12,0,4,0,8,11,9,5,11,5,19,11,19,7,19,5,14,19,14,4,19,4,17,1,12,14,1,14,5,1,5,9];super(r,a,e,t),this.type="DodecahedronGeometry",this.parameters={radius:e,detail:t}}static fromJSON(e){return new i(e.radius,e.detail)}};var An=class{constructor(){this.type="Curve",this.arcLengthDivisions=200,this.needsUpdate=!1,this.cacheArcLengths=null}getPoint(){je("Curve: .getPoint() not implemented.")}getPointAt(e,t){let n=this.getUtoTmapping(e);return this.getPoint(n,t)}getPoints(e=5){let t=[];for(let n=0;n<=e;n++)t.push(this.getPoint(n/e));return t}getSpacedPoints(e=5){let t=[];for(let n=0;n<=e;n++)t.push(this.getPointAt(n/e));return t}getLength(){let e=this.getLengths();return e[e.length-1]}getLengths(e=this.arcLengthDivisions){if(this.cacheArcLengths&&this.cacheArcLengths.length===e+1&&!this.needsUpdate)return this.cacheArcLengths;this.needsUpdate=!1;let t=[],n,s=this.getPoint(0),r=0;t.push(0);for(let a=1;a<=e;a++)n=this.getPoint(a/e),r+=n.distanceTo(s),t.push(r),s=n;return this.cacheArcLengths=t,t}updateArcLengths(){this.needsUpdate=!0,this.getLengths()}getUtoTmapping(e,t=null){let n=this.getLengths(),s=0,r=n.length,a;t?a=t:a=e*n[r-1];let o=0,l=r-1,c;for(;o<=l;)if(s=Math.floor(o+(l-o)/2),c=n[s]-a,c<0)o=s+1;else if(c>0)l=s-1;else{l=s;break}if(s=l,n[s]===a)return s/(r-1);let h=n[s],u=n[s+1]-h,d=(a-h)/u;return(s+d)/(r-1)}getTangent(e,t){let s=e-1e-4,r=e+1e-4;s<0&&(s=0),r>1&&(r=1);let a=this.getPoint(s),o=this.getPoint(r),l=t||(a.isVector2?new De:new U);return l.copy(o).sub(a).normalize(),l}getTangentAt(e,t){let n=this.getUtoTmapping(e);return this.getTangent(n,t)}computeFrenetFrames(e,t=!1){let n=new U,s=[],r=[],a=[],o=new U,l=new xt;for(let d=0;d<=e;d++){let g=d/e;s[d]=this.getTangentAt(g,new U)}r[0]=new U,a[0]=new U;let c=Number.MAX_VALUE,h=Math.abs(s[0].x),f=Math.abs(s[0].y),u=Math.abs(s[0].z);h<=c&&(c=h,n.set(1,0,0)),f<=c&&(c=f,n.set(0,1,0)),u<=c&&n.set(0,0,1),o.crossVectors(s[0],n).normalize(),r[0].crossVectors(s[0],o),a[0].crossVectors(s[0],r[0]);for(let d=1;d<=e;d++){if(r[d]=r[d-1].clone(),a[d]=a[d-1].clone(),o.crossVectors(s[d-1],s[d]),o.length()>Number.EPSILON){o.normalize();let g=Math.acos(mt(s[d-1].dot(s[d]),-1,1));r[d].applyMatrix4(l.makeRotationAxis(o,g))}a[d].crossVectors(s[d],r[d])}if(t===!0){let d=Math.acos(mt(r[0].dot(r[e]),-1,1));d/=e,s[0].dot(o.crossVectors(r[0],r[e]))>0&&(d=-d);for(let g=1;g<=e;g++)r[g].applyMatrix4(l.makeRotationAxis(s[g],d*g)),a[g].crossVectors(s[g],r[g])}return{tangents:s,normals:r,binormals:a}}clone(){return new this.constructor().copy(this)}copy(e){return this.arcLengthDivisions=e.arcLengthDivisions,this}toJSON(){let e={metadata:{version:4.7,type:"Curve",generator:"Curve.toJSON"}};return e.arcLengthDivisions=this.arcLengthDivisions,e.type=this.type,e}fromJSON(e){return this.arcLengthDivisions=e.arcLengthDivisions,this}},xr=class extends An{constructor(e=0,t=0,n=1,s=1,r=0,a=Math.PI*2,o=!1,l=0){super(),this.isEllipseCurve=!0,this.type="EllipseCurve",this.aX=e,this.aY=t,this.xRadius=n,this.yRadius=s,this.aStartAngle=r,this.aEndAngle=a,this.aClockwise=o,this.aRotation=l}getPoint(e,t=new De){let n=t,s=Math.PI*2,r=this.aEndAngle-this.aStartAngle,a=Math.abs(r)<Number.EPSILON;for(;r<0;)r+=s;for(;r>s;)r-=s;r<Number.EPSILON&&(a?r=0:r=s),this.aClockwise===!0&&!a&&(r===s?r=-s:r=r-s);let o=this.aStartAngle+e*r,l=this.aX+this.xRadius*Math.cos(o),c=this.aY+this.yRadius*Math.sin(o);if(this.aRotation!==0){let h=Math.cos(this.aRotation),f=Math.sin(this.aRotation),u=l-this.aX,d=c-this.aY;l=u*h-d*f+this.aX,c=u*f+d*h+this.aY}return n.set(l,c)}copy(e){return super.copy(e),this.aX=e.aX,this.aY=e.aY,this.xRadius=e.xRadius,this.yRadius=e.yRadius,this.aStartAngle=e.aStartAngle,this.aEndAngle=e.aEndAngle,this.aClockwise=e.aClockwise,this.aRotation=e.aRotation,this}toJSON(){let e=super.toJSON();return e.aX=this.aX,e.aY=this.aY,e.xRadius=this.xRadius,e.yRadius=this.yRadius,e.aStartAngle=this.aStartAngle,e.aEndAngle=this.aEndAngle,e.aClockwise=this.aClockwise,e.aRotation=this.aRotation,e}fromJSON(e){return super.fromJSON(e),this.aX=e.aX,this.aY=e.aY,this.xRadius=e.xRadius,this.yRadius=e.yRadius,this.aStartAngle=e.aStartAngle,this.aEndAngle=e.aEndAngle,this.aClockwise=e.aClockwise,this.aRotation=e.aRotation,this}},Ga=class extends xr{constructor(e,t,n,s,r,a){super(e,t,n,n,s,r,a),this.isArcCurve=!0,this.type="ArcCurve"}};function dc(){let i=0,e=0,t=0,n=0;function s(r,a,o,l){i=r,e=o,t=-3*r+3*a-2*o-l,n=2*r-2*a+o+l}return{initCatmullRom:function(r,a,o,l,c){s(a,o,c*(o-r),c*(l-a))},initNonuniformCatmullRom:function(r,a,o,l,c,h,f){let u=(a-r)/c-(o-r)/(c+h)+(o-a)/h,d=(o-a)/h-(l-a)/(h+f)+(l-o)/f;u*=h,d*=h,s(a,o,u,d)},calc:function(r){let a=r*r,o=a*r;return i+e*r+t*a+n*o}}}var ru=new U,au=new U,Ul=new dc,Fl=new dc,kl=new dc,Ts=class extends An{constructor(e=[],t=!1,n="centripetal",s=.5){super(),this.isCatmullRomCurve3=!0,this.type="CatmullRomCurve3",this.points=e,this.closed=t,this.curveType=n,this.tension=s}getPoint(e,t=new U){let n=t,s=this.points,r=s.length,a=(r-(this.closed?0:1))*e,o=Math.floor(a),l=a-o;this.closed?o+=o>0?0:(Math.floor(Math.abs(o)/r)+1)*r:l===0&&o===r-1&&(o=r-2,l=1);let c,h;this.closed||o>0?c=s[(o-1)%r]:(au.subVectors(s[0],s[1]).add(s[0]),c=au);let f=s[o%r],u=s[(o+1)%r];if(this.closed||o+2<r?h=s[(o+2)%r]:(ru.subVectors(s[r-1],s[r-2]).add(s[r-1]),h=ru),this.curveType==="centripetal"||this.curveType==="chordal"){let d=this.curveType==="chordal"?.5:.25,g=Math.pow(c.distanceToSquared(f),d),b=Math.pow(f.distanceToSquared(u),d),m=Math.pow(u.distanceToSquared(h),d);b<1e-4&&(b=1),g<1e-4&&(g=b),m<1e-4&&(m=b),Ul.initNonuniformCatmullRom(c.x,f.x,u.x,h.x,g,b,m),Fl.initNonuniformCatmullRom(c.y,f.y,u.y,h.y,g,b,m),kl.initNonuniformCatmullRom(c.z,f.z,u.z,h.z,g,b,m)}else this.curveType==="catmullrom"&&(Ul.initCatmullRom(c.x,f.x,u.x,h.x,this.tension),Fl.initCatmullRom(c.y,f.y,u.y,h.y,this.tension),kl.initCatmullRom(c.z,f.z,u.z,h.z,this.tension));return n.set(Ul.calc(l),Fl.calc(l),kl.calc(l)),n}copy(e){super.copy(e),this.points=[];for(let t=0,n=e.points.length;t<n;t++){let s=e.points[t];this.points.push(s.clone())}return this.closed=e.closed,this.curveType=e.curveType,this.tension=e.tension,this}toJSON(){let e=super.toJSON();e.points=[];for(let t=0,n=this.points.length;t<n;t++){let s=this.points[t];e.points.push(s.toArray())}return e.closed=this.closed,e.curveType=this.curveType,e.tension=this.tension,e}fromJSON(e){super.fromJSON(e),this.points=[];for(let t=0,n=e.points.length;t<n;t++){let s=e.points[t];this.points.push(new U().fromArray(s))}return this.closed=e.closed,this.curveType=e.curveType,this.tension=e.tension,this}};function ou(i,e,t,n,s){let r=(n-e)*.5,a=(s-t)*.5,o=i*i,l=i*o;return(2*t-2*n+r+a)*l+(-3*t+3*n-2*r-a)*o+r*i+t}function Id(i,e){let t=1-i;return t*t*e}function Ld(i,e){return 2*(1-i)*i*e}function Nd(i,e){return i*i*e}function er(i,e,t,n){return Id(i,e)+Ld(i,t)+Nd(i,n)}function Dd(i,e){let t=1-i;return t*t*t*e}function Ud(i,e){let t=1-i;return 3*t*t*i*e}function Fd(i,e){return 3*(1-i)*i*i*e}function kd(i,e){return i*i*i*e}function tr(i,e,t,n,s){return Dd(i,e)+Ud(i,t)+Fd(i,n)+kd(i,s)}var Wa=class extends An{constructor(e=new De,t=new De,n=new De,s=new De){super(),this.isCubicBezierCurve=!0,this.type="CubicBezierCurve",this.v0=e,this.v1=t,this.v2=n,this.v3=s}getPoint(e,t=new De){let n=t,s=this.v0,r=this.v1,a=this.v2,o=this.v3;return n.set(tr(e,s.x,r.x,a.x,o.x),tr(e,s.y,r.y,a.y,o.y)),n}copy(e){return super.copy(e),this.v0.copy(e.v0),this.v1.copy(e.v1),this.v2.copy(e.v2),this.v3.copy(e.v3),this}toJSON(){let e=super.toJSON();return e.v0=this.v0.toArray(),e.v1=this.v1.toArray(),e.v2=this.v2.toArray(),e.v3=this.v3.toArray(),e}fromJSON(e){return super.fromJSON(e),this.v0.fromArray(e.v0),this.v1.fromArray(e.v1),this.v2.fromArray(e.v2),this.v3.fromArray(e.v3),this}},qa=class extends An{constructor(e=new U,t=new U,n=new U,s=new U){super(),this.isCubicBezierCurve3=!0,this.type="CubicBezierCurve3",this.v0=e,this.v1=t,this.v2=n,this.v3=s}getPoint(e,t=new U){let n=t,s=this.v0,r=this.v1,a=this.v2,o=this.v3;return n.set(tr(e,s.x,r.x,a.x,o.x),tr(e,s.y,r.y,a.y,o.y),tr(e,s.z,r.z,a.z,o.z)),n}copy(e){return super.copy(e),this.v0.copy(e.v0),this.v1.copy(e.v1),this.v2.copy(e.v2),this.v3.copy(e.v3),this}toJSON(){let e=super.toJSON();return e.v0=this.v0.toArray(),e.v1=this.v1.toArray(),e.v2=this.v2.toArray(),e.v3=this.v3.toArray(),e}fromJSON(e){return super.fromJSON(e),this.v0.fromArray(e.v0),this.v1.fromArray(e.v1),this.v2.fromArray(e.v2),this.v3.fromArray(e.v3),this}},Xa=class extends An{constructor(e=new De,t=new De){super(),this.isLineCurve=!0,this.type="LineCurve",this.v1=e,this.v2=t}getPoint(e,t=new De){let n=t;return e===1?n.copy(this.v2):(n.copy(this.v2).sub(this.v1),n.multiplyScalar(e).add(this.v1)),n}getPointAt(e,t){return this.getPoint(e,t)}getTangent(e,t=new De){return t.subVectors(this.v2,this.v1).normalize()}getTangentAt(e,t){return this.getTangent(e,t)}copy(e){return super.copy(e),this.v1.copy(e.v1),this.v2.copy(e.v2),this}toJSON(){let e=super.toJSON();return e.v1=this.v1.toArray(),e.v2=this.v2.toArray(),e}fromJSON(e){return super.fromJSON(e),this.v1.fromArray(e.v1),this.v2.fromArray(e.v2),this}},$a=class extends An{constructor(e=new U,t=new U){super(),this.isLineCurve3=!0,this.type="LineCurve3",this.v1=e,this.v2=t}getPoint(e,t=new U){let n=t;return e===1?n.copy(this.v2):(n.copy(this.v2).sub(this.v1),n.multiplyScalar(e).add(this.v1)),n}getPointAt(e,t){return this.getPoint(e,t)}getTangent(e,t=new U){return t.subVectors(this.v2,this.v1).normalize()}getTangentAt(e,t){return this.getTangent(e,t)}copy(e){return super.copy(e),this.v1.copy(e.v1),this.v2.copy(e.v2),this}toJSON(){let e=super.toJSON();return e.v1=this.v1.toArray(),e.v2=this.v2.toArray(),e}fromJSON(e){return super.fromJSON(e),this.v1.fromArray(e.v1),this.v2.fromArray(e.v2),this}},Ya=class extends An{constructor(e=new De,t=new De,n=new De){super(),this.isQuadraticBezierCurve=!0,this.type="QuadraticBezierCurve",this.v0=e,this.v1=t,this.v2=n}getPoint(e,t=new De){let n=t,s=this.v0,r=this.v1,a=this.v2;return n.set(er(e,s.x,r.x,a.x),er(e,s.y,r.y,a.y)),n}copy(e){return super.copy(e),this.v0.copy(e.v0),this.v1.copy(e.v1),this.v2.copy(e.v2),this}toJSON(){let e=super.toJSON();return e.v0=this.v0.toArray(),e.v1=this.v1.toArray(),e.v2=this.v2.toArray(),e}fromJSON(e){return super.fromJSON(e),this.v0.fromArray(e.v0),this.v1.fromArray(e.v1),this.v2.fromArray(e.v2),this}},Vi=class extends An{constructor(e=new U,t=new U,n=new U){super(),this.isQuadraticBezierCurve3=!0,this.type="QuadraticBezierCurve3",this.v0=e,this.v1=t,this.v2=n}getPoint(e,t=new U){let n=t,s=this.v0,r=this.v1,a=this.v2;return n.set(er(e,s.x,r.x,a.x),er(e,s.y,r.y,a.y),er(e,s.z,r.z,a.z)),n}copy(e){return super.copy(e),this.v0.copy(e.v0),this.v1.copy(e.v1),this.v2.copy(e.v2),this}toJSON(){let e=super.toJSON();return e.v0=this.v0.toArray(),e.v1=this.v1.toArray(),e.v2=this.v2.toArray(),e}fromJSON(e){return super.fromJSON(e),this.v0.fromArray(e.v0),this.v1.fromArray(e.v1),this.v2.fromArray(e.v2),this}},Za=class extends An{constructor(e=[]){super(),this.isSplineCurve=!0,this.type="SplineCurve",this.points=e}getPoint(e,t=new De){let n=t,s=this.points,r=(s.length-1)*e,a=Math.floor(r),o=r-a,l=s[a===0?a:a-1],c=s[a],h=s[a>s.length-2?s.length-1:a+1],f=s[a>s.length-3?s.length-1:a+2];return n.set(ou(o,l.x,c.x,h.x,f.x),ou(o,l.y,c.y,h.y,f.y)),n}copy(e){super.copy(e),this.points=[];for(let t=0,n=e.points.length;t<n;t++){let s=e.points[t];this.points.push(s.clone())}return this}toJSON(){let e=super.toJSON();e.points=[];for(let t=0,n=this.points.length;t<n;t++){let s=this.points[t];e.points.push(s.toArray())}return e}fromJSON(e){super.fromJSON(e),this.points=[];for(let t=0,n=e.points.length;t<n;t++){let s=e.points[t];this.points.push(new De().fromArray(s))}return this}},Od=Object.freeze({__proto__:null,ArcCurve:Ga,CatmullRomCurve3:Ts,CubicBezierCurve:Wa,CubicBezierCurve3:qa,EllipseCurve:xr,LineCurve:Xa,LineCurve3:$a,QuadraticBezierCurve:Ya,QuadraticBezierCurve3:Vi,SplineCurve:Za});var Es=class i extends Ss{constructor(e=1,t=0){let n=(1+Math.sqrt(5))/2,s=[-1,n,0,1,n,0,-1,-n,0,1,-n,0,0,-1,n,0,1,n,0,-1,-n,0,1,-n,n,0,-1,n,0,1,-n,0,-1,-n,0,1],r=[0,11,5,0,5,1,0,1,7,0,7,10,0,10,11,1,5,9,5,11,4,11,10,2,10,7,6,7,1,8,3,9,4,3,4,2,3,2,6,3,6,8,3,8,9,4,9,5,2,4,11,6,2,10,8,6,7,9,8,1];super(s,r,e,t),this.type="IcosahedronGeometry",this.parameters={radius:e,detail:t}}static fromJSON(e){return new i(e.radius,e.detail)}};var vr=class i extends Ss{constructor(e=1,t=0){let n=[1,0,0,-1,0,0,0,1,0,0,-1,0,0,0,1,0,0,-1],s=[0,2,4,0,4,3,0,3,5,0,5,2,1,2,5,1,5,3,1,3,4,1,4,2];super(n,s,e,t),this.type="OctahedronGeometry",this.parameters={radius:e,detail:t}}static fromJSON(e){return new i(e.radius,e.detail)}},yr=class i extends Rt{constructor(e=1,t=1,n=1,s=1){super(),this.type="PlaneGeometry",this.parameters={width:e,height:t,widthSegments:n,heightSegments:s};let r=e/2,a=t/2,o=Math.floor(n),l=Math.floor(s),c=o+1,h=l+1,f=e/o,u=t/l,d=[],g=[],b=[],m=[];for(let p=0;p<h;p++){let E=p*u-a;for(let C=0;C<c;C++){let y=C*f-r;g.push(y,-E,0),b.push(0,0,1),m.push(C/o),m.push(1-p/l)}}for(let p=0;p<l;p++)for(let E=0;E<o;E++){let C=E+c*p,y=E+c*(p+1),w=E+1+c*(p+1),T=E+1+c*p;d.push(C,y,T),d.push(y,w,T)}this.setIndex(d),this.setAttribute("position",new yt(g,3)),this.setAttribute("normal",new yt(b,3)),this.setAttribute("uv",new yt(m,2))}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}static fromJSON(e){return new i(e.width,e.height,e.widthSegments,e.heightSegments)}};var _n=class i extends Rt{constructor(e=1,t=32,n=16,s=0,r=Math.PI*2,a=0,o=Math.PI){super(),this.type="SphereGeometry",this.parameters={radius:e,widthSegments:t,heightSegments:n,phiStart:s,phiLength:r,thetaStart:a,thetaLength:o},t=Math.max(3,Math.floor(t)),n=Math.max(2,Math.floor(n));let l=Math.min(a+o,Math.PI),c=0,h=[],f=new U,u=new U,d=[],g=[],b=[],m=[];for(let p=0;p<=n;p++){let E=[],C=p/n,y=a+C*o,w=e*Math.cos(y),T=Math.sqrt(e*e-w*w),I=0;p===0&&a===0?I=.5/t:p===n&&l===Math.PI&&(I=-.5/t);for(let x=0;x<=t;x++){let A=x/t,D=s+A*r;f.x=-T*Math.cos(D),f.y=w,f.z=T*Math.sin(D),g.push(f.x,f.y,f.z),u.copy(f).normalize(),b.push(u.x,u.y,u.z),m.push(A+I,1-C),E.push(c++)}h.push(E)}for(let p=0;p<n;p++)for(let E=0;E<t;E++){let C=h[p][E+1],y=h[p][E],w=h[p+1][E],T=h[p+1][E+1];(p!==0||a>0)&&d.push(C,y,T),(p!==n-1||l<Math.PI)&&d.push(y,w,T)}this.setIndex(d),this.setAttribute("position",new yt(g,3)),this.setAttribute("normal",new yt(b,3)),this.setAttribute("uv",new yt(m,2))}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}static fromJSON(e){return new i(e.radius,e.widthSegments,e.heightSegments,e.phiStart,e.phiLength,e.thetaStart,e.thetaLength)}};var Cn=class i extends Rt{constructor(e=1,t=.4,n=12,s=48,r=Math.PI*2,a=0,o=Math.PI*2){super(),this.type="TorusGeometry",this.parameters={radius:e,tube:t,radialSegments:n,tubularSegments:s,arc:r,thetaStart:a,thetaLength:o},n=Math.floor(n),s=Math.floor(s);let l=[],c=[],h=[],f=[],u=new U,d=new U,g=new U;for(let b=0;b<=n;b++){let m=a+b/n*o;for(let p=0;p<=s;p++){let E=p/s*r;d.x=(e+t*Math.cos(m))*Math.cos(E),d.y=(e+t*Math.cos(m))*Math.sin(E),d.z=t*Math.sin(m),c.push(d.x,d.y,d.z),u.x=e*Math.cos(E),u.y=e*Math.sin(E),g.subVectors(d,u).normalize(),h.push(g.x,g.y,g.z),f.push(p/s),f.push(b/n)}}for(let b=1;b<=n;b++)for(let m=1;m<=s;m++){let p=(s+1)*b+m-1,E=(s+1)*(b-1)+m-1,C=(s+1)*(b-1)+m,y=(s+1)*b+m;l.push(p,E,y),l.push(E,C,y)}this.setIndex(l),this.setAttribute("position",new yt(c,3)),this.setAttribute("normal",new yt(h,3)),this.setAttribute("uv",new yt(f,2))}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}static fromJSON(e){return new i(e.radius,e.tube,e.radialSegments,e.tubularSegments,e.arc,e.thetaStart,e.thetaLength)}};var br=class i extends Rt{constructor(e=new Vi(new U(-1,-1,0),new U(-1,1,0),new U(1,1,0)),t=64,n=1,s=8,r=!1){super(),this.type="TubeGeometry",this.parameters={path:e,tubularSegments:t,radius:n,radialSegments:s,closed:r};let a=e.computeFrenetFrames(t,r);this.tangents=a.tangents,this.normals=a.normals,this.binormals=a.binormals;let o=new U,l=new U,c=new De,h=new U,f=[],u=[],d=[],g=[];b(),this.setIndex(g),this.setAttribute("position",new yt(f,3)),this.setAttribute("normal",new yt(u,3)),this.setAttribute("uv",new yt(d,2));function b(){for(let C=0;C<t;C++)m(C);m(r===!1?t:0),E(),p()}function m(C){h=e.getPointAt(C/t,h);let y=a.normals[C],w=a.binormals[C];for(let T=0;T<=s;T++){let I=T/s*Math.PI*2,x=Math.sin(I),A=-Math.cos(I);l.x=A*y.x+x*w.x,l.y=A*y.y+x*w.y,l.z=A*y.z+x*w.z,l.normalize(),u.push(l.x,l.y,l.z),o.x=h.x+n*l.x,o.y=h.y+n*l.y,o.z=h.z+n*l.z,f.push(o.x,o.y,o.z)}}function p(){for(let C=1;C<=t;C++)for(let y=1;y<=s;y++){let w=(s+1)*(C-1)+(y-1),T=(s+1)*C+(y-1),I=(s+1)*C+y,x=(s+1)*(C-1)+y;g.push(w,T,x),g.push(T,I,x)}}function E(){for(let C=0;C<=t;C++)for(let y=0;y<=s;y++)c.x=C/t,c.y=y/s,d.push(c.x,c.y)}}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}toJSON(){let e=super.toJSON();return e.path=this.parameters.path.toJSON(),e}static fromJSON(e){return new i(new Od[e.path.type]().fromJSON(e.path),e.tubularSegments,e.radius,e.radialSegments,e.closed)}};function $i(i){let e={};for(let t in i){e[t]={};for(let n in i[t]){let s=i[t][n];if(lu(s))s.isRenderTargetTexture?(je("UniformsUtils: Textures of render targets cannot be cloned via cloneUniforms() or mergeUniforms()."),e[t][n]=null):e[t][n]=s.clone();else if(Array.isArray(s))if(lu(s[0])){let r=[];for(let a=0,o=s.length;a<o;a++)r[a]=s[a].clone();e[t][n]=r}else e[t][n]=s.slice();else e[t][n]=s}}return e}function on(i){let e={};for(let t=0;t<i.length;t++){let n=$i(i[t]);for(let s in n)e[s]=n[s]}return e}function lu(i){return i&&(i.isColor||i.isMatrix3||i.isMatrix4||i.isVector2||i.isVector3||i.isVector4||i.isTexture||i.isQuaternion)}function Bd(i){let e=[];for(let t=0;t<i.length;t++)e.push(i[t].clone());return e}function fc(i){let e=i.getRenderTarget();return e===null?i.outputColorSpace:e.isXRRenderTarget===!0?e.texture.colorSpace:pt.workingColorSpace}var ci={clone:$i,merge:on},zd=`void main() {
	gl_Position = projectionMatrix * modelViewMatrix * vec4( position, 1.0 );
}`,Vd=`void main() {
	gl_FragColor = vec4( 1.0, 0.0, 0.0, 1.0 );
}`,kt=class extends On{constructor(e){super(),this.isShaderMaterial=!0,this.type="ShaderMaterial",this.defines={},this.uniforms={},this.uniformsGroups=[],this.vertexShader=zd,this.fragmentShader=Vd,this.linewidth=1,this.wireframe=!1,this.wireframeLinewidth=1,this.fog=!1,this.lights=!1,this.clipping=!1,this.forceSinglePass=!0,this.extensions={clipCullDistance:!1,multiDraw:!1},this.defaultAttributeValues={color:[1,1,1],uv:[0,0],uv1:[0,0]},this.index0AttributeName=void 0,this.uniformsNeedUpdate=!1,this.glslVersion=null,e!==void 0&&this.setValues(e)}copy(e){return super.copy(e),this.fragmentShader=e.fragmentShader,this.vertexShader=e.vertexShader,this.uniforms=$i(e.uniforms),this.uniformsGroups=Bd(e.uniformsGroups),this.defines=Object.assign({},e.defines),this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this.fog=e.fog,this.lights=e.lights,this.clipping=e.clipping,this.extensions=Object.assign({},e.extensions),this.glslVersion=e.glslVersion,this.defaultAttributeValues=Object.assign({},e.defaultAttributeValues),this.index0AttributeName=e.index0AttributeName,this.uniformsNeedUpdate=e.uniformsNeedUpdate,this}toJSON(e){let t=super.toJSON(e);t.glslVersion=this.glslVersion,t.uniforms={};for(let s in this.uniforms){let a=this.uniforms[s].value;a&&a.isTexture?t.uniforms[s]={type:"t",value:a.toJSON(e).uuid}:a&&a.isColor?t.uniforms[s]={type:"c",value:a.getHex()}:a&&a.isVector2?t.uniforms[s]={type:"v2",value:a.toArray()}:a&&a.isVector3?t.uniforms[s]={type:"v3",value:a.toArray()}:a&&a.isVector4?t.uniforms[s]={type:"v4",value:a.toArray()}:a&&a.isMatrix3?t.uniforms[s]={type:"m3",value:a.toArray()}:a&&a.isMatrix4?t.uniforms[s]={type:"m4",value:a.toArray()}:t.uniforms[s]={value:a}}Object.keys(this.defines).length>0&&(t.defines=this.defines),t.vertexShader=this.vertexShader,t.fragmentShader=this.fragmentShader,t.lights=this.lights,t.clipping=this.clipping;let n={};for(let s in this.extensions)this.extensions[s]===!0&&(n[s]=!0);return Object.keys(n).length>0&&(t.extensions=n),t}fromJSON(e,t){if(super.fromJSON(e,t),e.uniforms!==void 0)for(let n in e.uniforms){let s=e.uniforms[n];switch(this.uniforms[n]={},s.type){case"t":this.uniforms[n].value=t[s.value]||null;break;case"c":this.uniforms[n].value=new Qe().setHex(s.value);break;case"v2":this.uniforms[n].value=new De().fromArray(s.value);break;case"v3":this.uniforms[n].value=new U().fromArray(s.value);break;case"v4":this.uniforms[n].value=new Ut().fromArray(s.value);break;case"m3":this.uniforms[n].value=new st().fromArray(s.value);break;case"m4":this.uniforms[n].value=new xt().fromArray(s.value);break;default:this.uniforms[n].value=s.value}}if(e.defines!==void 0&&(this.defines=e.defines),e.vertexShader!==void 0&&(this.vertexShader=e.vertexShader),e.fragmentShader!==void 0&&(this.fragmentShader=e.fragmentShader),e.glslVersion!==void 0&&(this.glslVersion=e.glslVersion),e.extensions!==void 0)for(let n in e.extensions)this.extensions[n]=e.extensions[n];return e.lights!==void 0&&(this.lights=e.lights),e.clipping!==void 0&&(this.clipping=e.clipping),this}},ws=class extends kt{constructor(e){super(e),this.isRawShaderMaterial=!0,this.type="RawShaderMaterial"}},Zt=class extends On{constructor(e){super(),this.isMeshStandardMaterial=!0,this.type="MeshStandardMaterial",this.defines={STANDARD:""},this.color=new Qe(16777215),this.roughness=1,this.metalness=0,this.map=null,this.lightMap=null,this.lightMapIntensity=1,this.aoMap=null,this.aoMapIntensity=1,this.emissive=new Qe(0),this.emissiveIntensity=1,this.emissiveMap=null,this.bumpMap=null,this.bumpScale=1,this.normalMap=null,this.normalMapType=Wr,this.normalScale=new De(1,1),this.displacementMap=null,this.displacementScale=1,this.displacementBias=0,this.roughnessMap=null,this.metalnessMap=null,this.alphaMap=null,this.envMap=null,this.envMapRotation=new wn,this.envMapIntensity=1,this.wireframe=!1,this.wireframeLinewidth=1,this.wireframeLinecap="round",this.wireframeLinejoin="round",this.flatShading=!1,this.fog=!0,this.setValues(e)}copy(e){return super.copy(e),this.defines={STANDARD:""},this.color.copy(e.color),this.roughness=e.roughness,this.metalness=e.metalness,this.map=e.map,this.lightMap=e.lightMap,this.lightMapIntensity=e.lightMapIntensity,this.aoMap=e.aoMap,this.aoMapIntensity=e.aoMapIntensity,this.emissive.copy(e.emissive),this.emissiveMap=e.emissiveMap,this.emissiveIntensity=e.emissiveIntensity,this.bumpMap=e.bumpMap,this.bumpScale=e.bumpScale,this.normalMap=e.normalMap,this.normalMapType=e.normalMapType,this.normalScale.copy(e.normalScale),this.displacementMap=e.displacementMap,this.displacementScale=e.displacementScale,this.displacementBias=e.displacementBias,this.roughnessMap=e.roughnessMap,this.metalnessMap=e.metalnessMap,this.alphaMap=e.alphaMap,this.envMap=e.envMap,this.envMapRotation.copy(e.envMapRotation),this.envMapIntensity=e.envMapIntensity,this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this.wireframeLinecap=e.wireframeLinecap,this.wireframeLinejoin=e.wireframeLinejoin,this.flatShading=e.flatShading,this.fog=e.fog,this}};var Mr=class extends On{constructor(e){super(),this.isMeshLambertMaterial=!0,this.type="MeshLambertMaterial",this.color=new Qe(16777215),this.map=null,this.lightMap=null,this.lightMapIntensity=1,this.aoMap=null,this.aoMapIntensity=1,this.emissive=new Qe(0),this.emissiveIntensity=1,this.emissiveMap=null,this.bumpMap=null,this.bumpScale=1,this.normalMap=null,this.normalMapType=Wr,this.normalScale=new De(1,1),this.displacementMap=null,this.displacementScale=1,this.displacementBias=0,this.specularMap=null,this.alphaMap=null,this.envMap=null,this.envMapRotation=new wn,this.combine=uo,this.reflectivity=1,this.envMapIntensity=1,this.refractionRatio=.98,this.wireframe=!1,this.wireframeLinewidth=1,this.wireframeLinecap="round",this.wireframeLinejoin="round",this.flatShading=!1,this.fog=!0,this.setValues(e)}copy(e){return super.copy(e),this.color.copy(e.color),this.map=e.map,this.lightMap=e.lightMap,this.lightMapIntensity=e.lightMapIntensity,this.aoMap=e.aoMap,this.aoMapIntensity=e.aoMapIntensity,this.emissive.copy(e.emissive),this.emissiveMap=e.emissiveMap,this.emissiveIntensity=e.emissiveIntensity,this.bumpMap=e.bumpMap,this.bumpScale=e.bumpScale,this.normalMap=e.normalMap,this.normalMapType=e.normalMapType,this.normalScale.copy(e.normalScale),this.displacementMap=e.displacementMap,this.displacementScale=e.displacementScale,this.displacementBias=e.displacementBias,this.specularMap=e.specularMap,this.alphaMap=e.alphaMap,this.envMap=e.envMap,this.envMapRotation.copy(e.envMapRotation),this.combine=e.combine,this.reflectivity=e.reflectivity,this.envMapIntensity=e.envMapIntensity,this.refractionRatio=e.refractionRatio,this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this.wireframeLinecap=e.wireframeLinecap,this.wireframeLinejoin=e.wireframeLinejoin,this.flatShading=e.flatShading,this.fog=e.fog,this}},ja=class extends On{constructor(e){super(),this.isMeshDepthMaterial=!0,this.type="MeshDepthMaterial",this.depthPacking=zu,this.map=null,this.alphaMap=null,this.displacementMap=null,this.displacementScale=1,this.displacementBias=0,this.wireframe=!1,this.wireframeLinewidth=1,this.setValues(e)}copy(e){return super.copy(e),this.depthPacking=e.depthPacking,this.map=e.map,this.alphaMap=e.alphaMap,this.displacementMap=e.displacementMap,this.displacementScale=e.displacementScale,this.displacementBias=e.displacementBias,this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this}},Ja=class extends On{constructor(e){super(),this.isMeshDistanceMaterial=!0,this.type="MeshDistanceMaterial",this.map=null,this.alphaMap=null,this.displacementMap=null,this.displacementScale=1,this.displacementBias=0,this.setValues(e)}copy(e){return super.copy(e),this.map=e.map,this.alphaMap=e.alphaMap,this.displacementMap=e.displacementMap,this.displacementScale=e.displacementScale,this.displacementBias=e.displacementBias,this}};function cs(i,e){return!i||i.constructor===e?i:typeof e.BYTES_PER_ELEMENT=="number"?new e(i):Array.prototype.slice.call(i)}function Ol(i){return i!==void 0&&i.inTangents!==void 0&&i.outTangents!==void 0}var yi=class{constructor(e,t,n,s){this.parameterPositions=e,this._cachedIndex=0,this.resultBuffer=s!==void 0?s:new t.constructor(n),this.sampleValues=t,this.valueSize=n,this.settings=null,this.DefaultSettings_={}}evaluate(e){let t=this.parameterPositions,n=this._cachedIndex,s=t[n],r=t[n-1];n:{e:{let a;t:{i:if(!(e<s)){for(let o=n+2;;){if(s===void 0){if(e<r)break i;return n=t.length,this._cachedIndex=n,this.copySampleValue_(n-1)}if(n===o)break;if(r=s,s=t[++n],e<s)break e}a=t.length;break t}if(!(e>=r)){let o=t[1];e<o&&(n=2,r=o);for(let l=n-2;;){if(r===void 0)return this._cachedIndex=0,this.copySampleValue_(0);if(n===l)break;if(s=r,r=t[--n-1],e>=r)break e}a=n,n=0;break t}break n}for(;n<a;){let o=n+a>>>1;e<t[o]?a=o:n=o+1}if(s=t[n],r=t[n-1],r===void 0)return this._cachedIndex=0,this.copySampleValue_(0);if(s===void 0)return n=t.length,this._cachedIndex=n,this.copySampleValue_(n-1)}this._cachedIndex=n,this.intervalChanged_(n,r,s)}return this.interpolate_(n,r,e,s)}getSettings_(){return this.settings||this.DefaultSettings_}copySampleValue_(e){let t=this.resultBuffer,n=this.sampleValues,s=this.valueSize,r=e*s;for(let a=0;a!==s;++a)t[a]=n[r+a];return t}interpolate_(){throw new Error("THREE.Interpolant: Call to abstract method.")}intervalChanged_(){}},Ka=class extends yi{constructor(e,t,n,s){super(e,t,n,s),this._weightPrev=-0,this._offsetPrev=-0,this._weightNext=-0,this._offsetNext=-0,this.DefaultSettings_={endingStart:Vl,endingEnd:Vl}}intervalChanged_(e,t,n){let s=this.parameterPositions,r=e-2,a=e+1,o=s[r],l=s[a];if(o===void 0)switch(this.getSettings_().endingStart){case Hl:r=e,o=2*t-n;break;case Gl:r=s.length-2,o=t+s[r]-s[r+1];break;default:r=e,o=n}if(l===void 0)switch(this.getSettings_().endingEnd){case Hl:a=e,l=2*n-t;break;case Gl:a=1,l=n+s[1]-s[0];break;default:a=e-1,l=t}let c=(n-t)*.5,h=this.valueSize;this._weightPrev=c/(t-o),this._weightNext=c/(l-n),this._offsetPrev=r*h,this._offsetNext=a*h}interpolate_(e,t,n,s){let r=this.resultBuffer,a=this.sampleValues,o=this.valueSize,l=e*o,c=l-o,h=this._offsetPrev,f=this._offsetNext,u=this._weightPrev,d=this._weightNext,g=(n-t)/(s-t),b=g*g,m=b*g,p=-u*m+2*u*b-u*g,E=(1+u)*m+(-1.5-2*u)*b+(-.5+u)*g+1,C=(-1-d)*m+(1.5+d)*b+.5*g,y=d*m-d*b;for(let w=0;w!==o;++w)r[w]=p*a[h+w]+E*a[c+w]+C*a[l+w]+y*a[f+w];return r}},Qa=class extends yi{constructor(e,t,n,s){super(e,t,n,s)}interpolate_(e,t,n,s){let r=this.resultBuffer,a=this.sampleValues,o=this.valueSize,l=e*o,c=l-o,h=(n-t)/(s-t),f=1-h;for(let u=0;u!==o;++u)r[u]=a[c+u]*f+a[l+u]*h;return r}},eo=class extends yi{constructor(e,t,n,s){super(e,t,n,s)}interpolate_(e){return this.copySampleValue_(e-1)}},to=class extends yi{interpolate_(e,t,n,s){let r=this.resultBuffer,a=this.sampleValues,o=this.valueSize,l=e*o,c=l-o,h=this.inTangents,f=this.outTangents;if(!h||!f){let g=(n-t)/(s-t),b=1-g;for(let m=0;m!==o;++m)r[m]=a[c+m]*b+a[l+m]*g;return r}let u=o*2,d=e-1;for(let g=0;g!==o;++g){let b=a[c+g],m=a[l+g],p=d*u+g*2,E=f[p],C=f[p+1],y=e*u+g*2,w=h[y],T=h[y+1],I=Gd(n,t,E,w,s);r[g]=th(I,b,C,T,m)}return r}};function th(i,e,t,n,s){let r=1-i;return r*r*r*e+3*r*r*i*t+3*r*i*i*n+i*i*i*s}function Hd(i,e,t,n,s){let r=1-i;return 3*r*r*(t-e)+6*r*i*(n-t)+3*i*i*(s-n)}function Gd(i,e,t,n,s){let r=(i-e)/(s-e);for(let a=0;a<8;a++){let o=th(r,e,t,n,s)-i;if(Math.abs(o)<1e-10)break;let l=Hd(r,e,t,n,s);if(Math.abs(l)<1e-10)break;r=Math.max(0,Math.min(1,r-o/l))}return r}var Mn=class{constructor(e,t,n,s){if(e===void 0)throw new Error("THREE.KeyframeTrack: track name is undefined");if(t===void 0||t.length===0)throw new Error("THREE.KeyframeTrack: no keyframes in track named "+e);this.name=e,this.times=cs(t,this.TimeBufferType),this.values=cs(n,this.ValueBufferType),this.setInterpolation(s||this.DefaultInterpolation)}static toJSON(e){let t=e.constructor,n;if(t.toJSON!==this.toJSON)n=t.toJSON(e);else{n={name:e.name,times:cs(e.times,Array),values:cs(e.values,Array)};let s=e.getInterpolation();s!==e.DefaultInterpolation&&(n.interpolation=s),Ol(e.settings)&&(n.settings={inTangents:cs(e.settings.inTangents,Array),outTangents:cs(e.settings.outTangents,Array)})}return n.type=e.ValueTypeName,n}InterpolantFactoryMethodDiscrete(e){return new eo(this.times,this.values,this.getValueSize(),e)}InterpolantFactoryMethodLinear(e){return new Qa(this.times,this.values,this.getValueSize(),e)}InterpolantFactoryMethodSmooth(e){return new Ka(this.times,this.values,this.getValueSize(),e)}InterpolantFactoryMethodBezier(e){let t=new to(this.times,this.values,this.getValueSize(),e);return this.settings&&(t.inTangents=this.settings.inTangents,t.outTangents=this.settings.outTangents),t}setInterpolation(e){let t;switch(e){case nr:t=this.InterpolantFactoryMethodDiscrete;break;case Fa:t=this.InterpolantFactoryMethodLinear;break;case Ea:t=this.InterpolantFactoryMethodSmooth;break;case zl:t=this.InterpolantFactoryMethodBezier;break}if(t===void 0){let n="unsupported interpolation for "+this.ValueTypeName+" keyframe track named "+this.name;if(this.createInterpolant===void 0)if(e!==this.DefaultInterpolation)this.setInterpolation(this.DefaultInterpolation);else throw new Error(n);return je("KeyframeTrack:",n),this}return this.createInterpolant=t,this}getInterpolation(){switch(this.createInterpolant){case this.InterpolantFactoryMethodDiscrete:return nr;case this.InterpolantFactoryMethodLinear:return Fa;case this.InterpolantFactoryMethodSmooth:return Ea;case this.InterpolantFactoryMethodBezier:return zl}}getValueSize(){return this.values.length/this.times.length}shift(e){if(e!==0){let t=this.times;for(let n=0,s=t.length;n!==s;++n)t[n]+=e}return this}scale(e){if(e!==1){let t=this.times;for(let n=0,s=t.length;n!==s;++n)t[n]*=e;Ol(this.settings)&&(cu(this.settings.inTangents,e),cu(this.settings.outTangents,e))}return this}trim(e,t){let n=this.times,s=n.length,r=0,a=s-1;for(;r!==s&&n[r]<e;)++r;for(;a!==-1&&n[a]>t;)--a;if(++a,r!==0||a!==s){r>=a&&(a=Math.max(a,1),r=a-1);let o=this.getValueSize();this.times=n.slice(r,a),this.values=this.values.slice(r*o,a*o)}return this}validate(){let e=!0,t=this.getValueSize();t-Math.floor(t)!==0&&(nt("KeyframeTrack: Invalid value size in track.",this),e=!1);let n=this.times,s=this.values,r=n.length;r===0&&(nt("KeyframeTrack: Track is empty.",this),e=!1);let a=null;for(let o=0;o!==r;o++){let l=n[o];if(typeof l=="number"&&isNaN(l)){nt("KeyframeTrack: Time is not a valid number.",this,o,l),e=!1;break}if(a!==null&&a>l){nt("KeyframeTrack: Out of order keys.",this,o,l,a),e=!1;break}a=l}if(s!==void 0&&Zh(s))for(let o=0,l=s.length;o!==l;++o){let c=s[o];if(isNaN(c)){nt("KeyframeTrack: Value is not a valid number.",this,o,c),e=!1;break}}return e}optimize(){let e=this.times.slice(),t=this.values.slice(),n=this.getValueSize(),s=this.getInterpolation()===Ea,r=e.length-1,a=1;for(let o=1;o<r;++o){let l=!1,c=e[o],h=e[o+1];if(c!==h&&(o!==1||c!==e[0]))if(s)l=!0;else{let f=o*n,u=f-n,d=f+n;for(let g=0;g!==n;++g){let b=t[f+g];if(b!==t[u+g]||b!==t[d+g]){l=!0;break}}}if(l){if(o!==a){e[a]=e[o];let f=o*n,u=a*n;for(let d=0;d!==n;++d)t[u+d]=t[f+d]}++a}}if(r>0){e[a]=e[r];for(let o=r*n,l=a*n,c=0;c!==n;++c)t[l+c]=t[o+c];++a}return a!==e.length?(this.times=e.slice(0,a),this.values=t.slice(0,a*n)):(this.times=e,this.values=t),this}clone(){let e=this.times.slice(),t=this.values.slice(),n=this.constructor,s=new n(this.name,e,t);return s.createInterpolant=this.createInterpolant,Ol(this.settings)&&(s.settings={inTangents:this.settings.inTangents.slice(),outTangents:this.settings.outTangents.slice()}),s}};function cu(i,e){for(let t=0,n=i.length;t!==n;t+=2)i[t]*=e}Mn.prototype.ValueTypeName="";Mn.prototype.TimeBufferType=Float32Array;Mn.prototype.ValueBufferType=Float32Array;Mn.prototype.DefaultInterpolation=Fa;var bi=class extends Mn{constructor(e,t,n){super(e,t,n)}};bi.prototype.ValueTypeName="bool";bi.prototype.ValueBufferType=Array;bi.prototype.DefaultInterpolation=nr;bi.prototype.InterpolantFactoryMethodLinear=void 0;bi.prototype.InterpolantFactoryMethodSmooth=void 0;var no=class extends Mn{constructor(e,t,n,s){super(e,t,n,s)}};no.prototype.ValueTypeName="color";var io=class extends Mn{constructor(e,t,n,s){super(e,t,n,s)}};io.prototype.ValueTypeName="number";var so=class extends yi{constructor(e,t,n,s){super(e,t,n,s)}interpolate_(e,t,n,s){let r=this.resultBuffer,a=this.sampleValues,o=this.valueSize,l=(n-t)/(s-t),c=e*o;for(let h=c+o;c!==h;c+=4)Gt.slerpFlat(r,0,a,c-o,a,c,l);return r}},Sr=class extends Mn{constructor(e,t,n,s){super(e,t,n,s)}InterpolantFactoryMethodLinear(e){return new so(this.times,this.values,this.getValueSize(),e)}};Sr.prototype.ValueTypeName="quaternion";Sr.prototype.InterpolantFactoryMethodSmooth=void 0;var Mi=class extends Mn{constructor(e,t,n){super(e,t,n)}};Mi.prototype.ValueTypeName="string";Mi.prototype.ValueBufferType=Array;Mi.prototype.DefaultInterpolation=nr;Mi.prototype.InterpolantFactoryMethodLinear=void 0;Mi.prototype.InterpolantFactoryMethodSmooth=void 0;var ro=class extends Mn{constructor(e,t,n,s){super(e,t,n,s)}};ro.prototype.ValueTypeName="vector";var ao=class{constructor(e,t,n){let s=this,r=!1,a=0,o=0,l,c=[];this.onStart=void 0,this.onLoad=e,this.onProgress=t,this.onError=n,this._abortController=null,this.itemStart=function(h){o++,r===!1&&s.onStart!==void 0&&s.onStart(h,a,o),r=!0},this.itemEnd=function(h){a++,s.onProgress!==void 0&&s.onProgress(h,a,o),a===o&&(r=!1,s.onLoad!==void 0&&s.onLoad())},this.itemError=function(h){s.onError!==void 0&&s.onError(h)},this.resolveURL=function(h){return h=h.normalize("NFC"),l?l(h):h},this.setURLModifier=function(h){return l=h,this},this.addHandler=function(h,f){return c.push(h,f),this},this.removeHandler=function(h){let f=c.indexOf(h);return f!==-1&&c.splice(f,2),this},this.getHandler=function(h){for(let f=0,u=c.length;f<u;f+=2){let d=c[f],g=c[f+1];if(d.global&&(d.lastIndex=0),d.test(h))return g}return null},this.abort=function(){return this.abortController.abort(),this._abortController=null,this}}get abortController(){return this._abortController||(this._abortController=new AbortController),this._abortController}},nh=new ao,oo=class{constructor(e){this.manager=e!==void 0?e:nh,this.crossOrigin="anonymous",this.withCredentials=!1,this.path="",this.resourcePath="",this.requestHeader={},typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("observe",{detail:this}))}load(){}loadAsync(e,t){let n=this;return new Promise(function(s,r){n.load(e,s,t,r)})}parse(){}setCrossOrigin(e){return this.crossOrigin=e,this}setWithCredentials(e){return this.withCredentials=e,this}setPath(e){return this.path=e,this}setResourcePath(e){return this.resourcePath=e,this}setRequestHeader(e){return this.requestHeader=e,this}abort(){return this}};oo.DEFAULT_MATERIAL_NAME="__DEFAULT";var As=class extends Ht{constructor(e,t=1){super(),this.isLight=!0,this.type="Light",this.color=new Qe(e),this.intensity=t}copy(e,t){return super.copy(e,t),this.color.copy(e.color),this.intensity=e.intensity,this}toJSON(e){let t=super.toJSON(e);return t.object.color=this.color.getHex(),t.object.intensity=this.intensity,t}},Tr=class extends As{constructor(e,t,n){super(e,n),this.isHemisphereLight=!0,this.type="HemisphereLight",this.position.copy(Ht.DEFAULT_UP),this.updateMatrix(),this.groundColor=new Qe(t)}copy(e,t){return super.copy(e,t),this.groundColor.copy(e.groundColor),this}toJSON(e){let t=super.toJSON(e);return t.object.groundColor=this.groundColor.getHex(),t}},Bl=new xt,uu=new U,hu=new U,Er=class{constructor(e){this.camera=e,this.intensity=1,this.bias=0,this.biasNode=null,this.normalBias=0,this.radius=1,this.blurSamples=8,this.mapSize=new De(512,512),this.mapType=xn,this.map=null,this.mapPass=null,this.matrix=new xt,this.autoUpdate=!0,this.needsUpdate=!1,this._frustum=new bs,this._frameExtents=new De(1,1),this._viewportCount=1,this._viewports=[new Ut(0,0,1,1)]}getViewportCount(){return this._viewportCount}getCamera(){return this.camera}getFrustum(){return this._frustum}updateMatrices(e){let t=this.camera;uu.setFromMatrixPosition(e.matrixWorld),t.position.copy(uu),hu.setFromMatrixPosition(e.target.matrixWorld),t.lookAt(hu),t.updateMatrixWorld(),this._updateMatrix(t,this.matrix,this._frustum)}_updateMatrix(e,t,n,s){Bl.multiplyMatrices(e.projectionMatrix,e.matrixWorldInverse),n.setFromProjectionMatrix(Bl,e.coordinateSystem,e.reversedDepth);let r=this._frameExtents,a=s?s.z/r.x:1,o=s?s.w/r.y:1,l=s?s.x/r.x:0,c=s?s.y/r.y:0;e.coordinateSystem===ms||e.reversedDepth?t.set(.5*a,0,0,.5*a+l,0,.5*o,0,.5*o+c,0,0,1,0,0,0,0,1):t.set(.5*a,0,0,.5*a+l,0,.5*o,0,.5*o+c,0,0,.5,.5,0,0,0,1),t.multiply(Bl)}getViewport(e){return this._viewports[e]}getFrameExtents(){return this._frameExtents}dispose(){this.map&&this.map.dispose(),this.mapPass&&this.mapPass.dispose()}copy(e){return this.camera=e.camera.clone(),this.intensity=e.intensity,this.bias=e.bias,this.radius=e.radius,this.autoUpdate=e.autoUpdate,this.needsUpdate=e.needsUpdate,this.normalBias=e.normalBias,this.blurSamples=e.blurSamples,this.mapSize.copy(e.mapSize),this.biasNode=e.biasNode,this}clone(){return new this.constructor().copy(this)}toJSON(){let e={};return e.intensity=this.intensity,e.bias=this.bias,e.normalBias=this.normalBias,e.radius=this.radius,e.blurSamples=this.blurSamples,e.mapSize=this.mapSize.toArray(),e.camera=this.camera.toJSON(!1).object,delete e.camera.matrix,e}},Sa=new U,Ta=new Gt,Wn=new U,wr=class extends Ht{constructor(){super(),this.isCamera=!0,this.type="Camera",this.matrixWorldInverse=new xt,this.projectionMatrix=new xt,this.projectionMatrixInverse=new xt,this.coordinateSystem=kn,this._reversedDepth=!1}get reversedDepth(){return this._reversedDepth}copy(e,t){return super.copy(e,t),this.matrixWorldInverse.copy(e.matrixWorldInverse),this.projectionMatrix.copy(e.projectionMatrix),this.projectionMatrixInverse.copy(e.projectionMatrixInverse),this.coordinateSystem=e.coordinateSystem,this}getWorldDirection(e){return super.getWorldDirection(e).negate()}updateMatrixWorld(e){super.updateMatrixWorld(e),this.matrixWorld.decompose(Sa,Ta,Wn),Wn.x===1&&Wn.y===1&&Wn.z===1?this.matrixWorldInverse.copy(this.matrixWorld).invert():this.matrixWorldInverse.compose(Sa,Ta,Wn.set(1,1,1)).invert()}updateWorldMatrix(e,t,n=!1){super.updateWorldMatrix(e,t,n),this.matrixWorld.decompose(Sa,Ta,Wn),Wn.x===1&&Wn.y===1&&Wn.z===1?this.matrixWorldInverse.copy(this.matrixWorld).invert():this.matrixWorldInverse.compose(Sa,Ta,Wn.set(1,1,1)).invert()}clone(){return new this.constructor().copy(this)}},_i=new U,du=new De,fu=new De,Jt=class extends wr{constructor(e=50,t=1,n=.1,s=2e3){super(),this.isPerspectiveCamera=!0,this.type="PerspectiveCamera",this.fov=e,this.zoom=1,this.near=n,this.far=s,this.focus=10,this.aspect=t,this.view=null,this.filmGauge=35,this.filmOffset=0,this.updateProjectionMatrix()}copy(e,t){return super.copy(e,t),this.fov=e.fov,this.zoom=e.zoom,this.near=e.near,this.far=e.far,this.focus=e.focus,this.aspect=e.aspect,this.view=e.view===null?null:Object.assign({},e.view),this.filmGauge=e.filmGauge,this.filmOffset=e.filmOffset,this}setFocalLength(e){let t=.5*this.getFilmHeight()/e;this.fov=_s*2*Math.atan(t),this.updateProjectionMatrix()}getFocalLength(){let e=Math.tan(Ks*.5*this.fov);return .5*this.getFilmHeight()/e}getEffectiveFOV(){return _s*2*Math.atan(Math.tan(Ks*.5*this.fov)/this.zoom)}getFilmWidth(){return this.filmGauge*Math.min(this.aspect,1)}getFilmHeight(){return this.filmGauge/Math.max(this.aspect,1)}getViewBounds(e,t,n){_i.set(-1,-1,.5).applyMatrix4(this.projectionMatrixInverse),t.set(_i.x,_i.y).multiplyScalar(-e/_i.z),_i.set(1,1,.5).applyMatrix4(this.projectionMatrixInverse),n.set(_i.x,_i.y).multiplyScalar(-e/_i.z)}getViewSize(e,t){return this.getViewBounds(e,du,fu),t.subVectors(fu,du)}setViewOffset(e,t,n,s,r,a){this.aspect=e/t,this.view===null&&(this.view={enabled:!0,fullWidth:1,fullHeight:1,offsetX:0,offsetY:0,width:1,height:1}),this.view.enabled=!0,this.view.fullWidth=e,this.view.fullHeight=t,this.view.offsetX=n,this.view.offsetY=s,this.view.width=r,this.view.height=a,this.updateProjectionMatrix()}clearViewOffset(){this.view!==null&&(this.view.enabled=!1),this.updateProjectionMatrix()}updateProjectionMatrix(){let e=this.near,t=e*Math.tan(Ks*.5*this.fov)/this.zoom,n=2*t,s=this.aspect*n,r=-.5*s,a=this.view;if(this.view!==null&&this.view.enabled){let l=a.fullWidth,c=a.fullHeight;r+=a.offsetX*s/l,t-=a.offsetY*n/c,s*=a.width/l,n*=a.height/c}let o=this.filmOffset;o!==0&&(r+=e*o/this.getFilmWidth()),this.projectionMatrix.makePerspective(r,r+s,t,t-n,e,this.far,this.coordinateSystem,this.reversedDepth),this.projectionMatrixInverse.copy(this.projectionMatrix).invert()}toJSON(e){let t=super.toJSON(e);return t.object.fov=this.fov,t.object.zoom=this.zoom,t.object.near=this.near,t.object.far=this.far,t.object.focus=this.focus,t.object.aspect=this.aspect,this.view!==null&&(t.object.view=Object.assign({},this.view)),t.object.filmGauge=this.filmGauge,t.object.filmOffset=this.filmOffset,t}};var ql=class extends Er{constructor(){super(new Jt(90,1,.5,500)),this.isPointLightShadow=!0}},oi=class extends As{constructor(e,t,n=0,s=2){super(e,t),this.isPointLight=!0,this.type="PointLight",this.distance=n,this.decay=s,this.shadow=new ql}get power(){return this.intensity*4*Math.PI}set power(e){this.intensity=e/(4*Math.PI)}dispose(){super.dispose(),this.shadow.dispose()}copy(e,t){return super.copy(e,t),this.distance=e.distance,this.decay=e.decay,this.shadow=e.shadow.clone(),this}toJSON(e){let t=super.toJSON(e);return t.object.distance=this.distance,t.object.decay=this.decay,t.object.shadow=this.shadow.toJSON(),t}},Si=class extends wr{constructor(e=-1,t=1,n=1,s=-1,r=.1,a=2e3){super(),this.isOrthographicCamera=!0,this.type="OrthographicCamera",this.zoom=1,this.view=null,this.left=e,this.right=t,this.top=n,this.bottom=s,this.near=r,this.far=a,this.updateProjectionMatrix()}copy(e,t){return super.copy(e,t),this.left=e.left,this.right=e.right,this.top=e.top,this.bottom=e.bottom,this.near=e.near,this.far=e.far,this.zoom=e.zoom,this.view=e.view===null?null:Object.assign({},e.view),this}setViewOffset(e,t,n,s,r,a){this.view===null&&(this.view={enabled:!0,fullWidth:1,fullHeight:1,offsetX:0,offsetY:0,width:1,height:1}),this.view.enabled=!0,this.view.fullWidth=e,this.view.fullHeight=t,this.view.offsetX=n,this.view.offsetY=s,this.view.width=r,this.view.height=a,this.updateProjectionMatrix()}clearViewOffset(){this.view!==null&&(this.view.enabled=!1),this.updateProjectionMatrix()}updateProjectionMatrix(){let e=(this.right-this.left)/(2*this.zoom),t=(this.top-this.bottom)/(2*this.zoom),n=(this.right+this.left)/2,s=(this.top+this.bottom)/2,r=n-e,a=n+e,o=s+t,l=s-t;if(this.view!==null&&this.view.enabled){let c=(this.right-this.left)/this.view.fullWidth/this.zoom,h=(this.top-this.bottom)/this.view.fullHeight/this.zoom;r+=c*this.view.offsetX,a=r+c*this.view.width,o-=h*this.view.offsetY,l=o-h*this.view.height}this.projectionMatrix.makeOrthographic(r,a,o,l,this.near,this.far,this.coordinateSystem,this.reversedDepth),this.projectionMatrixInverse.copy(this.projectionMatrix).invert()}toJSON(e){let t=super.toJSON(e);return t.object.zoom=this.zoom,t.object.left=this.left,t.object.right=this.right,t.object.top=this.top,t.object.bottom=this.bottom,t.object.near=this.near,t.object.far=this.far,this.view!==null&&(t.object.view=Object.assign({},this.view)),t}},Xl=class extends Er{constructor(){super(new Si(-5,5,5,-5,.5,500)),this.isDirectionalLightShadow=!0}},Hi=class extends As{constructor(e,t){super(e,t),this.isDirectionalLight=!0,this.type="DirectionalLight",this.position.copy(Ht.DEFAULT_UP),this.updateMatrix(),this.target=new Ht,this.shadow=new Xl}dispose(){super.dispose(),this.shadow.dispose()}copy(e){return super.copy(e),this.target=e.target.clone(),this.shadow=e.shadow.clone(),this}toJSON(e){let t=super.toJSON(e);return t.object.shadow=this.shadow.toJSON(),t.object.target=this.target.uuid,t}};var us=-90,hs=1,lo=class extends Ht{constructor(e,t,n){super(),this.type="CubeCamera",this.renderTarget=n,this.coordinateSystem=null,this.activeMipmapLevel=0;let s=new Jt(us,hs,e,t);s.layers=this.layers,this.add(s);let r=new Jt(us,hs,e,t);r.layers=this.layers,this.add(r);let a=new Jt(us,hs,e,t);a.layers=this.layers,this.add(a);let o=new Jt(us,hs,e,t);o.layers=this.layers,this.add(o);let l=new Jt(us,hs,e,t);l.layers=this.layers,this.add(l);let c=new Jt(us,hs,e,t);c.layers=this.layers,this.add(c)}updateCoordinateSystem(){let e=this.coordinateSystem,t=this.children.concat(),[n,s,r,a,o,l]=t;for(let c of t)this.remove(c);if(e===kn)n.up.set(0,1,0),n.lookAt(1,0,0),s.up.set(0,1,0),s.lookAt(-1,0,0),r.up.set(0,0,-1),r.lookAt(0,1,0),a.up.set(0,0,1),a.lookAt(0,-1,0),o.up.set(0,1,0),o.lookAt(0,0,1),l.up.set(0,1,0),l.lookAt(0,0,-1);else if(e===ms)n.up.set(0,-1,0),n.lookAt(-1,0,0),s.up.set(0,-1,0),s.lookAt(1,0,0),r.up.set(0,0,1),r.lookAt(0,1,0),a.up.set(0,0,-1),a.lookAt(0,-1,0),o.up.set(0,-1,0),o.lookAt(0,0,1),l.up.set(0,-1,0),l.lookAt(0,0,-1);else throw new Error("THREE.CubeCamera.updateCoordinateSystem(): Invalid coordinate system: "+e);for(let c of t)this.add(c),c.updateMatrixWorld()}update(e,t){this.parent===null&&this.updateMatrixWorld();let{renderTarget:n,activeMipmapLevel:s}=this;this.coordinateSystem!==e.coordinateSystem&&(this.coordinateSystem=e.coordinateSystem,this.updateCoordinateSystem());let[r,a,o,l,c,h]=this.children,f=e.getRenderTarget(),u=e.getActiveCubeFace(),d=e.getActiveMipmapLevel(),g=e.xr.enabled;e.xr.enabled=!1;let b=n.texture.generateMipmaps;n.texture.generateMipmaps=!1;let m=!1;e.isWebGLRenderer===!0?m=e.state.buffers.depth.getReversed():m=e.reversedDepthBuffer,e.setRenderTarget(n,0,s),m&&e.autoClear===!1&&e.clearDepth(),e.render(t,r),e.setRenderTarget(n,1,s),m&&e.autoClear===!1&&e.clearDepth(),e.render(t,a),e.setRenderTarget(n,2,s),m&&e.autoClear===!1&&e.clearDepth(),e.render(t,o),e.setRenderTarget(n,3,s),m&&e.autoClear===!1&&e.clearDepth(),e.render(t,l),e.setRenderTarget(n,4,s),m&&e.autoClear===!1&&e.clearDepth(),e.render(t,c),n.texture.generateMipmaps=b,e.setRenderTarget(n,5,s),m&&e.autoClear===!1&&e.clearDepth(),e.render(t,h),e.setRenderTarget(f,u,d),e.xr.enabled=g,n.texture.needsPMREMUpdate=!0}},co=class extends Jt{constructor(e=[]){super(),this.isArrayCamera=!0,this.isMultiViewCamera=!1,this.cameras=e}},Ar=class{constructor(){this._previousTime=0,this._currentTime=0,this._startTime=performance.now(),this._delta=0,this._elapsed=0,this._timescale=1,this._document=null,this._pageVisibilityHandler=null}connect(e){this._document=e,e.hidden!==void 0&&(this._pageVisibilityHandler=Wd.bind(this),e.addEventListener("visibilitychange",this._pageVisibilityHandler,!1))}disconnect(){this._pageVisibilityHandler!==null&&(this._document.removeEventListener("visibilitychange",this._pageVisibilityHandler),this._pageVisibilityHandler=null),this._document=null}getDelta(){return this._delta/1e3}getElapsed(){return this._elapsed/1e3}getTimescale(){return this._timescale}setTimescale(e){return this._timescale=e,this}reset(){return this._currentTime=performance.now()-this._startTime,this}dispose(){this.disconnect()}update(e){return this._pageVisibilityHandler!==null&&this._document.hidden===!0?this._delta=0:(this._previousTime=this._currentTime,this._currentTime=(e!==void 0?e:performance.now())-this._startTime,this._delta=(this._currentTime-this._previousTime)*this._timescale,this._elapsed+=this._delta),this}};function Wd(){this._document.hidden===!1&&this.reset()}var pc="\\[\\]\\.:\\/",qd=new RegExp("["+pc+"]","g"),mc="[^"+pc+"]",Xd="[^"+pc.replace("\\.","")+"]",$d=/((?:WC+[\/:])*)/.source.replace("WC",mc),Yd=/(WCOD+)?/.source.replace("WCOD",Xd),Zd=/(?:\.(WC+)(?:\[(.+)\])?)?/.source.replace("WC",mc),jd=/\.(WC+)(?:\[(.+)\])?/.source.replace("WC",mc),Jd=new RegExp("^"+$d+Yd+Zd+jd+"$"),Kd=["material","materials","bones","map"],$l=class{constructor(e,t,n){let s=n||Nt.parseTrackName(t);this._targetGroup=e,this._bindings=e.subscribe_(t,s)}getValue(e,t){this.bind();let n=this._targetGroup.nCachedObjects_,s=this._bindings[n];s!==void 0&&s.getValue(e,t)}setValue(e,t){let n=this._bindings;for(let s=this._targetGroup.nCachedObjects_,r=n.length;s!==r;++s)n[s].setValue(e,t)}bind(){let e=this._bindings;for(let t=this._targetGroup.nCachedObjects_,n=e.length;t!==n;++t)e[t].bind()}unbind(){let e=this._bindings;for(let t=this._targetGroup.nCachedObjects_,n=e.length;t!==n;++t)e[t].unbind()}},Nt=class i{constructor(e,t,n){this.path=t,this.parsedPath=n||i.parseTrackName(t),this.node=i.findNode(e,this.parsedPath.nodeName),this.rootNode=e,this.getValue=this._getValue_unbound,this.setValue=this._setValue_unbound}static create(e,t,n){return e&&e.isAnimationObjectGroup?new i.Composite(e,t,n):new i(e,t,n)}static sanitizeNodeName(e){return e.replace(/\s/g,"_").replace(qd,"")}static parseTrackName(e){let t=Jd.exec(e);if(t===null)throw new Error("THREE.PropertyBinding: Cannot parse trackName: "+e);let n={nodeName:t[2],objectName:t[3],objectIndex:t[4],propertyName:t[5],propertyIndex:t[6]},s=n.nodeName&&n.nodeName.lastIndexOf(".");if(s!==void 0&&s!==-1){let r=n.nodeName.substring(s+1);Kd.indexOf(r)!==-1&&(n.nodeName=n.nodeName.substring(0,s),n.objectName=r)}if(n.propertyName===null||n.propertyName.length===0)throw new Error("THREE.PropertyBinding: can not parse propertyName from trackName: "+e);return n}static findNode(e,t){if(t===void 0||t===""||t==="."||t===-1||t===e.name||t===e.uuid)return e;if(e.skeleton){let n=e.skeleton.getBoneByName(t);if(n!==void 0)return n}if(e.children){let n=function(r){for(let a=0;a<r.length;a++){let o=r[a];if(o.name===t||o.uuid===t)return o;let l=n(o.children);if(l)return l}return null},s=n(e.children);if(s)return s}return null}_getValue_unavailable(){}_setValue_unavailable(){}_getValue_direct(e,t){e[t]=this.targetObject[this.propertyName]}_getValue_array(e,t){let n=this.resolvedProperty;for(let s=0,r=n.length;s!==r;++s)e[t++]=n[s]}_getValue_arrayElement(e,t){e[t]=this.resolvedProperty[this.propertyIndex]}_getValue_toArray(e,t){this.resolvedProperty.toArray(e,t)}_setValue_direct(e,t){this.targetObject[this.propertyName]=e[t]}_setValue_direct_setNeedsUpdate(e,t){this.targetObject[this.propertyName]=e[t],this.targetObject.needsUpdate=!0}_setValue_direct_setMatrixWorldNeedsUpdate(e,t){this.targetObject[this.propertyName]=e[t],this.targetObject.matrixWorldNeedsUpdate=!0}_setValue_array(e,t){let n=this.resolvedProperty;for(let s=0,r=n.length;s!==r;++s)n[s]=e[t++]}_setValue_array_setNeedsUpdate(e,t){let n=this.resolvedProperty;for(let s=0,r=n.length;s!==r;++s)n[s]=e[t++];this.targetObject.needsUpdate=!0}_setValue_array_setMatrixWorldNeedsUpdate(e,t){let n=this.resolvedProperty;for(let s=0,r=n.length;s!==r;++s)n[s]=e[t++];this.targetObject.matrixWorldNeedsUpdate=!0}_setValue_arrayElement(e,t){this.resolvedProperty[this.propertyIndex]=e[t]}_setValue_arrayElement_setNeedsUpdate(e,t){this.resolvedProperty[this.propertyIndex]=e[t],this.targetObject.needsUpdate=!0}_setValue_arrayElement_setMatrixWorldNeedsUpdate(e,t){this.resolvedProperty[this.propertyIndex]=e[t],this.targetObject.matrixWorldNeedsUpdate=!0}_setValue_fromArray(e,t){this.resolvedProperty.fromArray(e,t)}_setValue_fromArray_setNeedsUpdate(e,t){this.resolvedProperty.fromArray(e,t),this.targetObject.needsUpdate=!0}_setValue_fromArray_setMatrixWorldNeedsUpdate(e,t){this.resolvedProperty.fromArray(e,t),this.targetObject.matrixWorldNeedsUpdate=!0}_getValue_unbound(e,t){this.bind(),this.getValue(e,t)}_setValue_unbound(e,t){this.bind(),this.setValue(e,t)}bind(){let e=this.node,t=this.parsedPath,n=t.objectName,s=t.propertyName,r=t.propertyIndex;if(e||(e=i.findNode(this.rootNode,t.nodeName),this.node=e),this.getValue=this._getValue_unavailable,this.setValue=this._setValue_unavailable,!e){je("PropertyBinding: No target node found for track: "+this.path+".");return}if(n){let c=t.objectIndex;switch(n){case"materials":if(!e.material){nt("PropertyBinding: Can not bind to material as node does not have a material.",this);return}if(!e.material.materials){nt("PropertyBinding: Can not bind to material.materials as node.material does not have a materials array.",this);return}e=e.material.materials;break;case"bones":if(!e.skeleton){nt("PropertyBinding: Can not bind to bones as node does not have a skeleton.",this);return}e=e.skeleton.bones;for(let h=0;h<e.length;h++)if(e[h].name===c){c=h;break}break;case"map":if("map"in e){e=e.map;break}if(!e.material){nt("PropertyBinding: Can not bind to material as node does not have a material.",this);return}if(!e.material.map){nt("PropertyBinding: Can not bind to material.map as node.material does not have a map.",this);return}e=e.material.map;break;default:if(e[n]===void 0){nt("PropertyBinding: Can not bind to objectName of node undefined.",this);return}e=e[n]}if(c!==void 0){if(e[c]===void 0){nt("PropertyBinding: Trying to bind to objectIndex of objectName, but is undefined.",this,e);return}e=e[c]}}let a=e[s];if(a===void 0){let c=t.nodeName;nt("PropertyBinding: Trying to update property for track: "+c+"."+s+" but it wasn't found.",e);return}let o=this.Versioning.None;this.targetObject=e,e.isMaterial===!0?o=this.Versioning.NeedsUpdate:e.isObject3D===!0&&(o=this.Versioning.MatrixWorldNeedsUpdate);let l=this.BindingType.Direct;if(r!==void 0){if(s==="morphTargetInfluences"){if(!e.geometry){nt("PropertyBinding: Can not bind to morphTargetInfluences because node does not have a geometry.",this);return}if(!e.geometry.morphAttributes){nt("PropertyBinding: Can not bind to morphTargetInfluences because node does not have a geometry.morphAttributes.",this);return}e.morphTargetDictionary[r]!==void 0&&(r=e.morphTargetDictionary[r])}l=this.BindingType.ArrayElement,this.resolvedProperty=a,this.propertyIndex=r}else a.fromArray!==void 0&&a.toArray!==void 0?(l=this.BindingType.HasFromToArray,this.resolvedProperty=a):Array.isArray(a)?(l=this.BindingType.EntireArray,this.resolvedProperty=a):this.propertyName=s;this.getValue=this.GetterByBindingType[l],this.setValue=this.SetterByBindingTypeAndVersioning[l][o]}unbind(){this.node=null,this.getValue=this._getValue_unbound,this.setValue=this._setValue_unbound}};Nt.Composite=$l;Nt.prototype.BindingType={Direct:0,EntireArray:1,ArrayElement:2,HasFromToArray:3};Nt.prototype.Versioning={None:0,NeedsUpdate:1,MatrixWorldNeedsUpdate:2};Nt.prototype.GetterByBindingType=[Nt.prototype._getValue_direct,Nt.prototype._getValue_array,Nt.prototype._getValue_arrayElement,Nt.prototype._getValue_toArray];Nt.prototype.SetterByBindingTypeAndVersioning=[[Nt.prototype._setValue_direct,Nt.prototype._setValue_direct_setNeedsUpdate,Nt.prototype._setValue_direct_setMatrixWorldNeedsUpdate],[Nt.prototype._setValue_array,Nt.prototype._setValue_array_setNeedsUpdate,Nt.prototype._setValue_array_setMatrixWorldNeedsUpdate],[Nt.prototype._setValue_arrayElement,Nt.prototype._setValue_arrayElement_setNeedsUpdate,Nt.prototype._setValue_arrayElement_setMatrixWorldNeedsUpdate],[Nt.prototype._setValue_fromArray,Nt.prototype._setValue_fromArray_setNeedsUpdate,Nt.prototype._setValue_fromArray_setMatrixWorldNeedsUpdate]];var n_=new Float32Array(1);var pu=new xt,Cr=class{constructor(e,t,n=0,s=1/0){this.ray=new Bi(e,t),this.near=n,this.far=s,this.camera=null,this.layers=new vs,this.params={Mesh:{},Line:{threshold:1},LOD:{},Points:{threshold:1},Sprite:{}}}set(e,t){this.ray.set(e,t)}setFromCamera(e,t){t.isPerspectiveCamera?(this.ray.origin.setFromMatrixPosition(t.matrixWorld),this.ray.direction.set(e.x,e.y,.5).unproject(t).sub(this.ray.origin).normalize(),this.camera=t):t.isOrthographicCamera?(this.ray.origin.set(e.x,e.y,t.projectionMatrix.elements[14]).unproject(t),this.ray.direction.set(0,0,-1).transformDirection(t.matrixWorld),this.camera=t):nt("Raycaster: Unsupported camera type: "+t.type)}setFromXRController(e){return pu.identity().extractRotation(e.matrixWorld),this.ray.origin.setFromMatrixPosition(e.matrixWorld),this.ray.direction.set(0,0,-1).applyMatrix4(pu),this}intersectObject(e,t=!0,n=[]){return Yl(e,this,n,t),n.sort(mu),n}intersectObjects(e,t=!0,n=[]){for(let s=0,r=e.length;s<r;s++)Yl(e[s],this,n,t);return n.sort(mu),n}};function mu(i,e){return i.distance-e.distance}function Yl(i,e,t,n){let s=!0;if(i.layers.test(e.layers)&&i.raycast(e,t)===!1&&(s=!1),s===!0&&n===!0){let r=i.children;for(let a=0,o=r.length;a<o;a++)Yl(r[a],e,t,!0)}}var Zl=class i{static{i.prototype.isMatrix2=!0}constructor(e,t,n,s){this.elements=[1,0,0,1],e!==void 0&&this.set(e,t,n,s)}identity(){return this.set(1,0,0,1),this}fromArray(e,t=0){for(let n=0;n<4;n++)this.elements[n]=e[n+t];return this}set(e,t,n,s){let r=this.elements;return r[0]=e,r[2]=t,r[1]=n,r[3]=s,this}};function gc(i,e,t,n){let s=Qd(n);switch(t){case ac:return i*e;case xo:return i*e/s.components*s.byteLength;case vo:return i*e/s.components*s.byteLength;case Ci:return i*e*2/s.components*s.byteLength;case yo:return i*e*2/s.components*s.byteLength;case oc:return i*e*3/s.components*s.byteLength;case In:return i*e*4/s.components*s.byteLength;case bo:return i*e*4/s.components*s.byteLength;case Or:case Br:return Math.floor((i+3)/4)*Math.floor((e+3)/4)*8;case zr:case Vr:return Math.floor((i+3)/4)*Math.floor((e+3)/4)*16;case So:case Eo:return Math.max(i,16)*Math.max(e,8)/4;case Mo:case To:return Math.max(i,8)*Math.max(e,8)/2;case wo:case Ao:case Ro:case Po:return Math.floor((i+3)/4)*Math.floor((e+3)/4)*8;case Co:case Hr:case Io:return Math.floor((i+3)/4)*Math.floor((e+3)/4)*16;case Lo:return Math.floor((i+3)/4)*Math.floor((e+3)/4)*16;case No:return Math.floor((i+4)/5)*Math.floor((e+3)/4)*16;case Do:return Math.floor((i+4)/5)*Math.floor((e+4)/5)*16;case Uo:return Math.floor((i+5)/6)*Math.floor((e+4)/5)*16;case Fo:return Math.floor((i+5)/6)*Math.floor((e+5)/6)*16;case ko:return Math.floor((i+7)/8)*Math.floor((e+4)/5)*16;case Oo:return Math.floor((i+7)/8)*Math.floor((e+5)/6)*16;case Bo:return Math.floor((i+7)/8)*Math.floor((e+7)/8)*16;case zo:return Math.floor((i+9)/10)*Math.floor((e+4)/5)*16;case Vo:return Math.floor((i+9)/10)*Math.floor((e+5)/6)*16;case Ho:return Math.floor((i+9)/10)*Math.floor((e+7)/8)*16;case Go:return Math.floor((i+9)/10)*Math.floor((e+9)/10)*16;case Wo:return Math.floor((i+11)/12)*Math.floor((e+9)/10)*16;case qo:return Math.floor((i+11)/12)*Math.floor((e+11)/12)*16;case Xo:case $o:case Yo:return Math.ceil(i/4)*Math.ceil(e/4)*16;case Zo:case jo:return Math.ceil(i/4)*Math.ceil(e/4)*8;case Gr:case Jo:return Math.ceil(i/4)*Math.ceil(e/4)*16}throw new Error(`Unable to determine texture byte length for ${t} format.`)}function Qd(i){switch(i){case xn:case nc:return{byteLength:1,components:1};case Ps:case ic:case tn:return{byteLength:2,components:1};case go:case _o:return{byteLength:2,components:4};case Vn:case mo:case Pn:return{byteLength:4,components:1};case sc:case rc:return{byteLength:4,components:3}}throw new Error(`THREE.TextureUtils: Unknown texture type ${i}.`)}typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("register",{detail:{revision:"186"}}));typeof window<"u"&&(window.__THREE__?je("WARNING: Multiple instances of Three.js being imported."):window.__THREE__="186");function Th(){let i=null,e=!1,t=null,n=null;function s(r,a){n=i.requestAnimationFrame(s),t(r,a)}return{start:function(){e!==!0&&t!==null&&i!==null&&(n=i.requestAnimationFrame(s),e=!0)},stop:function(){i!==null&&i.cancelAnimationFrame(n),e=!1},setAnimationLoop:function(r){t=r},setContext:function(r){i=r}}}function tf(i){let e=new WeakMap;function t(o,l){let c=o.array,h=o.usage,f=c.byteLength,u=i.createBuffer();i.bindBuffer(l,u),i.bufferData(l,c,h),o.onUploadCallback();let d;if(c instanceof Float32Array)d=i.FLOAT;else if(typeof Float16Array<"u"&&c instanceof Float16Array)d=i.HALF_FLOAT;else if(c instanceof Uint16Array)o.isFloat16BufferAttribute?d=i.HALF_FLOAT:d=i.UNSIGNED_SHORT;else if(c instanceof Int16Array)d=i.SHORT;else if(c instanceof Uint32Array)d=i.UNSIGNED_INT;else if(c instanceof Int32Array)d=i.INT;else if(c instanceof Int8Array)d=i.BYTE;else if(c instanceof Uint8Array)d=i.UNSIGNED_BYTE;else if(c instanceof Uint8ClampedArray)d=i.UNSIGNED_BYTE;else throw new Error("THREE.WebGLAttributes: Unsupported buffer data format: "+c);return{buffer:u,type:d,bytesPerElement:c.BYTES_PER_ELEMENT,version:o.version,size:f}}function n(o,l,c){let h=l.array,f=l.updateRanges;if(i.bindBuffer(c,o),f.length===0)i.bufferSubData(c,0,h);else{f.sort((d,g)=>d.start-g.start);let u=0;for(let d=1;d<f.length;d++){let g=f[u],b=f[d];b.start<=g.start+g.count+1?g.count=Math.max(g.count,b.start+b.count-g.start):(++u,f[u]=b)}f.length=u+1;for(let d=0,g=f.length;d<g;d++){let b=f[d];i.bufferSubData(c,b.start*h.BYTES_PER_ELEMENT,h,b.start,b.count)}l.clearUpdateRanges()}l.onUploadCallback()}function s(o){return o.isInterleavedBufferAttribute&&(o=o.data),e.get(o)}function r(o){o.isInterleavedBufferAttribute&&(o=o.data);let l=e.get(o);l&&(i.deleteBuffer(l.buffer),e.delete(o))}function a(o,l){if(o.isInterleavedBufferAttribute&&(o=o.data),o.isGLBufferAttribute){let h=e.get(o);(!h||h.version<o.version)&&e.set(o,{buffer:o.buffer,type:o.type,bytesPerElement:o.elementSize,version:o.version});return}let c=e.get(o);if(c===void 0)e.set(o,t(o,l));else if(c.version<o.version){if(c.size!==o.array.byteLength)throw new Error("THREE.WebGLAttributes: The size of the buffer attribute's array buffer does not match the original size. Resizing buffer attributes is not supported.");n(c.buffer,o,l),c.version=o.version}}return{get:s,remove:r,update:a}}var nf=`#ifdef USE_ALPHAHASH
	if ( diffuseColor.a < getAlphaHashThreshold( vPosition ) ) discard;
#endif`,sf=`#ifdef USE_ALPHAHASH
	const float ALPHA_HASH_SCALE = 0.05;
	float hash2D( vec2 value ) {
		return fract( 1.0e4 * sin( 17.0 * value.x + 0.1 * value.y ) * ( 0.1 + abs( sin( 13.0 * value.y + value.x ) ) ) );
	}
	float hash3D( vec3 value ) {
		return hash2D( vec2( hash2D( value.xy ), value.z ) );
	}
	float getAlphaHashThreshold( vec3 position ) {
		float maxDeriv = max(
			length( dFdx( position.xyz ) ),
			length( dFdy( position.xyz ) )
		);
		float pixScale = 1.0 / ( ALPHA_HASH_SCALE * maxDeriv );
		vec2 pixScales = vec2(
			exp2( floor( log2( pixScale ) ) ),
			exp2( ceil( log2( pixScale ) ) )
		);
		vec2 alpha = vec2(
			hash3D( floor( pixScales.x * position.xyz ) ),
			hash3D( floor( pixScales.y * position.xyz ) )
		);
		float lerpFactor = fract( log2( pixScale ) );
		float x = ( 1.0 - lerpFactor ) * alpha.x + lerpFactor * alpha.y;
		float a = min( lerpFactor, 1.0 - lerpFactor );
		vec3 cases = vec3(
			x * x / ( 2.0 * a * ( 1.0 - a ) ),
			( x - 0.5 * a ) / ( 1.0 - a ),
			1.0 - ( ( 1.0 - x ) * ( 1.0 - x ) / ( 2.0 * a * ( 1.0 - a ) ) )
		);
		float threshold = ( x < ( 1.0 - a ) )
			? ( ( x < a ) ? cases.x : cases.y )
			: cases.z;
		return clamp( threshold , 1.0e-6, 1.0 );
	}
#endif`,rf=`#ifdef USE_ALPHAMAP
	diffuseColor.a *= texture2D( alphaMap, vAlphaMapUv ).g;
#endif`,af=`#ifdef USE_ALPHAMAP
	uniform sampler2D alphaMap;
#endif`,of=`#ifdef USE_ALPHATEST
	#ifdef ALPHA_TO_COVERAGE
	diffuseColor.a = smoothstep( alphaTest, alphaTest + fwidth( diffuseColor.a ), diffuseColor.a );
	if ( diffuseColor.a == 0.0 ) discard;
	#else
	if ( diffuseColor.a < alphaTest ) discard;
	#endif
#endif`,lf=`#ifdef USE_ALPHATEST
	uniform float alphaTest;
#endif`,cf=`#ifdef USE_AOMAP
	float ambientOcclusion = ( texture2D( aoMap, vAoMapUv ).r - 1.0 ) * aoMapIntensity + 1.0;
	reflectedLight.indirectDiffuse *= ambientOcclusion;
	#if defined( USE_CLEARCOAT )
		clearcoatSpecularIndirect *= ambientOcclusion;
	#endif
	#if defined( USE_SHEEN )
		sheenSpecularIndirect *= ambientOcclusion;
	#endif
	#if defined( USE_ENVMAP ) && defined( STANDARD )
		float dotNV = saturate( dot( geometryNormal, geometryViewDir ) );
		reflectedLight.indirectSpecular *= computeSpecularOcclusion( dotNV, ambientOcclusion, material.roughness );
	#endif
#endif`,uf=`#ifdef USE_AOMAP
	uniform sampler2D aoMap;
	uniform float aoMapIntensity;
#endif`,hf=`#ifdef USE_BATCHING
	#if ! defined( GL_ANGLE_multi_draw )
	#define gl_DrawID _gl_DrawID
	uniform int _gl_DrawID;
	#endif
	uniform highp sampler2D batchingTexture;
	uniform highp usampler2D batchingIdTexture;
	mat4 getBatchingMatrix( const in float i ) {
		int size = textureSize( batchingTexture, 0 ).x;
		int j = int( i ) * 4;
		int x = j % size;
		int y = j / size;
		vec4 v1 = texelFetch( batchingTexture, ivec2( x, y ), 0 );
		vec4 v2 = texelFetch( batchingTexture, ivec2( x + 1, y ), 0 );
		vec4 v3 = texelFetch( batchingTexture, ivec2( x + 2, y ), 0 );
		vec4 v4 = texelFetch( batchingTexture, ivec2( x + 3, y ), 0 );
		return mat4( v1, v2, v3, v4 );
	}
	float getIndirectIndex( const in int i ) {
		int size = textureSize( batchingIdTexture, 0 ).x;
		int x = i % size;
		int y = i / size;
		return float( texelFetch( batchingIdTexture, ivec2( x, y ), 0 ).r );
	}
#endif
#ifdef USE_BATCHING_COLOR
	uniform sampler2D batchingColorTexture;
	vec4 getBatchingColor( const in float i ) {
		int size = textureSize( batchingColorTexture, 0 ).x;
		int j = int( i );
		int x = j % size;
		int y = j / size;
		return texelFetch( batchingColorTexture, ivec2( x, y ), 0 );
	}
#endif`,df=`#ifdef USE_BATCHING
	mat4 batchingMatrix = getBatchingMatrix( getIndirectIndex( gl_DrawID ) );
#endif`,ff=`vec3 transformed = vec3( position );
#ifdef USE_ALPHAHASH
	vPosition = vec3( position );
#endif`,pf=`vec3 objectNormal = vec3( normal );
#ifdef USE_TANGENT
	vec3 objectTangent = vec3( tangent.xyz );
#endif`,mf=`float G_BlinnPhong_Implicit( ) {
	return 0.25;
}
float D_BlinnPhong( const in float shininess, const in float dotNH ) {
	return RECIPROCAL_PI * ( shininess * 0.5 + 1.0 ) * pow( dotNH, shininess );
}
vec3 BRDF_BlinnPhong( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, const in vec3 specularColor, const in float shininess ) {
	vec3 halfDir = normalize( lightDir + viewDir );
	float dotNH = saturate( dot( normal, halfDir ) );
	float dotVH = saturate( dot( viewDir, halfDir ) );
	vec3 F = F_Schlick( specularColor, 1.0, dotVH );
	float G = G_BlinnPhong_Implicit( );
	float D = D_BlinnPhong( shininess, dotNH );
	return F * ( G * D );
} // validated`,gf=`#ifdef USE_IRIDESCENCE
	const mat3 XYZ_TO_REC709 = mat3(
		 3.2404542, -0.9692660,  0.0556434,
		-1.5371385,  1.8760108, -0.2040259,
		-0.4985314,  0.0415560,  1.0572252
	);
	vec3 Fresnel0ToIor( vec3 fresnel0 ) {
		vec3 sqrtF0 = sqrt( fresnel0 );
		return ( vec3( 1.0 ) + sqrtF0 ) / ( vec3( 1.0 ) - sqrtF0 );
	}
	vec3 IorToFresnel0( vec3 transmittedIor, float incidentIor ) {
		return pow2( ( transmittedIor - vec3( incidentIor ) ) / ( transmittedIor + vec3( incidentIor ) ) );
	}
	float IorToFresnel0( float transmittedIor, float incidentIor ) {
		return pow2( ( transmittedIor - incidentIor ) / ( transmittedIor + incidentIor ));
	}
	vec3 evalSensitivity( float OPD, vec3 shift ) {
		float phase = 2.0 * PI * OPD * 1.0e-9;
		vec3 val = vec3( 5.4856e-13, 4.4201e-13, 5.2481e-13 );
		vec3 pos = vec3( 1.6810e+06, 1.7953e+06, 2.2084e+06 );
		vec3 var = vec3( 4.3278e+09, 9.3046e+09, 6.6121e+09 );
		vec3 xyz = val * sqrt( 2.0 * PI * var ) * cos( pos * phase + shift ) * exp( - pow2( phase ) * var );
		xyz.x += 9.7470e-14 * sqrt( 2.0 * PI * 4.5282e+09 ) * cos( 2.2399e+06 * phase + shift[ 0 ] ) * exp( - 4.5282e+09 * pow2( phase ) );
		xyz /= 1.0685e-7;
		vec3 rgb = XYZ_TO_REC709 * xyz;
		return rgb;
	}
	vec3 evalIridescence( float outsideIOR, float eta2, float cosTheta1, float thinFilmThickness, vec3 baseF0 ) {
		vec3 I;
		float iridescenceIOR = mix( outsideIOR, eta2, smoothstep( 0.0, 0.03, thinFilmThickness ) );
		float sinTheta2Sq = pow2( outsideIOR / iridescenceIOR ) * ( 1.0 - pow2( cosTheta1 ) );
		float cosTheta2Sq = 1.0 - sinTheta2Sq;
		if ( cosTheta2Sq < 0.0 ) {
			return vec3( 1.0 );
		}
		float cosTheta2 = sqrt( cosTheta2Sq );
		float R0 = IorToFresnel0( iridescenceIOR, outsideIOR );
		float R12 = F_Schlick( R0, 1.0, cosTheta1 );
		float T121 = 1.0 - R12;
		float phi12 = 0.0;
		if ( iridescenceIOR < outsideIOR ) phi12 = PI;
		float phi21 = PI - phi12;
		vec3 baseIOR = Fresnel0ToIor( clamp( baseF0, 0.0, 0.9999 ) );		vec3 R1 = IorToFresnel0( baseIOR, iridescenceIOR );
		vec3 R23 = F_Schlick( R1, 1.0, cosTheta2 );
		vec3 phi23 = vec3( 0.0 );
		if ( baseIOR[ 0 ] < iridescenceIOR ) phi23[ 0 ] = PI;
		if ( baseIOR[ 1 ] < iridescenceIOR ) phi23[ 1 ] = PI;
		if ( baseIOR[ 2 ] < iridescenceIOR ) phi23[ 2 ] = PI;
		float OPD = 2.0 * iridescenceIOR * thinFilmThickness * cosTheta2;
		vec3 phi = vec3( phi21 ) + phi23;
		vec3 R123 = clamp( R12 * R23, 1e-5, 0.9999 );
		vec3 r123 = sqrt( R123 );
		vec3 Rs = pow2( T121 ) * R23 / ( vec3( 1.0 ) - R123 );
		vec3 C0 = R12 + Rs;
		I = C0;
		vec3 Cm = Rs - T121;
		for ( int m = 1; m <= 2; ++ m ) {
			Cm *= r123;
			vec3 Sm = 2.0 * evalSensitivity( float( m ) * OPD, float( m ) * phi );
			I += Cm * Sm;
		}
		return max( I, vec3( 0.0 ) );
	}
#endif`,_f=`#ifdef USE_BUMPMAP
	uniform sampler2D bumpMap;
	uniform float bumpScale;
	vec2 dHdxy_fwd() {
		vec2 dSTdx = dFdx( vBumpMapUv );
		vec2 dSTdy = dFdy( vBumpMapUv );
		float Hll = bumpScale * texture2D( bumpMap, vBumpMapUv ).x;
		float dBx = bumpScale * texture2D( bumpMap, vBumpMapUv + dSTdx ).x - Hll;
		float dBy = bumpScale * texture2D( bumpMap, vBumpMapUv + dSTdy ).x - Hll;
		return vec2( dBx, dBy );
	}
	vec3 perturbNormalArb( vec3 surf_pos, vec3 surf_norm, vec2 dHdxy, float faceDirection ) {
		vec3 vSigmaX = normalize( dFdx( surf_pos.xyz ) );
		vec3 vSigmaY = normalize( dFdy( surf_pos.xyz ) );
		vec3 vN = surf_norm;
		vec3 R1 = cross( vSigmaY, vN );
		vec3 R2 = cross( vN, vSigmaX );
		float fDet = dot( vSigmaX, R1 ) * faceDirection;
		vec3 vGrad = sign( fDet ) * ( dHdxy.x * R1 + dHdxy.y * R2 );
		return normalize( abs( fDet ) * surf_norm - vGrad );
	}
#endif`,xf=`#if NUM_CLIPPING_PLANES > 0
	vec4 plane;
	#ifdef ALPHA_TO_COVERAGE
		float distanceToPlane, distanceGradient;
		float clipOpacity = 1.0;
		#pragma unroll_loop_start
		for ( int i = 0; i < UNION_CLIPPING_PLANES; i ++ ) {
			plane = clippingPlanes[ i ];
			distanceToPlane = - dot( vClipPosition, plane.xyz ) + plane.w;
			distanceGradient = fwidth( distanceToPlane ) / 2.0;
			clipOpacity *= smoothstep( - distanceGradient, distanceGradient, distanceToPlane );
			if ( clipOpacity == 0.0 ) discard;
		}
		#pragma unroll_loop_end
		#if UNION_CLIPPING_PLANES < NUM_CLIPPING_PLANES
			float unionClipOpacity = 1.0;
			#pragma unroll_loop_start
			for ( int i = UNION_CLIPPING_PLANES; i < NUM_CLIPPING_PLANES; i ++ ) {
				plane = clippingPlanes[ i ];
				distanceToPlane = - dot( vClipPosition, plane.xyz ) + plane.w;
				distanceGradient = fwidth( distanceToPlane ) / 2.0;
				unionClipOpacity *= 1.0 - smoothstep( - distanceGradient, distanceGradient, distanceToPlane );
			}
			#pragma unroll_loop_end
			clipOpacity *= 1.0 - unionClipOpacity;
		#endif
		diffuseColor.a *= clipOpacity;
		if ( diffuseColor.a == 0.0 ) discard;
	#else
		#pragma unroll_loop_start
		for ( int i = 0; i < UNION_CLIPPING_PLANES; i ++ ) {
			plane = clippingPlanes[ i ];
			if ( dot( vClipPosition, plane.xyz ) > plane.w ) discard;
		}
		#pragma unroll_loop_end
		#if UNION_CLIPPING_PLANES < NUM_CLIPPING_PLANES
			bool clipped = true;
			#pragma unroll_loop_start
			for ( int i = UNION_CLIPPING_PLANES; i < NUM_CLIPPING_PLANES; i ++ ) {
				plane = clippingPlanes[ i ];
				clipped = ( dot( vClipPosition, plane.xyz ) > plane.w ) && clipped;
			}
			#pragma unroll_loop_end
			if ( clipped ) discard;
		#endif
	#endif
#endif`,vf=`#if NUM_CLIPPING_PLANES > 0
	varying vec3 vClipPosition;
	uniform vec4 clippingPlanes[ NUM_CLIPPING_PLANES ];
#endif`,yf=`#if NUM_CLIPPING_PLANES > 0
	varying vec3 vClipPosition;
#endif`,bf=`#if NUM_CLIPPING_PLANES > 0
	vClipPosition = - mvPosition.xyz;
#endif`,Mf=`#if defined( USE_COLOR ) || defined( USE_COLOR_ALPHA )
	diffuseColor *= vColor;
#endif`,Sf=`#if defined( USE_COLOR ) || defined( USE_COLOR_ALPHA )
	varying vec4 vColor;
#endif`,Tf=`#if defined( USE_COLOR ) || defined( USE_COLOR_ALPHA ) || defined( USE_INSTANCING_COLOR ) || defined( USE_BATCHING_COLOR )
	varying vec4 vColor;
#endif`,Ef=`#if defined( USE_COLOR ) || defined( USE_COLOR_ALPHA ) || defined( USE_INSTANCING_COLOR ) || defined( USE_BATCHING_COLOR )
	vColor = vec4( 1.0 );
#endif
#ifdef USE_COLOR_ALPHA
	vColor *= color;
#elif defined( USE_COLOR )
	vColor.rgb *= color;
#endif
#ifdef USE_INSTANCING_COLOR
	vColor.rgb *= instanceColor.rgb;
#endif
#ifdef USE_BATCHING_COLOR
	vColor *= getBatchingColor( getIndirectIndex( gl_DrawID ) );
#endif`,wf=`#define PI 3.141592653589793
#define PI2 6.283185307179586
#define PI_HALF 1.5707963267948966
#define RECIPROCAL_PI 0.3183098861837907
#define RECIPROCAL_PI2 0.15915494309189535
#define EPSILON 1e-6
#ifndef saturate
#define saturate( a ) clamp( a, 0.0, 1.0 )
#endif
#define whiteComplement( a ) ( 1.0 - saturate( a ) )
float pow2( const in float x ) { return x*x; }
vec3 pow2( const in vec3 x ) { return x*x; }
float pow3( const in float x ) { return x*x*x; }
float pow4( const in float x ) { float x2 = x*x; return x2*x2; }
float max3( const in vec3 v ) { return max( max( v.x, v.y ), v.z ); }
float average( const in vec3 v ) { return dot( v, vec3( 0.3333333 ) ); }
highp float rand( const in vec2 uv ) {
	const highp float a = 12.9898, b = 78.233, c = 43758.5453;
	highp float dt = dot( uv.xy, vec2( a,b ) ), sn = mod( dt, PI );
	return fract( sin( sn ) * c );
}
#ifdef HIGH_PRECISION
	float precisionSafeLength( vec3 v ) { return length( v ); }
#else
	float precisionSafeLength( vec3 v ) {
		float maxComponent = max3( abs( v ) );
		return length( v / maxComponent ) * maxComponent;
	}
#endif
struct IncidentLight {
	vec3 color;
	vec3 direction;
	bool visible;
};
struct ReflectedLight {
	vec3 directDiffuse;
	vec3 directSpecular;
	vec3 indirectDiffuse;
	vec3 indirectSpecular;
};
#ifdef USE_ALPHAHASH
	varying vec3 vPosition;
#endif
vec3 transformDirection( in vec3 dir, in mat4 matrix ) {
	return normalize( ( matrix * vec4( dir, 0.0 ) ).xyz );
}
#define inverseTransformDirection transformDirectionByInverseViewMatrix
vec3 transformNormalByInverseViewMatrix( in vec3 normal, in mat4 viewMatrix ) {
	return normalize( ( vec4( normal, 0.0 ) * viewMatrix ).xyz );
}
vec3 transformDirectionByInverseViewMatrix( in vec3 dir, in mat4 viewMatrix ) {
	return normalize( ( vec4( dir, 0.0 ) * viewMatrix ).xyz );
}
bool isPerspectiveMatrix( mat4 m ) {
	return m[ 2 ][ 3 ] == - 1.0;
}
vec2 equirectUv( in vec3 dir ) {
	float u = atan( dir.z, dir.x ) * RECIPROCAL_PI2 + 0.5;
	float v = asin( clamp( dir.y, - 1.0, 1.0 ) ) * RECIPROCAL_PI + 0.5;
	return vec2( u, v );
}
vec3 BRDF_Lambert( const in vec3 diffuseColor ) {
	return RECIPROCAL_PI * diffuseColor;
}
vec3 F_Schlick( const in vec3 f0, const in float f90, const in float dotVH ) {
	float fresnel = exp2( ( - 5.55473 * dotVH - 6.98316 ) * dotVH );
	return f0 * ( 1.0 - fresnel ) + ( f90 * fresnel );
}
float F_Schlick( const in float f0, const in float f90, const in float dotVH ) {
	float fresnel = exp2( ( - 5.55473 * dotVH - 6.98316 ) * dotVH );
	return f0 * ( 1.0 - fresnel ) + ( f90 * fresnel );
} // validated`,Af=`#ifdef ENVMAP_TYPE_CUBE_UV
	#define cubeUV_minMipLevel 4.0
	#define cubeUV_minTileSize 16.0
	float getFace( vec3 direction ) {
		vec3 absDirection = abs( direction );
		float face = - 1.0;
		if ( absDirection.x > absDirection.z ) {
			if ( absDirection.x > absDirection.y )
				face = direction.x > 0.0 ? 0.0 : 3.0;
			else
				face = direction.y > 0.0 ? 1.0 : 4.0;
		} else {
			if ( absDirection.z > absDirection.y )
				face = direction.z > 0.0 ? 2.0 : 5.0;
			else
				face = direction.y > 0.0 ? 1.0 : 4.0;
		}
		return face;
	}
	vec2 getUV( vec3 direction, float face ) {
		vec2 uv;
		if ( face == 0.0 ) {
			uv = vec2( direction.z, direction.y ) / abs( direction.x );
		} else if ( face == 1.0 ) {
			uv = vec2( - direction.x, - direction.z ) / abs( direction.y );
		} else if ( face == 2.0 ) {
			uv = vec2( - direction.x, direction.y ) / abs( direction.z );
		} else if ( face == 3.0 ) {
			uv = vec2( - direction.z, direction.y ) / abs( direction.x );
		} else if ( face == 4.0 ) {
			uv = vec2( - direction.x, direction.z ) / abs( direction.y );
		} else {
			uv = vec2( direction.x, direction.y ) / abs( direction.z );
		}
		return 0.5 * ( uv + 1.0 );
	}
	vec3 bilinearCubeUV( sampler2D envMap, vec3 direction, float mipInt ) {
		float face = getFace( direction );
		float filterInt = max( cubeUV_minMipLevel - mipInt, 0.0 );
		mipInt = max( mipInt, cubeUV_minMipLevel );
		float faceSize = exp2( mipInt );
		highp vec2 uv = getUV( direction, face ) * ( faceSize - 2.0 ) + 1.0;
		if ( face > 2.0 ) {
			uv.y += faceSize;
			face -= 3.0;
		}
		uv.x += face * faceSize;
		uv.x += filterInt * 3.0 * cubeUV_minTileSize;
		uv.y += 4.0 * ( exp2( CUBEUV_MAX_MIP ) - faceSize );
		uv.x *= CUBEUV_TEXEL_WIDTH;
		uv.y *= CUBEUV_TEXEL_HEIGHT;
		#ifdef texture2DGradEXT
			return texture2DGradEXT( envMap, uv, vec2( 0.0 ), vec2( 0.0 ) ).rgb;
		#else
			return texture2D( envMap, uv ).rgb;
		#endif
	}
	#define cubeUV_r0 1.0
	#define cubeUV_m0 - 2.0
	#define cubeUV_r1 0.8
	#define cubeUV_m1 - 1.0
	#define cubeUV_r4 0.4
	#define cubeUV_m4 2.0
	#define cubeUV_r5 0.305
	#define cubeUV_m5 3.0
	#define cubeUV_r6 0.21
	#define cubeUV_m6 4.0
	float roughnessToMip( float roughness ) {
		float mip = 0.0;
		if ( roughness >= cubeUV_r1 ) {
			mip = ( cubeUV_r0 - roughness ) * ( cubeUV_m1 - cubeUV_m0 ) / ( cubeUV_r0 - cubeUV_r1 ) + cubeUV_m0;
		} else if ( roughness >= cubeUV_r4 ) {
			mip = ( cubeUV_r1 - roughness ) * ( cubeUV_m4 - cubeUV_m1 ) / ( cubeUV_r1 - cubeUV_r4 ) + cubeUV_m1;
		} else if ( roughness >= cubeUV_r5 ) {
			mip = ( cubeUV_r4 - roughness ) * ( cubeUV_m5 - cubeUV_m4 ) / ( cubeUV_r4 - cubeUV_r5 ) + cubeUV_m4;
		} else if ( roughness >= cubeUV_r6 ) {
			mip = ( cubeUV_r5 - roughness ) * ( cubeUV_m6 - cubeUV_m5 ) / ( cubeUV_r5 - cubeUV_r6 ) + cubeUV_m5;
		} else {
			mip = - 2.0 * log2( 1.16 * roughness );		}
		return mip;
	}
	vec4 textureCubeUV( sampler2D envMap, vec3 sampleDir, float roughness ) {
		float mip = clamp( roughnessToMip( roughness ), cubeUV_m0, CUBEUV_MAX_MIP );
		float mipF = fract( mip );
		float mipInt = floor( mip );
		vec3 color0 = bilinearCubeUV( envMap, sampleDir, mipInt );
		if ( mipF == 0.0 ) {
			return vec4( color0, 1.0 );
		} else {
			vec3 color1 = bilinearCubeUV( envMap, sampleDir, mipInt + 1.0 );
			return vec4( mix( color0, color1, mipF ), 1.0 );
		}
	}
#endif`,Cf=`vec3 transformedNormal = objectNormal;
#ifdef USE_TANGENT
	vec3 transformedTangent = objectTangent;
#endif
#ifdef USE_BATCHING
	mat3 bm = mat3( batchingMatrix );
	transformedNormal /= vec3( dot( bm[ 0 ], bm[ 0 ] ), dot( bm[ 1 ], bm[ 1 ] ), dot( bm[ 2 ], bm[ 2 ] ) );
	transformedNormal = bm * transformedNormal;
	#ifdef USE_TANGENT
		transformedTangent = bm * transformedTangent;
	#endif
#endif
#ifdef USE_INSTANCING
	mat3 im = mat3( instanceMatrix );
	transformedNormal /= vec3( dot( im[ 0 ], im[ 0 ] ), dot( im[ 1 ], im[ 1 ] ), dot( im[ 2 ], im[ 2 ] ) );
	transformedNormal = im * transformedNormal;
	#ifdef USE_TANGENT
		transformedTangent = im * transformedTangent;
	#endif
#endif
transformedNormal = normalMatrix * transformedNormal;
#ifdef FLIP_SIDED
	transformedNormal = - transformedNormal;
#endif
#ifdef USE_TANGENT
	transformedTangent = ( modelViewMatrix * vec4( transformedTangent, 0.0 ) ).xyz;
#endif`,Rf=`#ifdef USE_DISPLACEMENTMAP
	uniform sampler2D displacementMap;
	uniform float displacementScale;
	uniform float displacementBias;
#endif`,Pf=`#ifdef USE_DISPLACEMENTMAP
	transformed += normalize( objectNormal ) * ( texture2D( displacementMap, vDisplacementMapUv ).x * displacementScale + displacementBias );
#endif`,If=`#ifdef USE_EMISSIVEMAP
	vec4 emissiveColor = texture2D( emissiveMap, vEmissiveMapUv );
	#ifdef DECODE_VIDEO_TEXTURE_EMISSIVE
		emissiveColor = sRGBTransferEOTF( emissiveColor );
	#endif
	totalEmissiveRadiance *= emissiveColor.rgb;
#endif`,Lf=`#ifdef USE_EMISSIVEMAP
	uniform sampler2D emissiveMap;
#endif`,Nf="gl_FragColor = linearToOutputTexel( gl_FragColor );",Df=`vec4 LinearTransferOETF( in vec4 value ) {
	return value;
}
vec4 sRGBTransferEOTF( in vec4 value ) {
	return vec4( mix( pow( value.rgb * 0.9478672986 + vec3( 0.0521327014 ), vec3( 2.4 ) ), value.rgb * 0.0773993808, vec3( lessThanEqual( value.rgb, vec3( 0.04045 ) ) ) ), value.a );
}
vec4 sRGBTransferOETF( in vec4 value ) {
	return vec4( mix( pow( value.rgb, vec3( 0.41666 ) ) * 1.055 - vec3( 0.055 ), value.rgb * 12.92, vec3( lessThanEqual( value.rgb, vec3( 0.0031308 ) ) ) ), value.a );
}`,Uf=`#ifdef USE_ENVMAP
	#ifdef ENV_WORLDPOS
		vec3 cameraToFrag;
		if ( isOrthographic ) {
			cameraToFrag = normalize( vec3( - viewMatrix[ 0 ][ 2 ], - viewMatrix[ 1 ][ 2 ], - viewMatrix[ 2 ][ 2 ] ) );
		} else {
			cameraToFrag = normalize( vWorldPosition - cameraPosition );
		}
		vec3 worldNormal = transformNormalByInverseViewMatrix( normal, viewMatrix );
		#ifdef ENVMAP_MODE_REFLECTION
			vec3 reflectVec = reflect( cameraToFrag, worldNormal );
		#else
			vec3 reflectVec = refract( cameraToFrag, worldNormal, refractionRatio );
		#endif
	#else
		vec3 reflectVec = vReflect;
	#endif
	#ifdef ENVMAP_TYPE_CUBE
		vec4 envColor = textureCube( envMap, envMapRotation * reflectVec );
		#ifdef ENVMAP_BLENDING_MULTIPLY
			outgoingLight = mix( outgoingLight, outgoingLight * envColor.xyz, specularStrength * reflectivity );
		#elif defined( ENVMAP_BLENDING_MIX )
			outgoingLight = mix( outgoingLight, envColor.xyz, specularStrength * reflectivity );
		#elif defined( ENVMAP_BLENDING_ADD )
			outgoingLight += envColor.xyz * specularStrength * reflectivity;
		#endif
	#endif
#endif`,Ff=`#ifdef USE_ENVMAP
	uniform float envMapIntensity;
	uniform mat3 envMapRotation;
	#ifdef ENVMAP_TYPE_CUBE
		uniform samplerCube envMap;
	#else
		uniform sampler2D envMap;
	#endif
#endif`,kf=`#ifdef USE_ENVMAP
	uniform float reflectivity;
	#if defined( USE_BUMPMAP ) || defined( USE_NORMALMAP ) || defined( PHONG ) || defined( LAMBERT )
		#define ENV_WORLDPOS
	#endif
	#ifdef ENV_WORLDPOS
		varying vec3 vWorldPosition;
		uniform float refractionRatio;
	#else
		varying vec3 vReflect;
	#endif
#endif`,Of=`#ifdef USE_ENVMAP
	#if defined( USE_BUMPMAP ) || defined( USE_NORMALMAP ) || defined( PHONG ) || defined( LAMBERT )
		#define ENV_WORLDPOS
	#endif
	#ifdef ENV_WORLDPOS

		varying vec3 vWorldPosition;
	#else
		varying vec3 vReflect;
		uniform float refractionRatio;
	#endif
#endif`,Bf=`#ifdef USE_ENVMAP
	#ifdef ENV_WORLDPOS
		vWorldPosition = worldPosition.xyz;
	#else
		vec3 cameraToVertex;
		if ( isOrthographic ) {
			cameraToVertex = normalize( vec3( - viewMatrix[ 0 ][ 2 ], - viewMatrix[ 1 ][ 2 ], - viewMatrix[ 2 ][ 2 ] ) );
		} else {
			cameraToVertex = normalize( worldPosition.xyz - cameraPosition );
		}
		vec3 worldNormal = transformNormalByInverseViewMatrix( transformedNormal, viewMatrix );
		#ifdef ENVMAP_MODE_REFLECTION
			vReflect = reflect( cameraToVertex, worldNormal );
		#else
			vReflect = refract( cameraToVertex, worldNormal, refractionRatio );
		#endif
	#endif
#endif`,zf=`#ifdef USE_FOG
	vFogDepth = - mvPosition.z;
#endif`,Vf=`#ifdef USE_FOG
	varying float vFogDepth;
#endif`,Hf=`#ifdef USE_FOG
	#ifdef FOG_EXP2
		float fogFactor = 1.0 - exp( - fogDensity * fogDensity * vFogDepth * vFogDepth );
	#else
		float fogFactor = smoothstep( fogNear, fogFar, vFogDepth );
	#endif
	gl_FragColor.rgb = mix( gl_FragColor.rgb, fogColor, fogFactor );
#endif`,Gf=`#ifdef USE_FOG
	uniform vec3 fogColor;
	varying float vFogDepth;
	#ifdef FOG_EXP2
		uniform float fogDensity;
	#else
		uniform float fogNear;
		uniform float fogFar;
	#endif
#endif`,Wf=`#ifdef USE_GRADIENTMAP
	uniform sampler2D gradientMap;
#endif
vec3 getGradientIrradiance( vec3 normal, vec3 lightDirection ) {
	float dotNL = dot( normal, lightDirection );
	vec2 coord = vec2( dotNL * 0.5 + 0.5, 0.0 );
	#ifdef USE_GRADIENTMAP
		return vec3( texture2D( gradientMap, coord ).r );
	#else
		vec2 fw = fwidth( coord ) * 0.5;
		return mix( vec3( 0.7 ), vec3( 1.0 ), smoothstep( 0.7 - fw.x, 0.7 + fw.x, coord.x ) );
	#endif
}`,qf=`#ifdef USE_LIGHTMAP
	uniform sampler2D lightMap;
	uniform float lightMapIntensity;
#endif`,Xf=`LambertMaterial material;
material.diffuseColor = diffuseColor.rgb;
material.specularStrength = specularStrength;`,$f=`varying vec3 vViewPosition;
struct LambertMaterial {
	vec3 diffuseColor;
	float specularStrength;
};
void RE_Direct_Lambert( const in IncidentLight directLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in LambertMaterial material, inout ReflectedLight reflectedLight ) {
	float dotNL = saturate( dot( geometryNormal, directLight.direction ) );
	vec3 irradiance = dotNL * directLight.color;
	reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
void RE_IndirectDiffuse_Lambert( const in vec3 irradiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in LambertMaterial material, inout ReflectedLight reflectedLight ) {
	reflectedLight.indirectDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
#define RE_Direct				RE_Direct_Lambert
#define RE_IndirectDiffuse		RE_IndirectDiffuse_Lambert`,Yf=`uniform bool receiveShadow;
uniform vec3 ambientLightColor;
#if defined( USE_LIGHT_PROBES )
	uniform vec3 lightProbe[ 9 ];
#endif
vec3 shGetIrradianceAt( in vec3 normal, in vec3 shCoefficients[ 9 ] ) {
	float x = normal.x, y = normal.y, z = normal.z;
	vec3 result = shCoefficients[ 0 ] * 0.886227;
	result += shCoefficients[ 1 ] * 2.0 * 0.511664 * y;
	result += shCoefficients[ 2 ] * 2.0 * 0.511664 * z;
	result += shCoefficients[ 3 ] * 2.0 * 0.511664 * x;
	result += shCoefficients[ 4 ] * 2.0 * 0.429043 * x * y;
	result += shCoefficients[ 5 ] * 2.0 * 0.429043 * y * z;
	result += shCoefficients[ 6 ] * ( 0.743125 * z * z - 0.247708 );
	result += shCoefficients[ 7 ] * 2.0 * 0.429043 * x * z;
	result += shCoefficients[ 8 ] * 0.429043 * ( x * x - y * y );
	return result;
}
vec3 getLightProbeIrradiance( const in vec3 lightProbe[ 9 ], const in vec3 normal ) {
	vec3 worldNormal = transformNormalByInverseViewMatrix( normal, viewMatrix );
	vec3 irradiance = shGetIrradianceAt( worldNormal, lightProbe );
	return irradiance;
}
vec3 getAmbientLightIrradiance( const in vec3 ambientLightColor ) {
	vec3 irradiance = ambientLightColor;
	return irradiance;
}
float getDistanceAttenuation( const in float lightDistance, const in float cutoffDistance, const in float decayExponent ) {
	float distanceFalloff = 1.0 / max( pow( lightDistance, decayExponent ), 0.01 );
	if ( cutoffDistance > 0.0 ) {
		distanceFalloff *= pow2( saturate( 1.0 - pow4( lightDistance / cutoffDistance ) ) );
	}
	return distanceFalloff;
}
float getSpotAttenuation( const in float coneCosine, const in float penumbraCosine, const in float angleCosine ) {
	return smoothstep( coneCosine, penumbraCosine, angleCosine );
}
#if NUM_SUN_LIGHTS > 0
	struct SunLight {
		vec3 direction;
		vec3 color;
	};
	uniform SunLight sunLights[ NUM_SUN_LIGHTS ];
	void getSunLightInfo( const in SunLight sunLight, out IncidentLight light ) {
		light.color = sunLight.color;
		light.direction = sunLight.direction;
		light.visible = true;
	}
#endif
#if NUM_DIR_LIGHTS > 0
	struct DirectionalLight {
		vec3 direction;
		vec3 color;
	};
	uniform DirectionalLight directionalLights[ NUM_DIR_LIGHTS ];
	void getDirectionalLightInfo( const in DirectionalLight directionalLight, out IncidentLight light ) {
		light.color = directionalLight.color;
		light.direction = directionalLight.direction;
		light.visible = true;
	}
#endif
#if NUM_POINT_LIGHTS > 0
	struct PointLight {
		vec3 position;
		vec3 color;
		float distance;
		float decay;
	};
	uniform PointLight pointLights[ NUM_POINT_LIGHTS ];
	void getPointLightInfo( const in PointLight pointLight, const in vec3 geometryPosition, out IncidentLight light ) {
		vec3 lVector = pointLight.position - geometryPosition;
		light.direction = normalize( lVector );
		float lightDistance = length( lVector );
		light.color = pointLight.color;
		light.color *= getDistanceAttenuation( lightDistance, pointLight.distance, pointLight.decay );
		light.visible = ( light.color != vec3( 0.0 ) );
	}
#endif
#if NUM_SPOT_LIGHTS > 0
	struct SpotLight {
		vec3 position;
		vec3 direction;
		vec3 color;
		float distance;
		float decay;
		float coneCos;
		float penumbraCos;
	};
	uniform SpotLight spotLights[ NUM_SPOT_LIGHTS ];
	void getSpotLightInfo( const in SpotLight spotLight, const in vec3 geometryPosition, out IncidentLight light ) {
		vec3 lVector = spotLight.position - geometryPosition;
		light.direction = normalize( lVector );
		float angleCos = dot( light.direction, spotLight.direction );
		float spotAttenuation = getSpotAttenuation( spotLight.coneCos, spotLight.penumbraCos, angleCos );
		if ( spotAttenuation > 0.0 ) {
			float lightDistance = length( lVector );
			light.color = spotLight.color * spotAttenuation;
			light.color *= getDistanceAttenuation( lightDistance, spotLight.distance, spotLight.decay );
			light.visible = ( light.color != vec3( 0.0 ) );
		} else {
			light.color = vec3( 0.0 );
			light.visible = false;
		}
	}
#endif
#if NUM_RECT_AREA_LIGHTS > 0
	struct RectAreaLight {
		vec3 color;
		vec3 position;
		vec3 halfWidth;
		vec3 halfHeight;
	};
	uniform sampler2D ltc_1;	uniform sampler2D ltc_2;
	uniform RectAreaLight rectAreaLights[ NUM_RECT_AREA_LIGHTS ];
#endif
#if NUM_HEMI_LIGHTS > 0
	struct HemisphereLight {
		vec3 direction;
		vec3 skyColor;
		vec3 groundColor;
	};
	uniform HemisphereLight hemisphereLights[ NUM_HEMI_LIGHTS ];
	vec3 getHemisphereLightIrradiance( const in HemisphereLight hemiLight, const in vec3 normal ) {
		float dotNL = dot( normal, hemiLight.direction );
		float hemiDiffuseWeight = 0.5 * dotNL + 0.5;
		vec3 irradiance = mix( hemiLight.groundColor, hemiLight.skyColor, hemiDiffuseWeight );
		return irradiance;
	}
#endif
#include <lightprobes_pars_fragment>`,Zf=`#ifdef USE_ENVMAP
	vec3 getIBLIrradiance( const in vec3 normal ) {
		#ifdef ENVMAP_TYPE_CUBE_UV
			vec3 worldNormal = transformNormalByInverseViewMatrix( normal, viewMatrix );
			vec4 envMapColor = textureCubeUV( envMap, envMapRotation * worldNormal, 1.0 );
			return PI * envMapColor.rgb * envMapIntensity;
		#else
			return vec3( 0.0 );
		#endif
	}
	vec3 getIBLRadiance( const in vec3 viewDir, const in vec3 normal, const in float roughness ) {
		#ifdef ENVMAP_TYPE_CUBE_UV
			vec3 reflectVec = reflect( - viewDir, normal );
			reflectVec = normalize( mix( reflectVec, normal, pow4( roughness ) ) );
			reflectVec = transformDirectionByInverseViewMatrix( reflectVec, viewMatrix );
			vec4 envMapColor = textureCubeUV( envMap, envMapRotation * reflectVec, roughness );
			return envMapColor.rgb * envMapIntensity;
		#else
			return vec3( 0.0 );
		#endif
	}
	#ifdef USE_RETROREFLECTION
		vec3 getIBLRetroRadiance( const in vec3 viewDir, const in vec3 normal, const in float roughness ) {
			#ifdef ENVMAP_TYPE_CUBE_UV
				vec3 retroVec = normalize( mix( viewDir, normal, pow4( roughness ) ) );
				retroVec = transformDirectionByInverseViewMatrix( retroVec, viewMatrix );
				vec4 envMapColor = textureCubeUV( envMap, envMapRotation * retroVec, roughness );
				return envMapColor.rgb * envMapIntensity;
			#else
				return vec3( 0.0 );
			#endif
		}
	#endif
	#ifdef USE_ANISOTROPY
		vec3 getIBLAnisotropyRadiance( const in vec3 viewDir, const in vec3 normal, const in float roughness, const in vec3 bitangent, const in float anisotropy ) {
			#ifdef ENVMAP_TYPE_CUBE_UV
				vec3 bentNormal = cross( bitangent, viewDir );
				bentNormal = normalize( cross( bentNormal, bitangent ) );
				bentNormal = normalize( mix( bentNormal, normal, pow2( pow2( 1.0 - anisotropy * ( 1.0 - roughness ) ) ) ) );
				return getIBLRadiance( viewDir, bentNormal, roughness );
			#else
				return vec3( 0.0 );
			#endif
		}
		#ifdef USE_RETROREFLECTION
			vec3 getIBLAnisotropyRetroRadiance( const in vec3 viewDir, const in vec3 normal, const in float roughness, const in vec3 bitangent, const in float anisotropy ) {
				#ifdef ENVMAP_TYPE_CUBE_UV
					vec3 bentNormal = cross( bitangent, viewDir );
					bentNormal = normalize( cross( bentNormal, bitangent ) );
					bentNormal = normalize( mix( bentNormal, normal, pow2( pow2( 1.0 - anisotropy * ( 1.0 - roughness ) ) ) ) );
					return getIBLRetroRadiance( viewDir, bentNormal, roughness );
				#else
					return vec3( 0.0 );
				#endif
			}
		#endif
	#endif
#endif`,jf=`ToonMaterial material;
material.diffuseColor = diffuseColor.rgb;`,Jf=`varying vec3 vViewPosition;
struct ToonMaterial {
	vec3 diffuseColor;
};
void RE_Direct_Toon( const in IncidentLight directLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in ToonMaterial material, inout ReflectedLight reflectedLight ) {
	vec3 irradiance = getGradientIrradiance( geometryNormal, directLight.direction ) * directLight.color;
	reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
void RE_IndirectDiffuse_Toon( const in vec3 irradiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in ToonMaterial material, inout ReflectedLight reflectedLight ) {
	reflectedLight.indirectDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
#define RE_Direct				RE_Direct_Toon
#define RE_IndirectDiffuse		RE_IndirectDiffuse_Toon`,Kf=`BlinnPhongMaterial material;
material.diffuseColor = diffuseColor.rgb;
material.specularColor = specular;
material.specularShininess = shininess;
material.specularStrength = specularStrength;`,Qf=`varying vec3 vViewPosition;
struct BlinnPhongMaterial {
	vec3 diffuseColor;
	vec3 specularColor;
	float specularShininess;
	float specularStrength;
};
void RE_Direct_BlinnPhong( const in IncidentLight directLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in BlinnPhongMaterial material, inout ReflectedLight reflectedLight ) {
	float dotNL = saturate( dot( geometryNormal, directLight.direction ) );
	vec3 irradiance = dotNL * directLight.color;
	reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
	reflectedLight.directSpecular += irradiance * BRDF_BlinnPhong( directLight.direction, geometryViewDir, geometryNormal, material.specularColor, material.specularShininess ) * material.specularStrength;
}
void RE_IndirectDiffuse_BlinnPhong( const in vec3 irradiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in BlinnPhongMaterial material, inout ReflectedLight reflectedLight ) {
	reflectedLight.indirectDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
#define RE_Direct				RE_Direct_BlinnPhong
#define RE_IndirectDiffuse		RE_IndirectDiffuse_BlinnPhong`,ep=`PhysicalMaterial material;
material.diffuseColor = diffuseColor.rgb;
material.diffuseContribution = diffuseColor.rgb * ( 1.0 - metalnessFactor );
material.metalness = metalnessFactor;
vec3 dxy = max( abs( dFdx( nonPerturbedNormal ) ), abs( dFdy( nonPerturbedNormal ) ) );
float geometryRoughness = max( max( dxy.x, dxy.y ), dxy.z );
material.roughness = max( roughnessFactor, 0.0525 );material.roughness += geometryRoughness;
material.roughness = min( material.roughness, 1.0 );
#ifdef IOR
	material.ior = ior;
	#ifdef USE_SPECULAR
		float specularIntensityFactor = specularIntensity;
		vec3 specularColorFactor = specularColor;
		#ifdef USE_SPECULAR_COLORMAP
			specularColorFactor *= texture2D( specularColorMap, vSpecularColorMapUv ).rgb;
		#endif
		#ifdef USE_SPECULAR_INTENSITYMAP
			specularIntensityFactor *= texture2D( specularIntensityMap, vSpecularIntensityMapUv ).a;
		#endif
		material.specularF90 = mix( specularIntensityFactor, 1.0, metalnessFactor );
	#else
		float specularIntensityFactor = 1.0;
		vec3 specularColorFactor = vec3( 1.0 );
		material.specularF90 = 1.0;
	#endif
	material.specularColor = min( pow2( ( material.ior - 1.0 ) / ( material.ior + 1.0 ) ) * specularColorFactor, vec3( 1.0 ) ) * specularIntensityFactor;
	material.specularColorBlended = mix( material.specularColor, diffuseColor.rgb, metalnessFactor );
#else
	material.specularColor = vec3( 0.04 );
	material.specularColorBlended = mix( material.specularColor, diffuseColor.rgb, metalnessFactor );
	material.specularF90 = 1.0;
#endif
#ifdef USE_CLEARCOAT
	material.clearcoat = clearcoat;
	material.clearcoatRoughness = clearcoatRoughness;
	material.clearcoatF0 = vec3( 0.04 );
	material.clearcoatF90 = 1.0;
	#ifdef USE_CLEARCOATMAP
		material.clearcoat *= texture2D( clearcoatMap, vClearcoatMapUv ).x;
	#endif
	#ifdef USE_CLEARCOAT_ROUGHNESSMAP
		material.clearcoatRoughness *= texture2D( clearcoatRoughnessMap, vClearcoatRoughnessMapUv ).y;
	#endif
	material.clearcoat = saturate( material.clearcoat );	material.clearcoatRoughness = max( material.clearcoatRoughness, 0.0525 );
	material.clearcoatRoughness += geometryRoughness;
	material.clearcoatRoughness = min( material.clearcoatRoughness, 1.0 );
#endif
#ifdef USE_DISPERSION
	material.dispersion = dispersion;
#endif
#ifdef USE_RETROREFLECTION
	material.retroreflectivity = retroreflectivity;
#endif
#ifdef USE_IRIDESCENCE
	material.iridescence = iridescence;
	material.iridescenceIOR = iridescenceIOR;
	#ifdef USE_IRIDESCENCEMAP
		material.iridescence *= texture2D( iridescenceMap, vIridescenceMapUv ).r;
	#endif
	#ifdef USE_IRIDESCENCE_THICKNESSMAP
		material.iridescenceThickness = (iridescenceThicknessMaximum - iridescenceThicknessMinimum) * texture2D( iridescenceThicknessMap, vIridescenceThicknessMapUv ).g + iridescenceThicknessMinimum;
	#else
		material.iridescenceThickness = iridescenceThicknessMaximum;
	#endif
#endif
#ifdef USE_SHEEN
	material.sheenColor = sheenColor;
	#ifdef USE_SHEEN_COLORMAP
		material.sheenColor *= texture2D( sheenColorMap, vSheenColorMapUv ).rgb;
	#endif
	material.sheenRoughness = clamp( sheenRoughness, 0.0001, 1.0 );
	#ifdef USE_SHEEN_ROUGHNESSMAP
		material.sheenRoughness *= texture2D( sheenRoughnessMap, vSheenRoughnessMapUv ).a;
	#endif
#endif
#ifdef USE_ANISOTROPY
	#ifdef USE_ANISOTROPYMAP
		mat2 anisotropyMat = mat2( anisotropyVector.x, anisotropyVector.y, - anisotropyVector.y, anisotropyVector.x );
		vec3 anisotropyPolar = texture2D( anisotropyMap, vAnisotropyMapUv ).rgb;
		vec2 anisotropyV = anisotropyMat * normalize( 2.0 * anisotropyPolar.rg - vec2( 1.0 ) ) * anisotropyPolar.b;
	#else
		vec2 anisotropyV = anisotropyVector;
	#endif
	material.anisotropy = length( anisotropyV );
	if( material.anisotropy == 0.0 ) {
		anisotropyV = vec2( 1.0, 0.0 );
	} else {
		anisotropyV /= material.anisotropy;
		material.anisotropy = saturate( material.anisotropy );
	}
	material.alphaT = mix( pow2( material.roughness ), 1.0, pow2( material.anisotropy ) );
	material.anisotropyT = tbn[ 0 ] * anisotropyV.x + tbn[ 1 ] * anisotropyV.y;
	material.anisotropyB = tbn[ 1 ] * anisotropyV.x - tbn[ 0 ] * anisotropyV.y;
#endif`,tp=`uniform sampler2D dfgLUT;
struct PhysicalMaterial {
	vec3 diffuseColor;
	vec3 diffuseContribution;
	vec3 specularColor;
	vec3 specularColorBlended;
	float roughness;
	float metalness;
	float specularF90;
	float dispersion;
	vec2 dfg;
	vec3 multiScatteringCompensation;
	#ifdef USE_RETROREFLECTION
		float retroreflectivity;
	#endif
	#ifdef USE_CLEARCOAT
		float clearcoat;
		float clearcoatRoughness;
		vec3 clearcoatF0;
		float clearcoatF90;
	#endif
	#ifdef USE_IRIDESCENCE
		float iridescence;
		float iridescenceIOR;
		float iridescenceThickness;
		vec3 iridescenceFresnel;
		vec3 iridescenceF0Dielectric;
		vec3 iridescenceF0Metallic;
	#endif
	#ifdef USE_SHEEN
		vec3 sheenColor;
		float sheenRoughness;
	#endif
	#ifdef IOR
		float ior;
	#endif
	#ifdef USE_TRANSMISSION
		float transmission;
		float transmissionAlpha;
		float thickness;
		float attenuationDistance;
		vec3 attenuationColor;
	#endif
	#ifdef USE_ANISOTROPY
		float anisotropy;
		float alphaT;
		vec3 anisotropyT;
		vec3 anisotropyB;
	#endif
};
vec3 clearcoatSpecularDirect = vec3( 0.0 );
vec3 clearcoatSpecularIndirect = vec3( 0.0 );
vec3 sheenSpecularDirect = vec3( 0.0 );
vec3 sheenSpecularIndirect = vec3(0.0 );
vec3 Schlick_to_F0( const in vec3 f, const in float f90, const in float dotVH ) {
    float x = clamp( 1.0 - dotVH, 0.0, 1.0 );
    float x2 = x * x;
    float x5 = clamp( x * x2 * x2, 0.0, 0.9999 );
    return ( f - vec3( f90 ) * x5 ) / ( 1.0 - x5 );
}
float V_GGX_SmithCorrelated( const in float alpha, const in float dotNL, const in float dotNV ) {
	float a2 = pow2( alpha );
	float gv = dotNL * sqrt( a2 + ( 1.0 - a2 ) * pow2( dotNV ) );
	float gl = dotNV * sqrt( a2 + ( 1.0 - a2 ) * pow2( dotNL ) );
	return 0.5 / max( gv + gl, EPSILON );
}
float D_GGX( const in float alpha, const in float dotNH ) {
	float a2 = pow2( alpha );
	float denom = pow2( dotNH ) * ( a2 - 1.0 ) + 1.0;
	return RECIPROCAL_PI * a2 / pow2( denom );
}
#ifdef USE_ANISOTROPY
	float V_GGX_SmithCorrelated_Anisotropic( const in float alphaT, const in float alphaB, const in float dotTV, const in float dotBV, const in float dotTL, const in float dotBL, const in float dotNV, const in float dotNL ) {
		float gv = dotNL * length( vec3( alphaT * dotTV, alphaB * dotBV, dotNV ) );
		float gl = dotNV * length( vec3( alphaT * dotTL, alphaB * dotBL, dotNL ) );
		return 0.5 / max( gv + gl, EPSILON );
	}
	float D_GGX_Anisotropic( const in float alphaT, const in float alphaB, const in float dotNH, const in float dotTH, const in float dotBH ) {
		float a2 = alphaT * alphaB;
		highp vec3 v = vec3( alphaB * dotTH, alphaT * dotBH, a2 * dotNH );
		highp float v2 = dot( v, v );
		float w2 = a2 / v2;
		return RECIPROCAL_PI * a2 * pow2 ( w2 );
	}
#endif
#ifdef USE_CLEARCOAT
	vec3 BRDF_GGX_Clearcoat( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, const in PhysicalMaterial material) {
		vec3 f0 = material.clearcoatF0;
		float f90 = material.clearcoatF90;
		float roughness = material.clearcoatRoughness;
		float alpha = pow2( roughness );
		vec3 halfDir = normalize( lightDir + viewDir );
		float dotNL = saturate( dot( normal, lightDir ) );
		float dotNV = saturate( dot( normal, viewDir ) );
		float dotNH = saturate( dot( normal, halfDir ) );
		float dotVH = saturate( dot( viewDir, halfDir ) );
		vec3 F = F_Schlick( f0, f90, dotVH );
		float V = V_GGX_SmithCorrelated( alpha, dotNL, dotNV );
		float D = D_GGX( alpha, dotNH );
		return F * ( V * D );
	}
#endif
vec3 BRDF_GGX( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, const in PhysicalMaterial material ) {
	vec3 f0 = material.specularColorBlended;
	float f90 = material.specularF90;
	float roughness = material.roughness;
	float alpha = pow2( roughness );
	vec3 halfDir = normalize( lightDir + viewDir );
	float dotNL = saturate( dot( normal, lightDir ) );
	float dotNV = saturate( dot( normal, viewDir ) );
	float dotNH = saturate( dot( normal, halfDir ) );
	float dotVH = saturate( dot( viewDir, halfDir ) );
	vec3 F = F_Schlick( f0, f90, dotVH );
	#ifdef USE_IRIDESCENCE
		F = mix( F, material.iridescenceFresnel, material.iridescence );
	#endif
	#ifdef USE_ANISOTROPY
		float dotTL = dot( material.anisotropyT, lightDir );
		float dotTV = dot( material.anisotropyT, viewDir );
		float dotTH = dot( material.anisotropyT, halfDir );
		float dotBL = dot( material.anisotropyB, lightDir );
		float dotBV = dot( material.anisotropyB, viewDir );
		float dotBH = dot( material.anisotropyB, halfDir );
		float V = V_GGX_SmithCorrelated_Anisotropic( material.alphaT, alpha, dotTV, dotBV, dotTL, dotBL, dotNV, dotNL );
		float D = D_GGX_Anisotropic( material.alphaT, alpha, dotNH, dotTH, dotBH );
	#else
		float V = V_GGX_SmithCorrelated( alpha, dotNL, dotNV );
		float D = D_GGX( alpha, dotNH );
	#endif
	return F * ( V * D );
}
vec2 LTC_Uv( const in vec3 N, const in vec3 V, const in float roughness ) {
	const float LUT_SIZE = 64.0;
	const float LUT_SCALE = ( LUT_SIZE - 1.0 ) / LUT_SIZE;
	const float LUT_BIAS = 0.5 / LUT_SIZE;
	float dotNV = saturate( dot( N, V ) );
	vec2 uv = vec2( roughness, sqrt( 1.0 - dotNV ) );
	uv = uv * LUT_SCALE + LUT_BIAS;
	return uv;
}
float LTC_ClippedSphereFormFactor( const in vec3 f ) {
	float l = length( f );
	return max( ( l * l + f.z ) / ( l + 1.0 ), 0.0 );
}
vec3 LTC_EdgeVectorFormFactor( const in vec3 v1, const in vec3 v2 ) {
	float x = dot( v1, v2 );
	float y = abs( x );
	float a = 0.8543985 + ( 0.4965155 + 0.0145206 * y ) * y;
	float b = 3.4175940 + ( 4.1616724 + y ) * y;
	float v = a / b;
	float theta_sintheta = ( x > 0.0 ) ? v : 0.5 * inversesqrt( max( 1.0 - x * x, 1e-7 ) ) - v;
	return cross( v1, v2 ) * theta_sintheta;
}
vec3 LTC_Evaluate( const in vec3 N, const in vec3 V, const in vec3 P, const in mat3 mInv, const in vec3 rectCoords[ 4 ] ) {
	vec3 v1 = rectCoords[ 1 ] - rectCoords[ 0 ];
	vec3 v2 = rectCoords[ 3 ] - rectCoords[ 0 ];
	vec3 lightNormal = cross( v1, v2 );
	if( dot( lightNormal, P - rectCoords[ 0 ] ) < 0.0 ) return vec3( 0.0 );
	vec3 T1, T2;
	T1 = normalize( V - N * dot( V, N ) );
	T2 = - cross( N, T1 );
	mat3 mat = mInv * transpose( mat3( T1, T2, N ) );
	vec3 coords[ 4 ];
	coords[ 0 ] = mat * ( rectCoords[ 0 ] - P );
	coords[ 1 ] = mat * ( rectCoords[ 1 ] - P );
	coords[ 2 ] = mat * ( rectCoords[ 2 ] - P );
	coords[ 3 ] = mat * ( rectCoords[ 3 ] - P );
	coords[ 0 ] = normalize( coords[ 0 ] );
	coords[ 1 ] = normalize( coords[ 1 ] );
	coords[ 2 ] = normalize( coords[ 2 ] );
	coords[ 3 ] = normalize( coords[ 3 ] );
	vec3 vectorFormFactor = vec3( 0.0 );
	vectorFormFactor += LTC_EdgeVectorFormFactor( coords[ 0 ], coords[ 1 ] );
	vectorFormFactor += LTC_EdgeVectorFormFactor( coords[ 1 ], coords[ 2 ] );
	vectorFormFactor += LTC_EdgeVectorFormFactor( coords[ 2 ], coords[ 3 ] );
	vectorFormFactor += LTC_EdgeVectorFormFactor( coords[ 3 ], coords[ 0 ] );
	float result = LTC_ClippedSphereFormFactor( vectorFormFactor );
	return vec3( result );
}
#if defined( USE_SHEEN )
float D_Charlie( float roughness, float dotNH ) {
	float alpha = pow2( roughness );
	float invAlpha = 1.0 / alpha;
	float cos2h = dotNH * dotNH;
	float sin2h = max( 1.0 - cos2h, 0.0078125 );
	return ( 2.0 + invAlpha ) * pow( sin2h, invAlpha * 0.5 ) / ( 2.0 * PI );
}
float V_Neubelt( float dotNV, float dotNL ) {
	return saturate( 1.0 / ( 4.0 * ( dotNL + dotNV - dotNL * dotNV ) ) );
}
vec3 BRDF_Sheen( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, vec3 sheenColor, const in float sheenRoughness ) {
	vec3 halfDir = normalize( lightDir + viewDir );
	float dotNL = saturate( dot( normal, lightDir ) );
	float dotNV = saturate( dot( normal, viewDir ) );
	float dotNH = saturate( dot( normal, halfDir ) );
	float D = D_Charlie( sheenRoughness, dotNH );
	float V = V_Neubelt( dotNV, dotNL );
	return sheenColor * ( D * V );
}
#endif
float IBLSheenBRDF( const in vec3 normal, const in vec3 viewDir, const in float roughness ) {
	float dotNV = saturate( dot( normal, viewDir ) );
	float r2 = roughness * roughness;
	float rInv = 1.0 / ( roughness + 0.1 );
	float a = -1.9362 + 1.0678 * roughness + 0.4573 * r2 - 0.8469 * rInv;
	float b = -0.6014 + 0.5538 * roughness - 0.4670 * r2 - 0.1255 * rInv;
	float DG = exp( a * dotNV + b );
	return saturate( DG );
}
vec3 EnvironmentBRDF( const in vec3 normal, const in vec3 viewDir, const in vec3 specularColor, const in float specularF90, const in float roughness ) {
	float dotNV = saturate( dot( normal, viewDir ) );
	vec2 fab = texture2D( dfgLUT, vec2( roughness, dotNV ) ).rg;
	return specularColor * fab.x + specularF90 * fab.y;
}
#ifdef USE_IRIDESCENCE
void computeMultiscatteringIridescence( const in vec2 fab, const in vec3 specularColor, const in float specularF90, const in float iridescence, const in vec3 iridescenceF0, inout vec3 singleScatter, inout vec3 multiScatter ) {
#else
void computeMultiscattering( const in vec2 fab, const in vec3 specularColor, const in float specularF90, inout vec3 singleScatter, inout vec3 multiScatter ) {
#endif
	#ifdef USE_IRIDESCENCE
		vec3 Fr = mix( specularColor, iridescenceF0, iridescence );
	#else
		vec3 Fr = specularColor;
	#endif
	vec3 FssEss = Fr * fab.x + specularF90 * fab.y;
	float Ess = fab.x + fab.y;
	float Ems = 1.0 - Ess;
	vec3 Favg = Fr + ( 1.0 - Fr ) * 0.047619;	vec3 Fms = FssEss * Favg / ( 1.0 - Ems * Favg );
	singleScatter += FssEss;
	multiScatter += Fms * Ems;
}
#if NUM_RECT_AREA_LIGHTS > 0
	void RE_Direct_RectArea_Physical( const in RectAreaLight rectAreaLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in PhysicalMaterial material, inout ReflectedLight reflectedLight ) {
		vec3 normal = geometryNormal;
		vec3 viewDir = geometryViewDir;
		vec3 position = geometryPosition;
		vec3 lightPos = rectAreaLight.position;
		vec3 halfWidth = rectAreaLight.halfWidth;
		vec3 halfHeight = rectAreaLight.halfHeight;
		vec3 lightColor = rectAreaLight.color;
		float roughness = material.roughness;
		vec3 rectCoords[ 4 ];
		rectCoords[ 0 ] = lightPos + halfWidth - halfHeight;		rectCoords[ 1 ] = lightPos - halfWidth - halfHeight;
		rectCoords[ 2 ] = lightPos - halfWidth + halfHeight;
		rectCoords[ 3 ] = lightPos + halfWidth + halfHeight;
		vec2 uv = LTC_Uv( normal, viewDir, roughness );
		vec4 t1 = texture2D( ltc_1, uv );
		vec4 t2 = texture2D( ltc_2, uv );
		mat3 mInv = mat3(
			vec3( t1.x, 0, t1.y ),
			vec3(    0, 1,    0 ),
			vec3( t1.z, 0, t1.w )
		);
		vec3 fresnel = ( material.specularColorBlended * t2.x + ( material.specularF90 - material.specularColorBlended ) * t2.y );
		reflectedLight.directSpecular += lightColor * fresnel * LTC_Evaluate( normal, viewDir, position, mInv, rectCoords );
		reflectedLight.directDiffuse += lightColor * material.diffuseContribution * LTC_Evaluate( normal, viewDir, position, mat3( 1.0 ), rectCoords );
		#ifdef USE_CLEARCOAT
			vec3 Ncc = geometryClearcoatNormal;
			vec2 uvClearcoat = LTC_Uv( Ncc, viewDir, material.clearcoatRoughness );
			vec4 t1Clearcoat = texture2D( ltc_1, uvClearcoat );
			vec4 t2Clearcoat = texture2D( ltc_2, uvClearcoat );
			mat3 mInvClearcoat = mat3(
				vec3( t1Clearcoat.x, 0, t1Clearcoat.y ),
				vec3(             0, 1,             0 ),
				vec3( t1Clearcoat.z, 0, t1Clearcoat.w )
			);
			vec3 fresnelClearcoat = material.clearcoatF0 * t2Clearcoat.x + ( material.clearcoatF90 - material.clearcoatF0 ) * t2Clearcoat.y;
			clearcoatSpecularDirect += lightColor * fresnelClearcoat * LTC_Evaluate( Ncc, viewDir, position, mInvClearcoat, rectCoords );
		#endif
	}
#endif
void RE_Direct_Physical( const in IncidentLight directLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in PhysicalMaterial material, inout ReflectedLight reflectedLight ) {
	float dotNL = saturate( dot( geometryNormal, directLight.direction ) );
	vec3 irradiance = dotNL * directLight.color;
	#ifdef USE_CLEARCOAT
		float dotNLcc = saturate( dot( geometryClearcoatNormal, directLight.direction ) );
		vec3 ccIrradiance = dotNLcc * directLight.color;
		clearcoatSpecularDirect += ccIrradiance * BRDF_GGX_Clearcoat( directLight.direction, geometryViewDir, geometryClearcoatNormal, material );
	#endif
	#ifdef USE_SHEEN

		sheenSpecularDirect += irradiance * BRDF_Sheen( directLight.direction, geometryViewDir, geometryNormal, material.sheenColor, material.sheenRoughness );

		float sheenAlbedoV = IBLSheenBRDF( geometryNormal, geometryViewDir, material.sheenRoughness );
		float sheenAlbedoL = IBLSheenBRDF( geometryNormal, directLight.direction, material.sheenRoughness );

		float sheenEnergyComp = 1.0 - max3( material.sheenColor ) * max( sheenAlbedoV, sheenAlbedoL );

		irradiance *= sheenEnergyComp;

	#endif
	vec3 specularBRDF = BRDF_GGX( directLight.direction, geometryViewDir, geometryNormal, material );
	#ifdef USE_RETROREFLECTION
		vec3 retroViewDir = reflect( - geometryViewDir, geometryNormal );
		vec3 retroSpecularBRDF = BRDF_GGX( directLight.direction, retroViewDir, geometryNormal, material );
		specularBRDF = mix( specularBRDF, retroSpecularBRDF, saturate( material.retroreflectivity ) );
	#endif
	reflectedLight.directSpecular += irradiance * specularBRDF * material.multiScatteringCompensation;
	vec3 halfDir = normalize( directLight.direction + geometryViewDir );
	float dotVH = saturate( dot( geometryViewDir, halfDir ) );
	vec3 F = F_Schlick( material.specularColor, material.specularF90, dotVH );
	#ifdef USE_RETROREFLECTION
		vec3 retroHalfDir = normalize( directLight.direction + retroViewDir );
		float dotRetroVH = saturate( dot( retroViewDir, retroHalfDir ) );
		vec3 retroF = F_Schlick( material.specularColor, material.specularF90, dotRetroVH );
		F = mix( F, retroF, saturate( material.retroreflectivity ) );
	#endif
	reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseContribution ) * ( 1.0 - F );
}
void RE_IndirectDiffuse_Physical( const in vec3 irradiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in PhysicalMaterial material, inout ReflectedLight reflectedLight ) {
	vec3 singleScattering = vec3( 0.0 );
	vec3 multiScattering = vec3( 0.0 );
	#ifdef USE_IRIDESCENCE
		computeMultiscatteringIridescence( material.dfg, material.specularColor, material.specularF90, material.iridescence, material.iridescenceF0Dielectric, singleScattering, multiScattering );
	#else
		computeMultiscattering( material.dfg, material.specularColor, material.specularF90, singleScattering, multiScattering );
	#endif
	vec3 diffuse = irradiance * BRDF_Lambert( material.diffuseContribution ) * ( 1.0 - singleScattering - multiScattering );
	#ifdef USE_SHEEN
		float sheenAlbedo = IBLSheenBRDF( geometryNormal, geometryViewDir, material.sheenRoughness );
		sheenSpecularIndirect += irradiance * material.sheenColor * sheenAlbedo * RECIPROCAL_PI;
		float sheenEnergyComp = 1.0 - max3( material.sheenColor ) * sheenAlbedo;
		diffuse *= sheenEnergyComp;
	#endif
	reflectedLight.indirectDiffuse += diffuse;
}
void RE_IndirectSpecular_Physical( const in vec3 radiance, const in vec3 irradiance, const in vec3 clearcoatRadiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in PhysicalMaterial material, inout ReflectedLight reflectedLight) {
	#ifdef USE_CLEARCOAT
		clearcoatSpecularIndirect += clearcoatRadiance * EnvironmentBRDF( geometryClearcoatNormal, geometryViewDir, material.clearcoatF0, material.clearcoatF90, material.clearcoatRoughness );
	#endif
	#ifdef USE_SHEEN
		sheenSpecularIndirect += irradiance * material.sheenColor * IBLSheenBRDF( geometryNormal, geometryViewDir, material.sheenRoughness ) * RECIPROCAL_PI;
	#endif
	vec3 singleScatteringDielectric = vec3( 0.0 );
	vec3 multiScatteringDielectric = vec3( 0.0 );
	vec3 singleScatteringMetallic = vec3( 0.0 );
	vec3 multiScatteringMetallic = vec3( 0.0 );
	#ifdef USE_IRIDESCENCE
		computeMultiscatteringIridescence( material.dfg, material.specularColor, material.specularF90, material.iridescence, material.iridescenceF0Dielectric, singleScatteringDielectric, multiScatteringDielectric );
		computeMultiscatteringIridescence( material.dfg, material.diffuseColor, material.specularF90, material.iridescence, material.iridescenceF0Metallic, singleScatteringMetallic, multiScatteringMetallic );
	#else
		computeMultiscattering( material.dfg, material.specularColor, material.specularF90, singleScatteringDielectric, multiScatteringDielectric );
		computeMultiscattering( material.dfg, material.diffuseColor, material.specularF90, singleScatteringMetallic, multiScatteringMetallic );
	#endif
	vec3 singleScattering = mix( singleScatteringDielectric, singleScatteringMetallic, material.metalness );
	vec3 multiScattering = mix( multiScatteringDielectric, multiScatteringMetallic, material.metalness );
	vec3 totalScatteringDielectric = singleScatteringDielectric + multiScatteringDielectric;
	vec3 diffuse = material.diffuseContribution * ( 1.0 - totalScatteringDielectric );
	vec3 cosineWeightedIrradiance = irradiance * RECIPROCAL_PI;
	vec3 indirectSpecular = radiance * singleScattering;
	indirectSpecular += multiScattering * cosineWeightedIrradiance;
	vec3 indirectDiffuse = diffuse * cosineWeightedIrradiance;
	#ifdef USE_SHEEN
		float sheenAlbedo = IBLSheenBRDF( geometryNormal, geometryViewDir, material.sheenRoughness );
		float sheenEnergyComp = 1.0 - max3( material.sheenColor ) * sheenAlbedo;
		indirectSpecular *= sheenEnergyComp;
		indirectDiffuse *= sheenEnergyComp;
	#endif
	reflectedLight.indirectSpecular += indirectSpecular;
	reflectedLight.indirectDiffuse += indirectDiffuse;
}
#define RE_Direct				RE_Direct_Physical
#define RE_Direct_RectArea		RE_Direct_RectArea_Physical
#define RE_IndirectDiffuse		RE_IndirectDiffuse_Physical
#define RE_IndirectSpecular		RE_IndirectSpecular_Physical
float computeSpecularOcclusion( const in float dotNV, const in float ambientOcclusion, const in float roughness ) {
	return saturate( pow( dotNV + ambientOcclusion, exp2( - 16.0 * roughness - 1.0 ) ) - 1.0 + ambientOcclusion );
}`,np=`
vec3 geometryPosition = - vViewPosition;
vec3 geometryNormal = normal;
vec3 geometryViewDir = ( isOrthographic ) ? vec3( 0, 0, 1 ) : normalize( vViewPosition );
vec3 geometryClearcoatNormal = vec3( 0.0 );
#ifdef USE_CLEARCOAT
	geometryClearcoatNormal = clearcoatNormal;
#endif
#ifdef USE_IRIDESCENCE
	float dotNVi = saturate( dot( normal, geometryViewDir ) );
	if ( material.iridescenceThickness == 0.0 ) {
		material.iridescence = 0.0;
	} else {
		material.iridescence = saturate( material.iridescence );
	}
	if ( material.iridescence > 0.0 ) {
		vec3 iridescenceFresnelDielectric = evalIridescence( 1.0, material.iridescenceIOR, dotNVi, material.iridescenceThickness, material.specularColor );
		vec3 iridescenceFresnelMetallic = evalIridescence( 1.0, material.iridescenceIOR, dotNVi, material.iridescenceThickness, material.diffuseColor );
		material.iridescenceFresnel = mix( iridescenceFresnelDielectric, iridescenceFresnelMetallic, material.metalness );
		material.iridescenceF0Dielectric = Schlick_to_F0( iridescenceFresnelDielectric, 1.0, dotNVi );
		material.iridescenceF0Metallic = Schlick_to_F0( iridescenceFresnelMetallic, 1.0, dotNVi );
	}
#endif
#ifdef STANDARD
	float dotNVms = saturate( dot( geometryNormal, geometryViewDir ) );
	material.dfg = texture2D( dfgLUT, vec2( material.roughness, dotNVms ) ).rg;
	#if ( NUM_SUN_LIGHTS > 0 || NUM_DIR_LIGHTS > 0 || NUM_POINT_LIGHTS > 0 || NUM_SPOT_LIGHTS > 0 )
		float EssMs = material.dfg.x + material.dfg.y;
		material.multiScatteringCompensation = 1.0 + material.specularColorBlended * ( 1.0 / EssMs - 1.0 );
	#endif
#endif
IncidentLight directLight;
#if ( NUM_POINT_LIGHTS > 0 ) && defined( RE_Direct )
	PointLight pointLight;
	#if defined( USE_SHADOWMAP ) && NUM_POINT_LIGHT_SHADOWS > 0
	PointLightShadow pointLightShadow;
	#endif
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_POINT_LIGHTS; i ++ ) {
		pointLight = pointLights[ i ];
		getPointLightInfo( pointLight, geometryPosition, directLight );
		#if defined( USE_SHADOWMAP ) && ( UNROLLED_LOOP_INDEX < NUM_POINT_LIGHT_SHADOWS ) && ( defined( SHADOWMAP_TYPE_PCF ) || defined( SHADOWMAP_TYPE_BASIC ) )
		pointLightShadow = pointLightShadows[ i ];
		directLight.color *= ( directLight.visible && receiveShadow ) ? getPointShadow( pointShadowMap[ i ], pointLightShadow.shadowMapSize, pointLightShadow.shadowIntensity, pointLightShadow.shadowBias, pointLightShadow.shadowRadius, vPointShadowCoord[ i ], pointLightShadow.shadowCameraNear, pointLightShadow.shadowCameraFar ) : 1.0;
		#endif
		RE_Direct( directLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if ( NUM_SPOT_LIGHTS > 0 ) && defined( RE_Direct )
	SpotLight spotLight;
	vec4 spotColor;
	vec3 spotLightCoord;
	bool inSpotLightMap;
	#if defined( USE_SHADOWMAP ) && NUM_SPOT_LIGHT_SHADOWS > 0
	SpotLightShadow spotLightShadow;
	#endif
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_SPOT_LIGHTS; i ++ ) {
		spotLight = spotLights[ i ];
		getSpotLightInfo( spotLight, geometryPosition, directLight );
		#if ( UNROLLED_LOOP_INDEX < NUM_SPOT_LIGHT_SHADOWS_WITH_MAPS )
		#define SPOT_LIGHT_MAP_INDEX UNROLLED_LOOP_INDEX
		#elif ( UNROLLED_LOOP_INDEX < NUM_SPOT_LIGHT_SHADOWS )
		#define SPOT_LIGHT_MAP_INDEX NUM_SPOT_LIGHT_MAPS
		#else
		#define SPOT_LIGHT_MAP_INDEX ( UNROLLED_LOOP_INDEX - NUM_SPOT_LIGHT_SHADOWS + NUM_SPOT_LIGHT_SHADOWS_WITH_MAPS )
		#endif
		#if ( SPOT_LIGHT_MAP_INDEX < NUM_SPOT_LIGHT_MAPS )
			spotLightCoord = vSpotLightCoord[ i ].xyz / vSpotLightCoord[ i ].w;
			inSpotLightMap = all( lessThan( abs( spotLightCoord * 2. - 1. ), vec3( 1.0 ) ) );
			spotColor = texture2D( spotLightMap[ SPOT_LIGHT_MAP_INDEX ], spotLightCoord.xy );
			directLight.color = inSpotLightMap ? directLight.color * spotColor.rgb : directLight.color;
		#endif
		#undef SPOT_LIGHT_MAP_INDEX
		#if defined( USE_SHADOWMAP ) && ( UNROLLED_LOOP_INDEX < NUM_SPOT_LIGHT_SHADOWS )
		spotLightShadow = spotLightShadows[ i ];
		directLight.color *= ( directLight.visible && receiveShadow ) ? getShadow( spotShadowMap[ i ], spotLightShadow.shadowMapSize, spotLightShadow.shadowIntensity, spotLightShadow.shadowBias, spotLightShadow.shadowRadius, vSpotLightCoord[ i ] ) : 1.0;
		#endif
		RE_Direct( directLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if ( NUM_SUN_LIGHTS > 0 ) && defined( RE_Direct )
	SunLight sunLight;
	#if defined( USE_SHADOWMAP ) && NUM_SUN_LIGHT_SHADOWS > 0
	SunLightShadow sunLightShadow;
	#endif
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_SUN_LIGHTS; i ++ ) {
		sunLight = sunLights[ i ];
		getSunLightInfo( sunLight, directLight );
		#if defined( USE_SHADOWMAP ) && ( UNROLLED_LOOP_INDEX < NUM_SUN_LIGHT_SHADOWS )
		sunLightShadow = sunLightShadows[ i ];
		directLight.color *= ( directLight.visible && receiveShadow ) ? getSunShadow( sunShadowMap[ i ], sunLightShadow, UNROLLED_LOOP_INDEX ) : 1.0;
		#endif
		RE_Direct( directLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if ( NUM_DIR_LIGHTS > 0 ) && defined( RE_Direct )
	DirectionalLight directionalLight;
	#if defined( USE_SHADOWMAP ) && NUM_DIR_LIGHT_SHADOWS > 0
	DirectionalLightShadow directionalLightShadow;
	#endif
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_DIR_LIGHTS; i ++ ) {
		directionalLight = directionalLights[ i ];
		getDirectionalLightInfo( directionalLight, directLight );
		#if defined( USE_SHADOWMAP ) && ( UNROLLED_LOOP_INDEX < NUM_DIR_LIGHT_SHADOWS )
		directionalLightShadow = directionalLightShadows[ i ];
		directLight.color *= ( directLight.visible && receiveShadow ) ? getShadow( directionalShadowMap[ i ], directionalLightShadow.shadowMapSize, directionalLightShadow.shadowIntensity, directionalLightShadow.shadowBias, directionalLightShadow.shadowRadius, vDirectionalShadowCoord[ i ] ) : 1.0;
		#endif
		RE_Direct( directLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if ( NUM_RECT_AREA_LIGHTS > 0 ) && defined( RE_Direct_RectArea )
	RectAreaLight rectAreaLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_RECT_AREA_LIGHTS; i ++ ) {
		rectAreaLight = rectAreaLights[ i ];
		RE_Direct_RectArea( rectAreaLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if defined( RE_IndirectDiffuse )
	vec3 iblIrradiance = vec3( 0.0 );
	vec3 irradiance = getAmbientLightIrradiance( ambientLightColor );
	#if defined( USE_LIGHT_PROBES )
		irradiance += getLightProbeIrradiance( lightProbe, geometryNormal );
	#endif
	#if ( NUM_HEMI_LIGHTS > 0 )
		#pragma unroll_loop_start
		for ( int i = 0; i < NUM_HEMI_LIGHTS; i ++ ) {
			irradiance += getHemisphereLightIrradiance( hemisphereLights[ i ], geometryNormal );
		}
		#pragma unroll_loop_end
	#endif
	#ifdef USE_LIGHT_PROBES_GRID
		vec3 probeWorldPos = ( ( vec4( geometryPosition, 1.0 ) - viewMatrix[ 3 ] ) * viewMatrix ).xyz;
		vec3 probeWorldNormal = transformNormalByInverseViewMatrix( geometryNormal, viewMatrix );
		irradiance += getLightProbeGridIrradiance( probeWorldPos, probeWorldNormal );
	#endif
#endif
#if defined( RE_IndirectSpecular )
	vec3 radiance = vec3( 0.0 );
	vec3 clearcoatRadiance = vec3( 0.0 );
#endif`,ip=`#if defined( RE_IndirectDiffuse )
	#ifdef USE_LIGHTMAP
		vec4 lightMapTexel = texture2D( lightMap, vLightMapUv );
		vec3 lightMapIrradiance = lightMapTexel.rgb * lightMapIntensity;
		irradiance += lightMapIrradiance;
	#endif
	#if defined( USE_ENVMAP ) && defined( ENVMAP_TYPE_CUBE_UV )
		#if defined( STANDARD ) || defined( LAMBERT ) || defined( PHONG )
			iblIrradiance += getIBLIrradiance( geometryNormal );
		#endif
	#endif
#endif
#if defined( USE_ENVMAP ) && defined( RE_IndirectSpecular )
	#ifdef USE_ANISOTROPY
		vec3 iblRadiance = getIBLAnisotropyRadiance( geometryViewDir, geometryNormal, material.roughness, material.anisotropyB, material.anisotropy );
	#else
		vec3 iblRadiance = getIBLRadiance( geometryViewDir, geometryNormal, material.roughness );
	#endif
	#ifdef USE_RETROREFLECTION
		#ifdef USE_ANISOTROPY
			vec3 retroIBLRadiance = getIBLAnisotropyRetroRadiance( geometryViewDir, geometryNormal, material.roughness, material.anisotropyB, material.anisotropy );
		#else
			vec3 retroIBLRadiance = getIBLRetroRadiance( geometryViewDir, geometryNormal, material.roughness );
		#endif
		iblRadiance = mix( iblRadiance, retroIBLRadiance, saturate( material.retroreflectivity ) );
	#endif
	radiance += iblRadiance;
	#ifdef USE_CLEARCOAT
		clearcoatRadiance += getIBLRadiance( geometryViewDir, geometryClearcoatNormal, material.clearcoatRoughness );
	#endif
#endif`,sp=`#if defined( RE_IndirectDiffuse )
	#if defined( LAMBERT ) || defined( PHONG )
		irradiance += iblIrradiance;
	#endif
	RE_IndirectDiffuse( irradiance, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
#endif
#if defined( RE_IndirectSpecular )
	RE_IndirectSpecular( radiance, iblIrradiance, clearcoatRadiance, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
#endif`,rp=`#ifdef USE_LIGHT_PROBES_GRID
uniform highp sampler3D probesSH;
uniform vec3 probesMin;
uniform vec3 probesMax;
uniform vec3 probesResolution;
vec3 getLightProbeGridIrradiance( vec3 worldPos, vec3 worldNormal ) {
	vec3 res = probesResolution;
	vec3 gridRange = probesMax - probesMin;
	vec3 resMinusOne = res - 1.0;
	vec3 probeSpacing = gridRange / resMinusOne;
	vec3 samplePos = worldPos + worldNormal * probeSpacing * 0.5;
	vec3 uvw = clamp( ( samplePos - probesMin ) / gridRange, 0.0, 1.0 );
	uvw = uvw * resMinusOne / res + 0.5 / res;
	float nz          = res.z;
	float paddedSlices = nz + 2.0;
	float atlasDepth  = 7.0 * paddedSlices;
	float uvZBase     = uvw.z * nz + 1.0;
	vec4 s0 = texture( probesSH, vec3( uvw.xy, ( uvZBase                       ) / atlasDepth ) );
	vec4 s1 = texture( probesSH, vec3( uvw.xy, ( uvZBase +       paddedSlices   ) / atlasDepth ) );
	vec4 s2 = texture( probesSH, vec3( uvw.xy, ( uvZBase + 2.0 * paddedSlices   ) / atlasDepth ) );
	vec4 s3 = texture( probesSH, vec3( uvw.xy, ( uvZBase + 3.0 * paddedSlices   ) / atlasDepth ) );
	vec4 s4 = texture( probesSH, vec3( uvw.xy, ( uvZBase + 4.0 * paddedSlices   ) / atlasDepth ) );
	vec4 s5 = texture( probesSH, vec3( uvw.xy, ( uvZBase + 5.0 * paddedSlices   ) / atlasDepth ) );
	vec4 s6 = texture( probesSH, vec3( uvw.xy, ( uvZBase + 6.0 * paddedSlices   ) / atlasDepth ) );
	vec3 c0 = s0.xyz;
	vec3 c1 = vec3( s0.w, s1.xy );
	vec3 c2 = vec3( s1.zw, s2.x );
	vec3 c3 = s2.yzw;
	vec3 c4 = s3.xyz;
	vec3 c5 = vec3( s3.w, s4.xy );
	vec3 c6 = vec3( s4.zw, s5.x );
	vec3 c7 = s5.yzw;
	vec3 c8 = s6.xyz;
	float x = worldNormal.x, y = worldNormal.y, z = worldNormal.z;
	vec3 result = c0 * 0.886227;
	result += c1 * 2.0 * 0.511664 * y;
	result += c2 * 2.0 * 0.511664 * z;
	result += c3 * 2.0 * 0.511664 * x;
	result += c4 * 2.0 * 0.429043 * x * y;
	result += c5 * 2.0 * 0.429043 * y * z;
	result += c6 * ( 0.743125 * z * z - 0.247708 );
	result += c7 * 2.0 * 0.429043 * x * z;
	result += c8 * 0.429043 * ( x * x - y * y );
	return max( result, vec3( 0.0 ) );
}
#endif`,ap=`#if defined( USE_LOGARITHMIC_DEPTH_BUFFER )
	gl_FragDepth = vIsPerspective == 0.0 ? gl_FragCoord.z : log2( vFragDepth ) * logDepthBufFC * 0.5;
#endif`,op=`#if defined( USE_LOGARITHMIC_DEPTH_BUFFER )
	uniform float logDepthBufFC;
	varying float vFragDepth;
	varying float vIsPerspective;
#endif`,lp=`#ifdef USE_LOGARITHMIC_DEPTH_BUFFER
	varying float vFragDepth;
	varying float vIsPerspective;
#endif`,cp=`#ifdef USE_LOGARITHMIC_DEPTH_BUFFER
	vFragDepth = 1.0 + gl_Position.w;
	vIsPerspective = float( isPerspectiveMatrix( projectionMatrix ) );
#endif`,up=`#ifdef USE_MAP
	vec4 sampledDiffuseColor = texture2D( map, vMapUv );
	#ifdef DECODE_VIDEO_TEXTURE
		sampledDiffuseColor = sRGBTransferEOTF( sampledDiffuseColor );
	#endif
	diffuseColor *= sampledDiffuseColor;
#endif`,hp=`#ifdef USE_MAP
	uniform sampler2D map;
#endif`,dp=`#if defined( USE_MAP ) || defined( USE_ALPHAMAP )
	#if defined( USE_POINTS_UV )
		vec2 uv = vUv;
	#else
		vec2 uv = ( uvTransform * vec3( gl_PointCoord.x, 1.0 - gl_PointCoord.y, 1 ) ).xy;
	#endif
#endif
#ifdef USE_MAP
	diffuseColor *= texture2D( map, uv );
#endif
#ifdef USE_ALPHAMAP
	diffuseColor.a *= texture2D( alphaMap, uv ).g;
#endif`,fp=`#if defined( USE_POINTS_UV )
	varying vec2 vUv;
#else
	#if defined( USE_MAP ) || defined( USE_ALPHAMAP )
		uniform mat3 uvTransform;
	#endif
#endif
#ifdef USE_MAP
	uniform sampler2D map;
#endif
#ifdef USE_ALPHAMAP
	uniform sampler2D alphaMap;
#endif`,pp=`float metalnessFactor = metalness;
#ifdef USE_METALNESSMAP
	vec4 texelMetalness = texture2D( metalnessMap, vMetalnessMapUv );
	metalnessFactor *= texelMetalness.b;
#endif`,mp=`#ifdef USE_METALNESSMAP
	uniform sampler2D metalnessMap;
#endif`,gp=`#ifdef USE_INSTANCING_MORPH
	float morphTargetInfluences[ MORPHTARGETS_COUNT ];
	float morphTargetBaseInfluence = texelFetch( morphTexture, ivec2( 0, gl_InstanceID ), 0 ).r;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		morphTargetInfluences[i] =  texelFetch( morphTexture, ivec2( i + 1, gl_InstanceID ), 0 ).r;
	}
#endif`,_p=`#if defined( USE_MORPHCOLORS )
	vColor *= morphTargetBaseInfluence;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		#if defined( USE_COLOR_ALPHA )
			if ( morphTargetInfluences[ i ] != 0.0 ) vColor += getMorph( gl_VertexID, i, 2 ) * morphTargetInfluences[ i ];
		#elif defined( USE_COLOR )
			if ( morphTargetInfluences[ i ] != 0.0 ) vColor += getMorph( gl_VertexID, i, 2 ).rgb * morphTargetInfluences[ i ];
		#endif
	}
#endif`,xp=`#ifdef USE_MORPHNORMALS
	objectNormal *= morphTargetBaseInfluence;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		if ( morphTargetInfluences[ i ] != 0.0 ) objectNormal += getMorph( gl_VertexID, i, 1 ).xyz * morphTargetInfluences[ i ];
	}
#endif`,vp=`#ifdef USE_MORPHTARGETS
	#ifndef USE_INSTANCING_MORPH
		uniform float morphTargetBaseInfluence;
		uniform float morphTargetInfluences[ MORPHTARGETS_COUNT ];
	#endif
	uniform sampler2DArray morphTargetsTexture;
	uniform ivec2 morphTargetsTextureSize;
	vec4 getMorph( const in int vertexIndex, const in int morphTargetIndex, const in int offset ) {
		int texelIndex = vertexIndex * MORPHTARGETS_TEXTURE_STRIDE + offset;
		int y = texelIndex / morphTargetsTextureSize.x;
		int x = texelIndex - y * morphTargetsTextureSize.x;
		ivec3 morphUV = ivec3( x, y, morphTargetIndex );
		return texelFetch( morphTargetsTexture, morphUV, 0 );
	}
#endif`,yp=`#ifdef USE_MORPHTARGETS
	transformed *= morphTargetBaseInfluence;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		if ( morphTargetInfluences[ i ] != 0.0 ) transformed += getMorph( gl_VertexID, i, 0 ).xyz * morphTargetInfluences[ i ];
	}
#endif`,bp=`float faceDirection = gl_FrontFacing ? 1.0 : - 1.0;
#ifdef FLAT_SHADED
	vec3 fdx = dFdx( vViewPosition );
	vec3 fdy = dFdy( vViewPosition );
	vec3 normal = normalize( cross( fdx, fdy ) );
#else
	vec3 normal = normalize( vNormal );
	#ifdef DOUBLE_SIDED
		normal *= faceDirection;
	#endif
#endif
#if defined( USE_NORMALMAP_TANGENTSPACE ) || defined( USE_CLEARCOAT_NORMALMAP ) || defined( USE_ANISOTROPY )
	#ifdef USE_TANGENT
		mat3 tbn = mat3( normalize( vTangent ), normalize( vBitangent ), normal );
	#else
		mat3 tbn = getTangentFrame( - vViewPosition, normal,
		#if defined( USE_NORMALMAP )
			vNormalMapUv
		#elif defined( USE_CLEARCOAT_NORMALMAP )
			vClearcoatNormalMapUv
		#else
			vUv
		#endif
		);
	#endif
	#ifdef DOUBLE_SIDED
		tbn[0] *= faceDirection;
		tbn[1] *= faceDirection;
	#endif
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	#ifdef USE_TANGENT
		mat3 tbn2 = mat3( normalize( vTangent ), normalize( vBitangent ), normal );
	#else
		mat3 tbn2 = getTangentFrame( - vViewPosition, normal, vClearcoatNormalMapUv );
	#endif
	#ifdef DOUBLE_SIDED
		tbn2[0] *= faceDirection;
		tbn2[1] *= faceDirection;
	#endif
#endif
vec3 nonPerturbedNormal = normal;`,Mp=`#ifdef USE_NORMALMAP_OBJECTSPACE
	normal = texture2D( normalMap, vNormalMapUv ).xyz * 2.0 - 1.0;
	#ifdef FLIP_SIDED
		normal = - normal;
	#endif
	#ifdef DOUBLE_SIDED
		normal = normal * faceDirection;
	#endif
	normal = normalize( normalMatrix * normal );
#elif defined( USE_NORMALMAP_TANGENTSPACE )
	vec3 mapN = texture2D( normalMap, vNormalMapUv ).xyz * 2.0 - 1.0;
	#if defined( USE_PACKED_NORMALMAP )
		mapN = vec3( mapN.xy, sqrt( saturate( 1.0 - dot( mapN.xy, mapN.xy ) ) ) );
	#endif
	mapN.xy *= normalScale;
	normal = normalize( tbn * mapN );
#elif defined( USE_BUMPMAP )
	normal = perturbNormalArb( - vViewPosition, normal, dHdxy_fwd(), faceDirection );
#endif`,Sp=`#ifndef FLAT_SHADED
	varying vec3 vNormal;
	#ifdef USE_TANGENT
		varying vec3 vTangent;
		varying vec3 vBitangent;
	#endif
#endif`,Tp=`#ifndef FLAT_SHADED
	varying vec3 vNormal;
	#ifdef USE_TANGENT
		varying vec3 vTangent;
		varying vec3 vBitangent;
	#endif
#endif`,Ep=`#ifndef FLAT_SHADED
	vNormal = normalize( transformedNormal );
	#ifdef USE_TANGENT
		vTangent = normalize( transformedTangent );
		vBitangent = normalize( cross( vNormal, vTangent ) * tangent.w );
		#ifdef FLIP_SIDED
			vBitangent = - vBitangent;
		#endif
	#endif
#endif`,wp=`#ifdef USE_NORMALMAP
	uniform sampler2D normalMap;
	uniform vec2 normalScale;
#endif
#ifdef USE_NORMALMAP_OBJECTSPACE
	uniform mat3 normalMatrix;
#endif
#if ! defined ( USE_TANGENT ) && ( defined ( USE_NORMALMAP_TANGENTSPACE ) || defined ( USE_CLEARCOAT_NORMALMAP ) || defined( USE_ANISOTROPY ) )
	mat3 getTangentFrame( vec3 eye_pos, vec3 surf_norm, vec2 uv ) {
		vec3 q0 = dFdx( eye_pos.xyz );
		vec3 q1 = dFdy( eye_pos.xyz );
		vec2 st0 = dFdx( uv.st );
		vec2 st1 = dFdy( uv.st );
		vec3 N = surf_norm;
		vec3 q1perp = cross( q1, N );
		vec3 q0perp = cross( N, q0 );
		vec3 T = q1perp * st0.x + q0perp * st1.x;
		vec3 B = q1perp * st0.y + q0perp * st1.y;
		float det = max( dot( T, T ), dot( B, B ) );
		float scale = ( det == 0.0 ) ? 0.0 : inversesqrt( det );
		return mat3( T * scale, B * scale, N );
	}
#endif`,Ap=`#ifdef USE_CLEARCOAT
	vec3 clearcoatNormal = nonPerturbedNormal;
#endif`,Cp=`#ifdef USE_CLEARCOAT_NORMALMAP
	vec3 clearcoatMapN = texture2D( clearcoatNormalMap, vClearcoatNormalMapUv ).xyz * 2.0 - 1.0;
	clearcoatMapN.xy *= clearcoatNormalScale;
	clearcoatNormal = normalize( tbn2 * clearcoatMapN );
#endif`,Rp=`#ifdef USE_CLEARCOATMAP
	uniform sampler2D clearcoatMap;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	uniform sampler2D clearcoatNormalMap;
	uniform vec2 clearcoatNormalScale;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	uniform sampler2D clearcoatRoughnessMap;
#endif`,Pp=`#ifdef USE_IRIDESCENCEMAP
	uniform sampler2D iridescenceMap;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	uniform sampler2D iridescenceThicknessMap;
#endif`,Ip=`#ifdef OPAQUE
diffuseColor.a = 1.0;
#endif
#ifdef USE_TRANSMISSION
diffuseColor.a *= material.transmissionAlpha;
#endif
gl_FragColor = vec4( outgoingLight, diffuseColor.a );`,Lp=`vec3 packNormalToRGB( const in vec3 normal ) {
	return normalize( normal ) * 0.5 + 0.5;
}
vec3 unpackRGBToNormal( const in vec3 rgb ) {
	return 2.0 * rgb.xyz - 1.0;
}
const float PackUpscale = 256. / 255.;const float UnpackDownscale = 255. / 256.;const float ShiftRight8 = 1. / 256.;
const float Inv255 = 1. / 255.;
const vec4 PackFactors = vec4( 1.0, 256.0, 256.0 * 256.0, 256.0 * 256.0 * 256.0 );
const vec2 UnpackFactors2 = vec2( UnpackDownscale, 1.0 / PackFactors.g );
const vec3 UnpackFactors3 = vec3( UnpackDownscale / PackFactors.rg, 1.0 / PackFactors.b );
const vec4 UnpackFactors4 = vec4( UnpackDownscale / PackFactors.rgb, 1.0 / PackFactors.a );
vec4 packDepthToRGBA( const in float v ) {
	if( v <= 0.0 )
		return vec4( 0., 0., 0., 0. );
	if( v >= 1.0 )
		return vec4( 1., 1., 1., 1. );
	float vuf;
	float af = modf( v * PackFactors.a, vuf );
	float bf = modf( vuf * ShiftRight8, vuf );
	float gf = modf( vuf * ShiftRight8, vuf );
	return vec4( vuf * Inv255, gf * PackUpscale, bf * PackUpscale, af );
}
vec3 packDepthToRGB( const in float v ) {
	if( v <= 0.0 )
		return vec3( 0., 0., 0. );
	if( v >= 1.0 )
		return vec3( 1., 1., 1. );
	float vuf;
	float bf = modf( v * PackFactors.b, vuf );
	float gf = modf( vuf * ShiftRight8, vuf );
	return vec3( vuf * Inv255, gf * PackUpscale, bf );
}
vec2 packDepthToRG( const in float v ) {
	if( v <= 0.0 )
		return vec2( 0., 0. );
	if( v >= 1.0 )
		return vec2( 1., 1. );
	float vuf;
	float gf = modf( v * 256., vuf );
	return vec2( vuf * Inv255, gf );
}
float unpackRGBAToDepth( const in vec4 v ) {
	return dot( v, UnpackFactors4 );
}
float unpackRGBToDepth( const in vec3 v ) {
	return dot( v, UnpackFactors3 );
}
float unpackRGToDepth( const in vec2 v ) {
	return v.r * UnpackFactors2.r + v.g * UnpackFactors2.g;
}
vec4 pack2HalfToRGBA( const in vec2 v ) {
	vec4 r = vec4( v.x, fract( v.x * 255.0 ), v.y, fract( v.y * 255.0 ) );
	return vec4( r.x - r.y / 255.0, r.y, r.z - r.w / 255.0, r.w );
}
vec2 unpackRGBATo2Half( const in vec4 v ) {
	return vec2( v.x + ( v.y / 255.0 ), v.z + ( v.w / 255.0 ) );
}
float viewZToOrthographicDepth( const in float viewZ, const in float near, const in float far ) {
	return ( viewZ + near ) / ( near - far );
}
float orthographicDepthToViewZ( const in float depth, const in float near, const in float far ) {
	#ifdef USE_REVERSED_DEPTH_BUFFER

		return depth * ( far - near ) - far;
	#else
		return depth * ( near - far ) - near;
	#endif
}
float viewZToPerspectiveDepth( const in float viewZ, const in float near, const in float far ) {
	return ( ( near + viewZ ) * far ) / ( ( far - near ) * viewZ );
}
float perspectiveDepthToViewZ( const in float depth, const in float near, const in float far ) {

	#ifdef USE_REVERSED_DEPTH_BUFFER
		return ( near * far ) / ( ( near - far ) * depth - near );
	#else
		return ( near * far ) / ( ( far - near ) * depth - far );
	#endif
}`,Np=`#ifdef PREMULTIPLIED_ALPHA
	gl_FragColor.rgb *= gl_FragColor.a;
#endif`,Dp=`vec4 mvPosition = vec4( transformed, 1.0 );
#ifdef USE_BATCHING
	mvPosition = batchingMatrix * mvPosition;
#endif
#ifdef USE_INSTANCING
	mvPosition = instanceMatrix * mvPosition;
#endif
mvPosition = modelViewMatrix * mvPosition;
gl_Position = projectionMatrix * mvPosition;`,Up=`#ifdef DITHERING
	gl_FragColor.rgb = dithering( gl_FragColor.rgb );
#endif`,Fp=`#ifdef DITHERING
	vec3 dithering( vec3 color ) {
		float grid_position = rand( gl_FragCoord.xy );
		vec3 dither_shift_RGB = vec3( 0.25 / 255.0, -0.25 / 255.0, 0.25 / 255.0 );
		dither_shift_RGB = mix( 2.0 * dither_shift_RGB, -2.0 * dither_shift_RGB, grid_position );
		return color + dither_shift_RGB;
	}
#endif`,kp=`float roughnessFactor = roughness;
#ifdef USE_ROUGHNESSMAP
	vec4 texelRoughness = texture2D( roughnessMap, vRoughnessMapUv );
	roughnessFactor *= texelRoughness.g;
#endif`,Op=`#ifdef USE_ROUGHNESSMAP
	uniform sampler2D roughnessMap;
#endif`,Bp=`#if NUM_SPOT_LIGHT_COORDS > 0
	varying vec4 vSpotLightCoord[ NUM_SPOT_LIGHT_COORDS ];
#endif
#if NUM_SPOT_LIGHT_MAPS > 0
	uniform sampler2D spotLightMap[ NUM_SPOT_LIGHT_MAPS ];
#endif
#ifdef USE_SHADOWMAP
	#if NUM_SUN_LIGHT_SHADOWS > 0
		#define SUN_LIGHT_CASCADES 2
		#if defined( SHADOWMAP_TYPE_PCF )
			uniform sampler2DShadow sunShadowMap[ NUM_SUN_LIGHT_SHADOWS ];
		#else
			uniform sampler2D sunShadowMap[ NUM_SUN_LIGHT_SHADOWS ];
		#endif
		uniform mat4 sunShadowMatrix[ NUM_SUN_LIGHT_SHADOWS * SUN_LIGHT_CASCADES ];
		uniform vec4 sunShadowCascade[ NUM_SUN_LIGHT_SHADOWS * SUN_LIGHT_CASCADES ];
		varying vec4 vSunShadowWorldPosition;
		varying vec3 vSunShadowWorldNormal;
		struct SunLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform SunLightShadow sunLightShadows[ NUM_SUN_LIGHT_SHADOWS ];
	#endif
	#if NUM_DIR_LIGHT_SHADOWS > 0
		#if defined( SHADOWMAP_TYPE_PCF )
			uniform sampler2DShadow directionalShadowMap[ NUM_DIR_LIGHT_SHADOWS ];
		#else
			uniform sampler2D directionalShadowMap[ NUM_DIR_LIGHT_SHADOWS ];
		#endif
		varying vec4 vDirectionalShadowCoord[ NUM_DIR_LIGHT_SHADOWS ];
		struct DirectionalLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform DirectionalLightShadow directionalLightShadows[ NUM_DIR_LIGHT_SHADOWS ];
	#endif
	#if NUM_SPOT_LIGHT_SHADOWS > 0
		#if defined( SHADOWMAP_TYPE_PCF )
			uniform sampler2DShadow spotShadowMap[ NUM_SPOT_LIGHT_SHADOWS ];
		#else
			uniform sampler2D spotShadowMap[ NUM_SPOT_LIGHT_SHADOWS ];
		#endif
		struct SpotLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform SpotLightShadow spotLightShadows[ NUM_SPOT_LIGHT_SHADOWS ];
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0
		#if defined( SHADOWMAP_TYPE_PCF )
			uniform samplerCubeShadow pointShadowMap[ NUM_POINT_LIGHT_SHADOWS ];
		#elif defined( SHADOWMAP_TYPE_BASIC )
			uniform samplerCube pointShadowMap[ NUM_POINT_LIGHT_SHADOWS ];
		#endif
		varying vec4 vPointShadowCoord[ NUM_POINT_LIGHT_SHADOWS ];
		struct PointLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
			float shadowCameraNear;
			float shadowCameraFar;
		};
		uniform PointLightShadow pointLightShadows[ NUM_POINT_LIGHT_SHADOWS ];
	#endif
	#if defined( SHADOWMAP_TYPE_PCF )
		float interleavedGradientNoise( vec2 position ) {
			return fract( 52.9829189 * fract( dot( position, vec2( 0.06711056, 0.00583715 ) ) ) );
		}
		vec2 vogelDiskSample( int sampleIndex, int samplesCount, float phi ) {
			const float goldenAngle = 2.399963229728653;
			float r = sqrt( ( float( sampleIndex ) + 0.5 ) / float( samplesCount ) );
			float theta = float( sampleIndex ) * goldenAngle + phi;
			return vec2( cos( theta ), sin( theta ) ) * r;
		}
	#endif
	#if defined( SHADOWMAP_TYPE_PCF )
		float getShadow( sampler2DShadow shadowMap, vec2 shadowMapSize, float shadowIntensity, float shadowBias, float shadowRadius, vec4 shadowCoord ) {
			float shadow = 1.0;
			shadowCoord.xyz /= shadowCoord.w;
			shadowCoord.z += shadowBias;
			bool inFrustum = shadowCoord.x >= 0.0 && shadowCoord.x <= 1.0 && shadowCoord.y >= 0.0 && shadowCoord.y <= 1.0;
			bool frustumTest = inFrustum && shadowCoord.z <= 1.0;
			if ( frustumTest ) {
				vec2 texelSize = vec2( 1.0 ) / shadowMapSize;
				float radius = shadowRadius * texelSize.x;
				float phi = interleavedGradientNoise( gl_FragCoord.xy ) * PI2;
				shadow = (
					texture( shadowMap, vec3( shadowCoord.xy + vogelDiskSample( 0, 5, phi ) * radius, shadowCoord.z ) ) +
					texture( shadowMap, vec3( shadowCoord.xy + vogelDiskSample( 1, 5, phi ) * radius, shadowCoord.z ) ) +
					texture( shadowMap, vec3( shadowCoord.xy + vogelDiskSample( 2, 5, phi ) * radius, shadowCoord.z ) ) +
					texture( shadowMap, vec3( shadowCoord.xy + vogelDiskSample( 3, 5, phi ) * radius, shadowCoord.z ) ) +
					texture( shadowMap, vec3( shadowCoord.xy + vogelDiskSample( 4, 5, phi ) * radius, shadowCoord.z ) )
				) * 0.2;
			}
			return mix( 1.0, shadow, shadowIntensity );
		}
	#elif defined( SHADOWMAP_TYPE_VSM )
		float getShadow( sampler2D shadowMap, vec2 shadowMapSize, float shadowIntensity, float shadowBias, float shadowRadius, vec4 shadowCoord ) {
			float shadow = 1.0;
			shadowCoord.xyz /= shadowCoord.w;
			#ifdef USE_REVERSED_DEPTH_BUFFER
				shadowCoord.z -= shadowBias;
			#else
				shadowCoord.z += shadowBias;
			#endif
			bool inFrustum = shadowCoord.x >= 0.0 && shadowCoord.x <= 1.0 && shadowCoord.y >= 0.0 && shadowCoord.y <= 1.0;
			bool frustumTest = inFrustum && shadowCoord.z <= 1.0;
			if ( frustumTest ) {
				vec2 distribution = texture2D( shadowMap, shadowCoord.xy ).rg;
				float mean = distribution.x;
				float variance = distribution.y * distribution.y;
				#ifdef USE_REVERSED_DEPTH_BUFFER
					float hard_shadow = step( mean, shadowCoord.z );
				#else
					float hard_shadow = step( shadowCoord.z, mean );
				#endif

				if ( hard_shadow == 1.0 ) {
					shadow = 1.0;
				} else {
					variance = max( variance, 0.0000001 );
					float d = shadowCoord.z - mean;
					float p_max = variance / ( variance + d * d );
					p_max = clamp( ( p_max - 0.3 ) / 0.65, 0.0, 1.0 );
					shadow = max( hard_shadow, p_max );
				}
			}
			return mix( 1.0, shadow, shadowIntensity );
		}
	#else
		float getShadow( sampler2D shadowMap, vec2 shadowMapSize, float shadowIntensity, float shadowBias, float shadowRadius, vec4 shadowCoord ) {
			float shadow = 1.0;
			shadowCoord.xyz /= shadowCoord.w;
			#ifdef USE_REVERSED_DEPTH_BUFFER
				shadowCoord.z -= shadowBias;
			#else
				shadowCoord.z += shadowBias;
			#endif
			bool inFrustum = shadowCoord.x >= 0.0 && shadowCoord.x <= 1.0 && shadowCoord.y >= 0.0 && shadowCoord.y <= 1.0;
			bool frustumTest = inFrustum && shadowCoord.z <= 1.0;
			if ( frustumTest ) {
				float depth = texture2D( shadowMap, shadowCoord.xy ).r;
				#ifdef USE_REVERSED_DEPTH_BUFFER
					shadow = step( depth, shadowCoord.z );
				#else
					shadow = step( shadowCoord.z, depth );
				#endif
			}
			return mix( 1.0, shadow, shadowIntensity );
		}
	#endif
	#if NUM_SUN_LIGHT_SHADOWS > 0
		float getSunShadow(
			#if defined( SHADOWMAP_TYPE_PCF )
				sampler2DShadow shadowMap,
			#else
				sampler2D shadowMap,
			#endif
			SunLightShadow sunLightShadow,
			int shadowIndex
		) {
			vec4 shadowWorldPosition = vec4( vSunShadowWorldPosition.xyz + vSunShadowWorldNormal * sunLightShadow.shadowNormalBias, 1.0 );
			float viewDepth = vSunShadowWorldPosition.w;
			int cascadeOffset = shadowIndex * SUN_LIGHT_CASCADES;
			float shadow = 1.0;
			for ( int i = SUN_LIGHT_CASCADES - 1; i >= 0; i -- ) {
				vec4 cascade = sunShadowCascade[ cascadeOffset + i ];
				if ( viewDepth >= cascade.x && viewDepth < cascade.y ) {
					float cascadeShadow = getShadow(
						shadowMap,
						sunLightShadow.shadowMapSize,
						sunLightShadow.shadowIntensity,
						sunLightShadow.shadowBias,
						sunLightShadow.shadowRadius,
						sunShadowMatrix[ cascadeOffset + i ] * shadowWorldPosition
					);
					shadow = mix( cascadeShadow, shadow, smoothstep( cascade.z, cascade.y, viewDepth ) );
				}
			}
			return shadow;
		}
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0
	#if defined( SHADOWMAP_TYPE_PCF )
	float getPointShadow( samplerCubeShadow shadowMap, vec2 shadowMapSize, float shadowIntensity, float shadowBias, float shadowRadius, vec4 shadowCoord, float shadowCameraNear, float shadowCameraFar ) {
		float shadow = 1.0;
		vec3 lightToPosition = shadowCoord.xyz;
		vec3 bd3D = normalize( lightToPosition );
		vec3 absVec = abs( lightToPosition );
		float viewSpaceZ = max( max( absVec.x, absVec.y ), absVec.z );
		if ( viewSpaceZ - shadowCameraFar <= 0.0 && viewSpaceZ - shadowCameraNear >= 0.0 ) {
			#ifdef USE_REVERSED_DEPTH_BUFFER
				float dp = ( shadowCameraNear * ( shadowCameraFar - viewSpaceZ ) ) / ( viewSpaceZ * ( shadowCameraFar - shadowCameraNear ) );
				dp -= shadowBias;
			#else
				float dp = ( shadowCameraFar * ( viewSpaceZ - shadowCameraNear ) ) / ( viewSpaceZ * ( shadowCameraFar - shadowCameraNear ) );
				dp += shadowBias;
			#endif
			float texelSize = shadowRadius / shadowMapSize.x;
			vec3 absDir = abs( bd3D );
			vec3 tangent = absDir.x > absDir.z ? vec3( 0.0, 1.0, 0.0 ) : vec3( 1.0, 0.0, 0.0 );
			tangent = normalize( cross( bd3D, tangent ) );
			vec3 bitangent = cross( bd3D, tangent );
			float phi = interleavedGradientNoise( gl_FragCoord.xy ) * PI2;
			vec2 sample0 = vogelDiskSample( 0, 5, phi );
			vec2 sample1 = vogelDiskSample( 1, 5, phi );
			vec2 sample2 = vogelDiskSample( 2, 5, phi );
			vec2 sample3 = vogelDiskSample( 3, 5, phi );
			vec2 sample4 = vogelDiskSample( 4, 5, phi );
			shadow = (
				texture( shadowMap, vec4( bd3D + ( tangent * sample0.x + bitangent * sample0.y ) * texelSize, dp ) ) +
				texture( shadowMap, vec4( bd3D + ( tangent * sample1.x + bitangent * sample1.y ) * texelSize, dp ) ) +
				texture( shadowMap, vec4( bd3D + ( tangent * sample2.x + bitangent * sample2.y ) * texelSize, dp ) ) +
				texture( shadowMap, vec4( bd3D + ( tangent * sample3.x + bitangent * sample3.y ) * texelSize, dp ) ) +
				texture( shadowMap, vec4( bd3D + ( tangent * sample4.x + bitangent * sample4.y ) * texelSize, dp ) )
			) * 0.2;
		}
		return mix( 1.0, shadow, shadowIntensity );
	}
	#elif defined( SHADOWMAP_TYPE_BASIC )
	float getPointShadow( samplerCube shadowMap, vec2 shadowMapSize, float shadowIntensity, float shadowBias, float shadowRadius, vec4 shadowCoord, float shadowCameraNear, float shadowCameraFar ) {
		float shadow = 1.0;
		vec3 lightToPosition = shadowCoord.xyz;
		vec3 absVec = abs( lightToPosition );
		float viewSpaceZ = max( max( absVec.x, absVec.y ), absVec.z );
		if ( viewSpaceZ - shadowCameraFar <= 0.0 && viewSpaceZ - shadowCameraNear >= 0.0 ) {
			float dp = ( shadowCameraFar * ( viewSpaceZ - shadowCameraNear ) ) / ( viewSpaceZ * ( shadowCameraFar - shadowCameraNear ) );
			dp += shadowBias;
			vec3 bd3D = normalize( lightToPosition );
			float depth = textureCube( shadowMap, bd3D ).r;
			#ifdef USE_REVERSED_DEPTH_BUFFER
				depth = 1.0 - depth;
			#endif
			shadow = step( dp, depth );
		}
		return mix( 1.0, shadow, shadowIntensity );
	}
	#endif
	#endif
#endif`,zp=`#if NUM_SPOT_LIGHT_COORDS > 0
	uniform mat4 spotLightMatrix[ NUM_SPOT_LIGHT_COORDS ];
	varying vec4 vSpotLightCoord[ NUM_SPOT_LIGHT_COORDS ];
#endif
#ifdef USE_SHADOWMAP
	#if NUM_SUN_LIGHT_SHADOWS > 0
		varying vec4 vSunShadowWorldPosition;
		varying vec3 vSunShadowWorldNormal;
	#endif
	#if NUM_DIR_LIGHT_SHADOWS > 0
		uniform mat4 directionalShadowMatrix[ NUM_DIR_LIGHT_SHADOWS ];
		varying vec4 vDirectionalShadowCoord[ NUM_DIR_LIGHT_SHADOWS ];
		struct DirectionalLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform DirectionalLightShadow directionalLightShadows[ NUM_DIR_LIGHT_SHADOWS ];
	#endif
	#if NUM_SPOT_LIGHT_SHADOWS > 0
		struct SpotLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform SpotLightShadow spotLightShadows[ NUM_SPOT_LIGHT_SHADOWS ];
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0
		uniform mat4 pointShadowMatrix[ NUM_POINT_LIGHT_SHADOWS ];
		varying vec4 vPointShadowCoord[ NUM_POINT_LIGHT_SHADOWS ];
		struct PointLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
			float shadowCameraNear;
			float shadowCameraFar;
		};
		uniform PointLightShadow pointLightShadows[ NUM_POINT_LIGHT_SHADOWS ];
	#endif
#endif`,Vp=`#if ( defined( USE_SHADOWMAP ) && ( NUM_DIR_LIGHT_SHADOWS > 0 || NUM_SUN_LIGHT_SHADOWS > 0 || NUM_POINT_LIGHT_SHADOWS > 0 ) ) || ( NUM_SPOT_LIGHT_COORDS > 0 )
	#ifdef HAS_NORMAL
		vec3 shadowWorldNormal = transformNormalByInverseViewMatrix( transformedNormal, viewMatrix );
	#else
		vec3 shadowWorldNormal = vec3( 0.0 );
	#endif
	vec4 shadowWorldPosition;
#endif
#if defined( USE_SHADOWMAP )
	#if NUM_SUN_LIGHT_SHADOWS > 0
		vSunShadowWorldPosition = vec4( worldPosition.xyz, - mvPosition.z );
		vSunShadowWorldNormal = shadowWorldNormal;
	#endif
	#if NUM_DIR_LIGHT_SHADOWS > 0
		#pragma unroll_loop_start
		for ( int i = 0; i < NUM_DIR_LIGHT_SHADOWS; i ++ ) {
			shadowWorldPosition = worldPosition + vec4( shadowWorldNormal * directionalLightShadows[ i ].shadowNormalBias, 0 );
			vDirectionalShadowCoord[ i ] = directionalShadowMatrix[ i ] * shadowWorldPosition;
		}
		#pragma unroll_loop_end
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0
		#pragma unroll_loop_start
		for ( int i = 0; i < NUM_POINT_LIGHT_SHADOWS; i ++ ) {
			shadowWorldPosition = worldPosition + vec4( shadowWorldNormal * pointLightShadows[ i ].shadowNormalBias, 0 );
			vPointShadowCoord[ i ] = pointShadowMatrix[ i ] * shadowWorldPosition;
		}
		#pragma unroll_loop_end
	#endif
#endif
#if NUM_SPOT_LIGHT_COORDS > 0
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_SPOT_LIGHT_COORDS; i ++ ) {
		shadowWorldPosition = worldPosition;
		#if ( defined( USE_SHADOWMAP ) && UNROLLED_LOOP_INDEX < NUM_SPOT_LIGHT_SHADOWS )
			shadowWorldPosition.xyz += shadowWorldNormal * spotLightShadows[ i ].shadowNormalBias;
		#endif
		vSpotLightCoord[ i ] = spotLightMatrix[ i ] * shadowWorldPosition;
	}
	#pragma unroll_loop_end
#endif`,Hp=`float getShadowMask() {
	float shadow = 1.0;
	#ifdef USE_SHADOWMAP
	#if NUM_SUN_LIGHT_SHADOWS > 0
	SunLightShadow sunLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_SUN_LIGHT_SHADOWS; i ++ ) {
		sunLight = sunLightShadows[ i ];
		shadow *= receiveShadow ? getSunShadow( sunShadowMap[ i ], sunLight, UNROLLED_LOOP_INDEX ) : 1.0;
	}
	#pragma unroll_loop_end
	#endif
	#if NUM_DIR_LIGHT_SHADOWS > 0
	DirectionalLightShadow directionalLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_DIR_LIGHT_SHADOWS; i ++ ) {
		directionalLight = directionalLightShadows[ i ];
		shadow *= receiveShadow ? getShadow( directionalShadowMap[ i ], directionalLight.shadowMapSize, directionalLight.shadowIntensity, directionalLight.shadowBias, directionalLight.shadowRadius, vDirectionalShadowCoord[ i ] ) : 1.0;
	}
	#pragma unroll_loop_end
	#endif
	#if NUM_SPOT_LIGHT_SHADOWS > 0
	SpotLightShadow spotLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_SPOT_LIGHT_SHADOWS; i ++ ) {
		spotLight = spotLightShadows[ i ];
		shadow *= receiveShadow ? getShadow( spotShadowMap[ i ], spotLight.shadowMapSize, spotLight.shadowIntensity, spotLight.shadowBias, spotLight.shadowRadius, vSpotLightCoord[ i ] ) : 1.0;
	}
	#pragma unroll_loop_end
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0 && ( defined( SHADOWMAP_TYPE_PCF ) || defined( SHADOWMAP_TYPE_BASIC ) )
	PointLightShadow pointLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_POINT_LIGHT_SHADOWS; i ++ ) {
		pointLight = pointLightShadows[ i ];
		shadow *= receiveShadow ? getPointShadow( pointShadowMap[ i ], pointLight.shadowMapSize, pointLight.shadowIntensity, pointLight.shadowBias, pointLight.shadowRadius, vPointShadowCoord[ i ], pointLight.shadowCameraNear, pointLight.shadowCameraFar ) : 1.0;
	}
	#pragma unroll_loop_end
	#endif
	#endif
	return shadow;
}`,Gp=`#ifdef USE_SKINNING
	mat4 boneMatX = getBoneMatrix( skinIndex.x );
	mat4 boneMatY = getBoneMatrix( skinIndex.y );
	mat4 boneMatZ = getBoneMatrix( skinIndex.z );
	mat4 boneMatW = getBoneMatrix( skinIndex.w );
#endif`,Wp=`#ifdef USE_SKINNING
	uniform mat4 bindMatrix;
	uniform mat4 bindMatrixInverse;
	uniform highp sampler2D boneTexture;
	mat4 getBoneMatrix( const in float i ) {
		int size = textureSize( boneTexture, 0 ).x;
		int j = int( i ) * 4;
		int x = j % size;
		int y = j / size;
		vec4 v1 = texelFetch( boneTexture, ivec2( x, y ), 0 );
		vec4 v2 = texelFetch( boneTexture, ivec2( x + 1, y ), 0 );
		vec4 v3 = texelFetch( boneTexture, ivec2( x + 2, y ), 0 );
		vec4 v4 = texelFetch( boneTexture, ivec2( x + 3, y ), 0 );
		return mat4( v1, v2, v3, v4 );
	}
#endif`,qp=`#ifdef USE_SKINNING
	vec4 skinVertex = bindMatrix * vec4( transformed, 1.0 );
	vec4 skinned = vec4( 0.0 );
	skinned += boneMatX * skinVertex * skinWeight.x;
	skinned += boneMatY * skinVertex * skinWeight.y;
	skinned += boneMatZ * skinVertex * skinWeight.z;
	skinned += boneMatW * skinVertex * skinWeight.w;
	transformed = ( bindMatrixInverse * skinned ).xyz;
#endif`,Xp=`#ifdef USE_SKINNING
	mat4 skinMatrix = mat4( 0.0 );
	skinMatrix += skinWeight.x * boneMatX;
	skinMatrix += skinWeight.y * boneMatY;
	skinMatrix += skinWeight.z * boneMatZ;
	skinMatrix += skinWeight.w * boneMatW;
	skinMatrix = bindMatrixInverse * skinMatrix * bindMatrix;
	objectNormal = vec4( skinMatrix * vec4( objectNormal, 0.0 ) ).xyz;
	#ifdef USE_TANGENT
		objectTangent = vec4( skinMatrix * vec4( objectTangent, 0.0 ) ).xyz;
	#endif
#endif`,$p=`float specularStrength;
#ifdef USE_SPECULARMAP
	vec4 texelSpecular = texture2D( specularMap, vSpecularMapUv );
	specularStrength = texelSpecular.r;
#else
	specularStrength = 1.0;
#endif`,Yp=`#ifdef USE_SPECULARMAP
	uniform sampler2D specularMap;
#endif`,Zp=`#if defined( TONE_MAPPING )
	gl_FragColor.rgb = toneMapping( gl_FragColor.rgb );
#endif`,jp=`#ifndef saturate
#define saturate( a ) clamp( a, 0.0, 1.0 )
#endif
uniform float toneMappingExposure;
vec3 LinearToneMapping( vec3 color ) {
	return saturate( toneMappingExposure * color );
}
vec3 ReinhardToneMapping( vec3 color ) {
	color *= toneMappingExposure;
	return saturate( color / ( vec3( 1.0 ) + color ) );
}
vec3 CineonToneMapping( vec3 color ) {
	color *= toneMappingExposure;
	color = max( vec3( 0.0 ), color - 0.004 );
	return pow( ( color * ( 6.2 * color + 0.5 ) ) / ( color * ( 6.2 * color + 1.7 ) + 0.06 ), vec3( 2.2 ) );
}
vec3 RRTAndODTFit( vec3 v ) {
	vec3 a = v * ( v + 0.0245786 ) - 0.000090537;
	vec3 b = v * ( 0.983729 * v + 0.4329510 ) + 0.238081;
	return a / b;
}
vec3 ACESFilmicToneMapping( vec3 color ) {
	const mat3 ACESInputMat = mat3(
		vec3( 0.59719, 0.07600, 0.02840 ),		vec3( 0.35458, 0.90834, 0.13383 ),
		vec3( 0.04823, 0.01566, 0.83777 )
	);
	const mat3 ACESOutputMat = mat3(
		vec3(  1.60475, -0.10208, -0.00327 ),		vec3( -0.53108,  1.10813, -0.07276 ),
		vec3( -0.07367, -0.00605,  1.07602 )
	);
	color *= toneMappingExposure / 0.6;
	color = ACESInputMat * color;
	color = RRTAndODTFit( color );
	color = ACESOutputMat * color;
	return saturate( color );
}
const mat3 LINEAR_REC2020_TO_LINEAR_SRGB = mat3(
	vec3( 1.6605, - 0.1246, - 0.0182 ),
	vec3( - 0.5876, 1.1329, - 0.1006 ),
	vec3( - 0.0728, - 0.0083, 1.1187 )
);
const mat3 LINEAR_SRGB_TO_LINEAR_REC2020 = mat3(
	vec3( 0.6274, 0.0691, 0.0164 ),
	vec3( 0.3293, 0.9195, 0.0880 ),
	vec3( 0.0433, 0.0113, 0.8956 )
);
vec3 agxDefaultContrastApprox( vec3 x ) {
	vec3 x2 = x * x;
	vec3 x4 = x2 * x2;
	return + 15.5 * x4 * x2
		- 40.14 * x4 * x
		+ 31.96 * x4
		- 6.868 * x2 * x
		+ 0.4298 * x2
		+ 0.1191 * x
		- 0.00232;
}
vec3 AgXToneMapping( vec3 color ) {
	const mat3 AgXInsetMatrix = mat3(
		vec3( 0.856627153315983, 0.137318972929847, 0.11189821299995 ),
		vec3( 0.0951212405381588, 0.761241990602591, 0.0767994186031903 ),
		vec3( 0.0482516061458583, 0.101439036467562, 0.811302368396859 )
	);
	const mat3 AgXOutsetMatrix = mat3(
		vec3( 1.1271005818144368, - 0.1413297634984383, - 0.14132976349843826 ),
		vec3( - 0.11060664309660323, 1.157823702216272, - 0.11060664309660294 ),
		vec3( - 0.016493938717834573, - 0.016493938717834257, 1.2519364065950405 )
	);
	const float AgxMinEv = - 12.47393;	const float AgxMaxEv = 4.026069;
	color *= toneMappingExposure;
	color = LINEAR_SRGB_TO_LINEAR_REC2020 * color;
	color = AgXInsetMatrix * color;
	color = max( color, 1e-10 );	color = log2( color );
	color = ( color - AgxMinEv ) / ( AgxMaxEv - AgxMinEv );
	color = clamp( color, 0.0, 1.0 );
	color = agxDefaultContrastApprox( color );
	color = AgXOutsetMatrix * color;
	color = pow( max( vec3( 0.0 ), color ), vec3( 2.2 ) );
	color = LINEAR_REC2020_TO_LINEAR_SRGB * color;
	color = clamp( color, 0.0, 1.0 );
	return color;
}
vec3 NeutralToneMapping( vec3 color ) {
	const float StartCompression = 0.8 - 0.04;
	const float Desaturation = 0.15;
	color *= toneMappingExposure;
	float x = min( color.r, min( color.g, color.b ) );
	float offset = x < 0.08 ? x - 6.25 * x * x : 0.04;
	color -= offset;
	float peak = max( color.r, max( color.g, color.b ) );
	if ( peak < StartCompression ) return color;
	float d = 1. - StartCompression;
	float newPeak = 1. - d * d / ( peak + d - StartCompression );
	color *= newPeak / peak;
	float g = 1. - 1. / ( Desaturation * ( peak - newPeak ) + 1. );
	return mix( color, vec3( newPeak ), g );
}
vec3 CustomToneMapping( vec3 color ) { return color; }`,Jp=`#ifdef USE_TRANSMISSION
	material.transmission = transmission;
	material.transmissionAlpha = 1.0;
	material.thickness = thickness;
	material.attenuationDistance = attenuationDistance;
	material.attenuationColor = attenuationColor;
	#ifdef USE_TRANSMISSIONMAP
		material.transmission *= texture2D( transmissionMap, vTransmissionMapUv ).r;
	#endif
	#ifdef USE_THICKNESSMAP
		material.thickness *= texture2D( thicknessMap, vThicknessMapUv ).g;
	#endif
	vec3 pos = vWorldPosition;
	vec3 v = normalize( cameraPosition - pos );
	vec3 n = transformNormalByInverseViewMatrix( normal, viewMatrix );
	vec4 transmitted = getIBLVolumeRefraction(
		n, v, material.roughness, material.diffuseContribution, material.specularColorBlended, material.specularF90,
		pos, modelMatrix, viewMatrix, projectionMatrix, material.dispersion, material.ior, material.thickness,
		material.attenuationColor, material.attenuationDistance );
	material.transmissionAlpha = mix( material.transmissionAlpha, transmitted.a, material.transmission );
	totalDiffuse = mix( totalDiffuse, transmitted.rgb, material.transmission );
#endif`,Kp=`#ifdef USE_TRANSMISSION
	uniform float transmission;
	uniform float thickness;
	uniform float attenuationDistance;
	uniform vec3 attenuationColor;
	#ifdef USE_TRANSMISSIONMAP
		uniform sampler2D transmissionMap;
	#endif
	#ifdef USE_THICKNESSMAP
		uniform sampler2D thicknessMap;
	#endif
	uniform vec2 transmissionSamplerSize;
	uniform sampler2D transmissionSamplerMap;
	uniform mat4 modelMatrix;
	uniform mat4 projectionMatrix;
	varying vec3 vWorldPosition;
	float w0( float a ) {
		return ( 1.0 / 6.0 ) * ( a * ( a * ( - a + 3.0 ) - 3.0 ) + 1.0 );
	}
	float w1( float a ) {
		return ( 1.0 / 6.0 ) * ( a *  a * ( 3.0 * a - 6.0 ) + 4.0 );
	}
	float w2( float a ){
		return ( 1.0 / 6.0 ) * ( a * ( a * ( - 3.0 * a + 3.0 ) + 3.0 ) + 1.0 );
	}
	float w3( float a ) {
		return ( 1.0 / 6.0 ) * ( a * a * a );
	}
	float g0( float a ) {
		return w0( a ) + w1( a );
	}
	float g1( float a ) {
		return w2( a ) + w3( a );
	}
	float h0( float a ) {
		return - 1.0 + w1( a ) / ( w0( a ) + w1( a ) );
	}
	float h1( float a ) {
		return 1.0 + w3( a ) / ( w2( a ) + w3( a ) );
	}
	vec4 bicubic( sampler2D tex, vec2 uv, vec4 texelSize, float lod ) {
		uv = uv * texelSize.zw + 0.5;
		vec2 iuv = floor( uv );
		vec2 fuv = fract( uv );
		float g0x = g0( fuv.x );
		float g1x = g1( fuv.x );
		float h0x = h0( fuv.x );
		float h1x = h1( fuv.x );
		float h0y = h0( fuv.y );
		float h1y = h1( fuv.y );
		vec2 p0 = ( vec2( iuv.x + h0x, iuv.y + h0y ) - 0.5 ) * texelSize.xy;
		vec2 p1 = ( vec2( iuv.x + h1x, iuv.y + h0y ) - 0.5 ) * texelSize.xy;
		vec2 p2 = ( vec2( iuv.x + h0x, iuv.y + h1y ) - 0.5 ) * texelSize.xy;
		vec2 p3 = ( vec2( iuv.x + h1x, iuv.y + h1y ) - 0.5 ) * texelSize.xy;
		return g0( fuv.y ) * ( g0x * textureLod( tex, p0, lod ) + g1x * textureLod( tex, p1, lod ) ) +
			g1( fuv.y ) * ( g0x * textureLod( tex, p2, lod ) + g1x * textureLod( tex, p3, lod ) );
	}
	vec4 textureBicubic( sampler2D sampler, vec2 uv, float lod ) {
		vec2 fLodSize = vec2( textureSize( sampler, int( lod ) ) );
		vec2 cLodSize = vec2( textureSize( sampler, int( lod + 1.0 ) ) );
		vec2 fLodSizeInv = 1.0 / fLodSize;
		vec2 cLodSizeInv = 1.0 / cLodSize;
		vec4 fSample = bicubic( sampler, uv, vec4( fLodSizeInv, fLodSize ), floor( lod ) );
		vec4 cSample = bicubic( sampler, uv, vec4( cLodSizeInv, cLodSize ), ceil( lod ) );
		return mix( fSample, cSample, fract( lod ) );
	}
	vec3 getVolumeTransmissionRay( const in vec3 n, const in vec3 v, const in float thickness, const in float ior, const in mat4 modelMatrix ) {
		vec3 refractionVector = refract( - v, normalize( n ), 1.0 / ior );
		vec3 modelScale;
		modelScale.x = length( vec3( modelMatrix[ 0 ].xyz ) );
		modelScale.y = length( vec3( modelMatrix[ 1 ].xyz ) );
		modelScale.z = length( vec3( modelMatrix[ 2 ].xyz ) );
		return normalize( refractionVector ) * thickness * modelScale;
	}
	float applyIorToRoughness( const in float roughness, const in float ior ) {
		return roughness * clamp( ior * 2.0 - 2.0, 0.0, 1.0 );
	}
	vec4 getTransmissionSample( const in vec2 fragCoord, const in float roughness, const in float ior ) {
		float lod = log2( transmissionSamplerSize.x ) * applyIorToRoughness( roughness, ior );
		return textureBicubic( transmissionSamplerMap, fragCoord.xy, lod );
	}
	vec3 volumeAttenuation( const in float transmissionDistance, const in vec3 attenuationColor, const in float attenuationDistance ) {
		if ( isinf( attenuationDistance ) ) {
			return vec3( 1.0 );
		} else {
			vec3 attenuationCoefficient = -log( attenuationColor ) / attenuationDistance;
			vec3 transmittance = exp( - attenuationCoefficient * transmissionDistance );			return transmittance;
		}
	}
	vec4 getIBLVolumeRefraction( const in vec3 n, const in vec3 v, const in float roughness, const in vec3 diffuseColor,
		const in vec3 specularColor, const in float specularF90, const in vec3 position, const in mat4 modelMatrix,
		const in mat4 viewMatrix, const in mat4 projMatrix, const in float dispersion, const in float ior, const in float thickness,
		const in vec3 attenuationColor, const in float attenuationDistance ) {
		vec4 transmittedLight;
		vec3 transmittance;
		#ifdef USE_DISPERSION
			float halfSpread = ( ior - 1.0 ) * 0.025 * dispersion;
			vec3 iors = vec3( ior - halfSpread, ior, ior + halfSpread );
			for ( int i = 0; i < 3; i ++ ) {
				vec3 transmissionRay = getVolumeTransmissionRay( n, v, thickness, iors[ i ], modelMatrix );
				vec3 refractedRayExit = position + transmissionRay;
				vec4 ndcPos = projMatrix * viewMatrix * vec4( refractedRayExit, 1.0 );
				vec2 refractionCoords = ndcPos.xy / ndcPos.w;
				refractionCoords += 1.0;
				refractionCoords /= 2.0;
				vec4 transmissionSample = getTransmissionSample( refractionCoords, roughness, iors[ i ] );
				transmittedLight[ i ] = transmissionSample[ i ];
				transmittedLight.a += transmissionSample.a;
				transmittance[ i ] = diffuseColor[ i ] * volumeAttenuation( length( transmissionRay ), attenuationColor, attenuationDistance )[ i ];
			}
			transmittedLight.a /= 3.0;
		#else
			vec3 transmissionRay = getVolumeTransmissionRay( n, v, thickness, ior, modelMatrix );
			vec3 refractedRayExit = position + transmissionRay;
			vec4 ndcPos = projMatrix * viewMatrix * vec4( refractedRayExit, 1.0 );
			vec2 refractionCoords = ndcPos.xy / ndcPos.w;
			refractionCoords += 1.0;
			refractionCoords /= 2.0;
			transmittedLight = getTransmissionSample( refractionCoords, roughness, ior );
			transmittance = diffuseColor * volumeAttenuation( length( transmissionRay ), attenuationColor, attenuationDistance );
		#endif
		vec3 attenuatedColor = transmittance * transmittedLight.rgb;
		vec3 F = EnvironmentBRDF( n, v, specularColor, specularF90, roughness );
		float transmittanceFactor = ( transmittance.r + transmittance.g + transmittance.b ) / 3.0;
		return vec4( ( 1.0 - F ) * attenuatedColor, 1.0 - ( 1.0 - transmittedLight.a ) * transmittanceFactor );
	}
#endif`,Qp=`#if defined( USE_UV ) || defined( USE_ANISOTROPY )
	varying vec2 vUv;
#endif
#ifdef USE_MAP
	varying vec2 vMapUv;
#endif
#ifdef USE_ALPHAMAP
	varying vec2 vAlphaMapUv;
#endif
#ifdef USE_LIGHTMAP
	varying vec2 vLightMapUv;
#endif
#ifdef USE_AOMAP
	varying vec2 vAoMapUv;
#endif
#ifdef USE_BUMPMAP
	varying vec2 vBumpMapUv;
#endif
#ifdef USE_NORMALMAP
	varying vec2 vNormalMapUv;
#endif
#ifdef USE_EMISSIVEMAP
	varying vec2 vEmissiveMapUv;
#endif
#ifdef USE_METALNESSMAP
	varying vec2 vMetalnessMapUv;
#endif
#ifdef USE_ROUGHNESSMAP
	varying vec2 vRoughnessMapUv;
#endif
#ifdef USE_ANISOTROPYMAP
	varying vec2 vAnisotropyMapUv;
#endif
#ifdef USE_CLEARCOATMAP
	varying vec2 vClearcoatMapUv;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	varying vec2 vClearcoatNormalMapUv;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	varying vec2 vClearcoatRoughnessMapUv;
#endif
#ifdef USE_IRIDESCENCEMAP
	varying vec2 vIridescenceMapUv;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	varying vec2 vIridescenceThicknessMapUv;
#endif
#ifdef USE_SHEEN_COLORMAP
	varying vec2 vSheenColorMapUv;
#endif
#ifdef USE_SHEEN_ROUGHNESSMAP
	varying vec2 vSheenRoughnessMapUv;
#endif
#ifdef USE_SPECULARMAP
	varying vec2 vSpecularMapUv;
#endif
#ifdef USE_SPECULAR_COLORMAP
	varying vec2 vSpecularColorMapUv;
#endif
#ifdef USE_SPECULAR_INTENSITYMAP
	varying vec2 vSpecularIntensityMapUv;
#endif
#ifdef USE_TRANSMISSIONMAP
	uniform mat3 transmissionMapTransform;
	varying vec2 vTransmissionMapUv;
#endif
#ifdef USE_THICKNESSMAP
	uniform mat3 thicknessMapTransform;
	varying vec2 vThicknessMapUv;
#endif`,em=`#if defined( USE_UV ) || defined( USE_ANISOTROPY )
	varying vec2 vUv;
#endif
#ifdef USE_MAP
	uniform mat3 mapTransform;
	varying vec2 vMapUv;
#endif
#ifdef USE_ALPHAMAP
	uniform mat3 alphaMapTransform;
	varying vec2 vAlphaMapUv;
#endif
#ifdef USE_LIGHTMAP
	uniform mat3 lightMapTransform;
	varying vec2 vLightMapUv;
#endif
#ifdef USE_AOMAP
	uniform mat3 aoMapTransform;
	varying vec2 vAoMapUv;
#endif
#ifdef USE_BUMPMAP
	uniform mat3 bumpMapTransform;
	varying vec2 vBumpMapUv;
#endif
#ifdef USE_NORMALMAP
	uniform mat3 normalMapTransform;
	varying vec2 vNormalMapUv;
#endif
#ifdef USE_DISPLACEMENTMAP
	uniform mat3 displacementMapTransform;
	varying vec2 vDisplacementMapUv;
#endif
#ifdef USE_EMISSIVEMAP
	uniform mat3 emissiveMapTransform;
	varying vec2 vEmissiveMapUv;
#endif
#ifdef USE_METALNESSMAP
	uniform mat3 metalnessMapTransform;
	varying vec2 vMetalnessMapUv;
#endif
#ifdef USE_ROUGHNESSMAP
	uniform mat3 roughnessMapTransform;
	varying vec2 vRoughnessMapUv;
#endif
#ifdef USE_ANISOTROPYMAP
	uniform mat3 anisotropyMapTransform;
	varying vec2 vAnisotropyMapUv;
#endif
#ifdef USE_CLEARCOATMAP
	uniform mat3 clearcoatMapTransform;
	varying vec2 vClearcoatMapUv;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	uniform mat3 clearcoatNormalMapTransform;
	varying vec2 vClearcoatNormalMapUv;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	uniform mat3 clearcoatRoughnessMapTransform;
	varying vec2 vClearcoatRoughnessMapUv;
#endif
#ifdef USE_SHEEN_COLORMAP
	uniform mat3 sheenColorMapTransform;
	varying vec2 vSheenColorMapUv;
#endif
#ifdef USE_SHEEN_ROUGHNESSMAP
	uniform mat3 sheenRoughnessMapTransform;
	varying vec2 vSheenRoughnessMapUv;
#endif
#ifdef USE_IRIDESCENCEMAP
	uniform mat3 iridescenceMapTransform;
	varying vec2 vIridescenceMapUv;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	uniform mat3 iridescenceThicknessMapTransform;
	varying vec2 vIridescenceThicknessMapUv;
#endif
#ifdef USE_SPECULARMAP
	uniform mat3 specularMapTransform;
	varying vec2 vSpecularMapUv;
#endif
#ifdef USE_SPECULAR_COLORMAP
	uniform mat3 specularColorMapTransform;
	varying vec2 vSpecularColorMapUv;
#endif
#ifdef USE_SPECULAR_INTENSITYMAP
	uniform mat3 specularIntensityMapTransform;
	varying vec2 vSpecularIntensityMapUv;
#endif
#ifdef USE_TRANSMISSIONMAP
	uniform mat3 transmissionMapTransform;
	varying vec2 vTransmissionMapUv;
#endif
#ifdef USE_THICKNESSMAP
	uniform mat3 thicknessMapTransform;
	varying vec2 vThicknessMapUv;
#endif`,tm=`#if defined( USE_UV ) || defined( USE_ANISOTROPY )
	vUv = vec3( uv, 1 ).xy;
#endif
#ifdef USE_MAP
	vMapUv = ( mapTransform * vec3( MAP_UV, 1 ) ).xy;
#endif
#ifdef USE_ALPHAMAP
	vAlphaMapUv = ( alphaMapTransform * vec3( ALPHAMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_LIGHTMAP
	vLightMapUv = ( lightMapTransform * vec3( LIGHTMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_AOMAP
	vAoMapUv = ( aoMapTransform * vec3( AOMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_BUMPMAP
	vBumpMapUv = ( bumpMapTransform * vec3( BUMPMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_NORMALMAP
	vNormalMapUv = ( normalMapTransform * vec3( NORMALMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_DISPLACEMENTMAP
	vDisplacementMapUv = ( displacementMapTransform * vec3( DISPLACEMENTMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_EMISSIVEMAP
	vEmissiveMapUv = ( emissiveMapTransform * vec3( EMISSIVEMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_METALNESSMAP
	vMetalnessMapUv = ( metalnessMapTransform * vec3( METALNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_ROUGHNESSMAP
	vRoughnessMapUv = ( roughnessMapTransform * vec3( ROUGHNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_ANISOTROPYMAP
	vAnisotropyMapUv = ( anisotropyMapTransform * vec3( ANISOTROPYMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_CLEARCOATMAP
	vClearcoatMapUv = ( clearcoatMapTransform * vec3( CLEARCOATMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	vClearcoatNormalMapUv = ( clearcoatNormalMapTransform * vec3( CLEARCOAT_NORMALMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	vClearcoatRoughnessMapUv = ( clearcoatRoughnessMapTransform * vec3( CLEARCOAT_ROUGHNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_IRIDESCENCEMAP
	vIridescenceMapUv = ( iridescenceMapTransform * vec3( IRIDESCENCEMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	vIridescenceThicknessMapUv = ( iridescenceThicknessMapTransform * vec3( IRIDESCENCE_THICKNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SHEEN_COLORMAP
	vSheenColorMapUv = ( sheenColorMapTransform * vec3( SHEEN_COLORMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SHEEN_ROUGHNESSMAP
	vSheenRoughnessMapUv = ( sheenRoughnessMapTransform * vec3( SHEEN_ROUGHNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SPECULARMAP
	vSpecularMapUv = ( specularMapTransform * vec3( SPECULARMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SPECULAR_COLORMAP
	vSpecularColorMapUv = ( specularColorMapTransform * vec3( SPECULAR_COLORMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SPECULAR_INTENSITYMAP
	vSpecularIntensityMapUv = ( specularIntensityMapTransform * vec3( SPECULAR_INTENSITYMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_TRANSMISSIONMAP
	vTransmissionMapUv = ( transmissionMapTransform * vec3( TRANSMISSIONMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_THICKNESSMAP
	vThicknessMapUv = ( thicknessMapTransform * vec3( THICKNESSMAP_UV, 1 ) ).xy;
#endif`,nm=`#if defined( USE_ENVMAP ) || defined( DISTANCE ) || defined ( USE_SHADOWMAP ) || defined ( USE_TRANSMISSION ) || NUM_SPOT_LIGHT_COORDS > 0
	vec4 worldPosition = vec4( transformed, 1.0 );
	#ifdef USE_BATCHING
		worldPosition = batchingMatrix * worldPosition;
	#endif
	#ifdef USE_INSTANCING
		worldPosition = instanceMatrix * worldPosition;
	#endif
	worldPosition = modelMatrix * worldPosition;
#endif`,im=`varying vec2 vUv;
uniform mat3 uvTransform;
void main() {
	vUv = ( uvTransform * vec3( uv, 1 ) ).xy;
	gl_Position = vec4( position.xy, 1.0, 1.0 );
}`,sm=`uniform sampler2D t2D;
uniform float backgroundIntensity;
varying vec2 vUv;
void main() {
	vec4 texColor = texture2D( t2D, vUv );
	#ifdef DECODE_VIDEO_TEXTURE
		texColor = vec4( mix( pow( texColor.rgb * 0.9478672986 + vec3( 0.0521327014 ), vec3( 2.4 ) ), texColor.rgb * 0.0773993808, vec3( lessThanEqual( texColor.rgb, vec3( 0.04045 ) ) ) ), texColor.w );
	#endif
	texColor.rgb *= backgroundIntensity;
	gl_FragColor = texColor;
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,rm=`varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
	gl_Position.z = gl_Position.w;
}`,am=`#ifdef ENVMAP_TYPE_CUBE
	uniform samplerCube envMap;
#elif defined( ENVMAP_TYPE_CUBE_UV )
	uniform sampler2D envMap;
#endif
uniform float backgroundBlurriness;
uniform float backgroundIntensity;
uniform mat3 backgroundRotation;
varying vec3 vWorldDirection;
#include <cube_uv_reflection_fragment>
void main() {
	#ifdef ENVMAP_TYPE_CUBE
		vec4 texColor = textureCube( envMap, backgroundRotation * vWorldDirection );
	#elif defined( ENVMAP_TYPE_CUBE_UV )
		vec4 texColor = textureCubeUV( envMap, backgroundRotation * vWorldDirection, backgroundBlurriness );
	#else
		vec4 texColor = vec4( 0.0, 0.0, 0.0, 1.0 );
	#endif
	texColor.rgb *= backgroundIntensity;
	gl_FragColor = texColor;
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,om=`varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
	gl_Position.z = gl_Position.w;
}`,lm=`uniform samplerCube tCube;
uniform float tFlip;
uniform float opacity;
varying vec3 vWorldDirection;
void main() {
	vec4 texColor = textureCube( tCube, vec3( tFlip * vWorldDirection.x, vWorldDirection.yz ) );
	gl_FragColor = texColor;
	gl_FragColor.a *= opacity;
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,cm=`#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
varying vec2 vHighPrecisionZW;
void main() {
	#include <uv_vertex>
	#include <batching_vertex>
	#include <skinbase_vertex>
	#include <morphinstance_vertex>
	#ifdef USE_DISPLACEMENTMAP
		#include <beginnormal_vertex>
		#include <morphnormal_vertex>
		#include <skinnormal_vertex>
	#endif
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vHighPrecisionZW = gl_Position.zw;
}`,um=`#if DEPTH_PACKING == 3200
	uniform float opacity;
#endif
#include <common>
#include <packing>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
varying vec2 vHighPrecisionZW;
void main() {
	vec4 diffuseColor = vec4( 1.0 );
	#include <clipping_planes_fragment>
	#if DEPTH_PACKING == 3200
		diffuseColor.a = opacity;
	#endif
	#include <map_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <logdepthbuf_fragment>
	#ifdef USE_REVERSED_DEPTH_BUFFER
		float fragCoordZ = vHighPrecisionZW[ 0 ] / vHighPrecisionZW[ 1 ];
	#else
		float fragCoordZ = 0.5 * vHighPrecisionZW[ 0 ] / vHighPrecisionZW[ 1 ] + 0.5;
	#endif
	#if DEPTH_PACKING == 3200
		gl_FragColor = vec4( vec3( 1.0 - fragCoordZ ), opacity );
	#elif DEPTH_PACKING == 3201
		gl_FragColor = packDepthToRGBA( fragCoordZ );
	#elif DEPTH_PACKING == 3202
		gl_FragColor = vec4( packDepthToRGB( fragCoordZ ), 1.0 );
	#elif DEPTH_PACKING == 3203
		gl_FragColor = vec4( packDepthToRG( fragCoordZ ), 0.0, 1.0 );
	#endif
}`,hm=`#define DISTANCE
varying vec3 vWorldPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <batching_vertex>
	#include <skinbase_vertex>
	#include <morphinstance_vertex>
	#ifdef USE_DISPLACEMENTMAP
		#include <beginnormal_vertex>
		#include <morphnormal_vertex>
		#include <skinnormal_vertex>
	#endif
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <worldpos_vertex>
	#include <clipping_planes_vertex>
	vWorldPosition = worldPosition.xyz;
}`,dm=`#define DISTANCE
uniform vec3 referencePosition;
uniform float nearDistance;
uniform float farDistance;
varying vec3 vWorldPosition;
#include <common>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( 1.0 );
	#include <clipping_planes_fragment>
	#include <map_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	float dist = length( vWorldPosition - referencePosition );
	dist = ( dist - nearDistance ) / ( farDistance - nearDistance );
	dist = saturate( dist );
	gl_FragColor = vec4( dist, 0.0, 0.0, 1.0 );
}`,fm=`varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
}`,pm=`uniform sampler2D tEquirect;
varying vec3 vWorldDirection;
#include <common>
void main() {
	vec3 direction = normalize( vWorldDirection );
	vec2 sampleUV = equirectUv( direction );
	gl_FragColor = texture2D( tEquirect, sampleUV );
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,mm=`uniform float scale;
attribute float lineDistance;
varying float vLineDistance;
#include <common>
#include <uv_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <morphtarget_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	vLineDistance = scale * lineDistance;
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <fog_vertex>
}`,gm=`uniform vec3 diffuse;
uniform float opacity;
uniform float dashSize;
uniform float totalSize;
varying float vLineDistance;
#include <common>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <fog_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	if ( mod( vLineDistance, totalSize ) > dashSize ) {
		discard;
	}
	vec3 outgoingLight = vec3( 0.0 );
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	outgoingLight = diffuseColor.rgb;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
}`,_m=`#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <envmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#if defined ( USE_ENVMAP ) || defined ( USE_SKINNING )
		#include <beginnormal_vertex>
		#include <morphnormal_vertex>
		#include <skinbase_vertex>
		#include <skinnormal_vertex>
		#include <defaultnormal_vertex>
	#endif
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <worldpos_vertex>
	#include <envmap_vertex>
	#include <fog_vertex>
}`,xm=`uniform vec3 diffuse;
uniform float opacity;
#ifndef FLAT_SHADED
	varying vec3 vNormal;
#endif
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <envmap_common_pars_fragment>
#include <envmap_pars_fragment>
#include <fog_pars_fragment>
#include <specularmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <specularmap_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	#ifdef USE_LIGHTMAP
		vec4 lightMapTexel = texture2D( lightMap, vLightMapUv );
		reflectedLight.indirectDiffuse += lightMapTexel.rgb * lightMapIntensity * RECIPROCAL_PI;
	#else
		reflectedLight.indirectDiffuse += vec3( 1.0 );
	#endif
	#include <aomap_fragment>
	reflectedLight.indirectDiffuse *= diffuseColor.rgb;
	vec3 outgoingLight = reflectedLight.indirectDiffuse;
	#include <envmap_fragment>
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,vm=`#define LAMBERT
varying vec3 vViewPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <envmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <shadowmap_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vViewPosition = - mvPosition.xyz;
	#include <worldpos_vertex>
	#include <envmap_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
}`,ym=`#define LAMBERT
uniform vec3 diffuse;
uniform vec3 emissive;
uniform float opacity;
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <cube_uv_reflection_fragment>
#include <envmap_common_pars_fragment>
#include <envmap_pars_fragment>
#include <envmap_physical_pars_fragment>
#include <fog_pars_fragment>
#include <bsdfs>
#include <lights_pars_begin>
#include <normal_pars_fragment>
#include <lights_lambert_pars_fragment>
#include <shadowmap_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <specularmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive;
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <specularmap_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	#include <emissivemap_fragment>
	#include <lights_lambert_fragment>
	#include <lights_fragment_begin>
	#include <lights_fragment_maps>
	#include <lights_fragment_end>
	#include <aomap_fragment>
	vec3 outgoingLight = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse + totalEmissiveRadiance;
	#include <envmap_fragment>
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,bm=`#define MATCAP
varying vec3 vViewPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <color_pars_vertex>
#include <displacementmap_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <fog_vertex>
	vViewPosition = - mvPosition.xyz;
}`,Mm=`#define MATCAP
uniform vec3 diffuse;
uniform float opacity;
uniform sampler2D matcap;
varying vec3 vViewPosition;
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <fog_pars_fragment>
#include <normal_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	vec3 viewDir = normalize( vViewPosition );
	vec3 x = normalize( vec3( viewDir.z, 0.0, - viewDir.x ) );
	vec3 y = cross( viewDir, x );
	vec2 uv = vec2( dot( x, normal ), dot( y, normal ) ) * 0.495 + 0.5;
	#ifdef USE_MATCAP
		vec4 matcapColor = texture2D( matcap, uv );
	#else
		vec4 matcapColor = vec4( vec3( mix( 0.2, 0.8, uv.y ) ), 1.0 );
	#endif
	vec3 outgoingLight = diffuseColor.rgb * matcapColor.rgb;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,Sm=`#define NORMAL
#if defined( FLAT_SHADED ) || defined( USE_BUMPMAP ) || defined( USE_NORMALMAP_TANGENTSPACE )
	varying vec3 vViewPosition;
#endif
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphinstance_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
#if defined( FLAT_SHADED ) || defined( USE_BUMPMAP ) || defined( USE_NORMALMAP_TANGENTSPACE )
	vViewPosition = - mvPosition.xyz;
#endif
}`,Tm=`#define NORMAL
uniform float opacity;
#if defined( FLAT_SHADED ) || defined( USE_BUMPMAP ) || defined( USE_NORMALMAP_TANGENTSPACE )
	varying vec3 vViewPosition;
#endif
#include <uv_pars_fragment>
#include <normal_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( 0.0, 0.0, 0.0, opacity );
	#include <clipping_planes_fragment>
	#include <logdepthbuf_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	gl_FragColor = vec4( normalize( normal ) * 0.5 + 0.5, diffuseColor.a );
	#ifdef OPAQUE
		gl_FragColor.a = 1.0;
	#endif
}`,Em=`#define PHONG
varying vec3 vViewPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <envmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <shadowmap_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphinstance_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vViewPosition = - mvPosition.xyz;
	#include <worldpos_vertex>
	#include <envmap_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
}`,wm=`#define PHONG
uniform vec3 diffuse;
uniform vec3 emissive;
uniform vec3 specular;
uniform float shininess;
uniform float opacity;
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <cube_uv_reflection_fragment>
#include <envmap_common_pars_fragment>
#include <envmap_pars_fragment>
#include <envmap_physical_pars_fragment>
#include <fog_pars_fragment>
#include <bsdfs>
#include <lights_pars_begin>
#include <normal_pars_fragment>
#include <lights_phong_pars_fragment>
#include <shadowmap_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <specularmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive;
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <specularmap_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	#include <emissivemap_fragment>
	#include <lights_phong_fragment>
	#include <lights_fragment_begin>
	#include <lights_fragment_maps>
	#include <lights_fragment_end>
	#include <aomap_fragment>
	vec3 outgoingLight = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse + reflectedLight.directSpecular + reflectedLight.indirectSpecular + totalEmissiveRadiance;
	#include <envmap_fragment>
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,Am=`#define STANDARD
varying vec3 vViewPosition;
#ifdef USE_TRANSMISSION
	varying vec3 vWorldPosition;
#endif
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <shadowmap_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vViewPosition = - mvPosition.xyz;
	#include <worldpos_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
#ifdef USE_TRANSMISSION
	vWorldPosition = worldPosition.xyz;
#endif
}`,Cm=`#define STANDARD
#ifdef PHYSICAL
	#define IOR
	#define USE_SPECULAR
#endif
uniform vec3 diffuse;
uniform vec3 emissive;
uniform float roughness;
uniform float metalness;
uniform float opacity;
#ifdef IOR
	uniform float ior;
#endif
#ifdef USE_SPECULAR
	uniform float specularIntensity;
	uniform vec3 specularColor;
	#ifdef USE_SPECULAR_COLORMAP
		uniform sampler2D specularColorMap;
	#endif
	#ifdef USE_SPECULAR_INTENSITYMAP
		uniform sampler2D specularIntensityMap;
	#endif
#endif
#ifdef USE_CLEARCOAT
	uniform float clearcoat;
	uniform float clearcoatRoughness;
#endif
#ifdef USE_DISPERSION
	uniform float dispersion;
#endif
#ifdef USE_RETROREFLECTION
	uniform float retroreflectivity;
#endif
#ifdef USE_IRIDESCENCE
	uniform float iridescence;
	uniform float iridescenceIOR;
	uniform float iridescenceThicknessMinimum;
	uniform float iridescenceThicknessMaximum;
#endif
#ifdef USE_SHEEN
	uniform vec3 sheenColor;
	uniform float sheenRoughness;
	#ifdef USE_SHEEN_COLORMAP
		uniform sampler2D sheenColorMap;
	#endif
	#ifdef USE_SHEEN_ROUGHNESSMAP
		uniform sampler2D sheenRoughnessMap;
	#endif
#endif
#ifdef USE_ANISOTROPY
	uniform vec2 anisotropyVector;
	#ifdef USE_ANISOTROPYMAP
		uniform sampler2D anisotropyMap;
	#endif
#endif
varying vec3 vViewPosition;
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <iridescence_fragment>
#include <cube_uv_reflection_fragment>
#include <envmap_common_pars_fragment>
#include <envmap_physical_pars_fragment>
#include <fog_pars_fragment>
#include <lights_pars_begin>
#include <normal_pars_fragment>
#include <lights_physical_pars_fragment>
#include <transmission_pars_fragment>
#include <shadowmap_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <clearcoat_pars_fragment>
#include <iridescence_pars_fragment>
#include <roughnessmap_pars_fragment>
#include <metalnessmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive;
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <roughnessmap_fragment>
	#include <metalnessmap_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	#include <clearcoat_normal_fragment_begin>
	#include <clearcoat_normal_fragment_maps>
	#include <emissivemap_fragment>
	#include <lights_physical_fragment>
	#include <lights_fragment_begin>
	#include <lights_fragment_maps>
	#include <lights_fragment_end>
	#include <aomap_fragment>
	vec3 totalDiffuse = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse;
	vec3 totalSpecular = reflectedLight.directSpecular + reflectedLight.indirectSpecular;
	#include <transmission_fragment>
	vec3 outgoingLight = totalDiffuse + totalSpecular + totalEmissiveRadiance;
	#ifdef USE_SHEEN

		outgoingLight = outgoingLight + sheenSpecularDirect + sheenSpecularIndirect;

	#endif
	#ifdef USE_CLEARCOAT
		float dotNVcc = saturate( dot( geometryClearcoatNormal, geometryViewDir ) );
		vec3 Fcc = F_Schlick( material.clearcoatF0, material.clearcoatF90, dotNVcc );
		outgoingLight = outgoingLight * ( 1.0 - material.clearcoat * Fcc ) + ( clearcoatSpecularDirect + clearcoatSpecularIndirect ) * material.clearcoat;
	#endif
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,Rm=`#define TOON
varying vec3 vViewPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <shadowmap_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vViewPosition = - mvPosition.xyz;
	#include <worldpos_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
}`,Pm=`#define TOON
uniform vec3 diffuse;
uniform vec3 emissive;
uniform float opacity;
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <gradientmap_pars_fragment>
#include <fog_pars_fragment>
#include <bsdfs>
#include <lights_pars_begin>
#include <normal_pars_fragment>
#include <lights_toon_pars_fragment>
#include <shadowmap_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive;
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	#include <emissivemap_fragment>
	#include <lights_toon_fragment>
	#include <lights_fragment_begin>
	#include <lights_fragment_maps>
	#include <lights_fragment_end>
	#include <aomap_fragment>
	vec3 outgoingLight = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse + totalEmissiveRadiance;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,Im=`uniform float size;
uniform float scale;
#include <common>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <morphtarget_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
#ifdef USE_POINTS_UV
	varying vec2 vUv;
	uniform mat3 uvTransform;
#endif
void main() {
	#ifdef USE_POINTS_UV
		vUv = ( uvTransform * vec3( uv, 1 ) ).xy;
	#endif
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <project_vertex>
	gl_PointSize = size;
	#ifdef USE_SIZEATTENUATION
		bool isPerspective = isPerspectiveMatrix( projectionMatrix );
		if ( isPerspective ) gl_PointSize *= ( scale / - mvPosition.z );
	#endif
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <worldpos_vertex>
	#include <fog_vertex>
}`,Lm=`uniform vec3 diffuse;
uniform float opacity;
#include <common>
#include <color_pars_fragment>
#include <map_particle_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <fog_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	vec3 outgoingLight = vec3( 0.0 );
	#include <logdepthbuf_fragment>
	#include <map_particle_fragment>
	#include <color_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	outgoingLight = diffuseColor.rgb;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
}`,Nm=`#include <common>
#include <batching_pars_vertex>
#include <fog_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <shadowmap_pars_vertex>
void main() {
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphinstance_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <worldpos_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
}`,Dm=`uniform vec3 color;
uniform float opacity;
#include <common>
#include <fog_pars_fragment>
#include <bsdfs>
#include <lights_pars_begin>
#include <logdepthbuf_pars_fragment>
#include <shadowmap_pars_fragment>
#include <shadowmask_pars_fragment>
void main() {
	#include <logdepthbuf_fragment>
	gl_FragColor = vec4( color, opacity * ( 1.0 - getShadowMask() ) );
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
}`,Um=`uniform float rotation;
uniform vec2 center;
#include <common>
#include <uv_pars_vertex>
#include <fog_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	vec4 mvPosition = modelViewMatrix[ 3 ];
	vec2 scale = vec2( length( modelMatrix[ 0 ].xyz ), length( modelMatrix[ 1 ].xyz ) );
	#ifndef USE_SIZEATTENUATION
		bool isPerspective = isPerspectiveMatrix( projectionMatrix );
		if ( isPerspective ) scale *= - mvPosition.z;
	#endif
	vec2 alignedPosition = ( position.xy - ( center - vec2( 0.5 ) ) ) * scale;
	vec2 rotatedPosition;
	rotatedPosition.x = cos( rotation ) * alignedPosition.x - sin( rotation ) * alignedPosition.y;
	rotatedPosition.y = sin( rotation ) * alignedPosition.x + cos( rotation ) * alignedPosition.y;
	mvPosition.xy += rotatedPosition;
	gl_Position = projectionMatrix * mvPosition;
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <fog_vertex>
}`,Fm=`uniform vec3 diffuse;
uniform float opacity;
#include <common>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <fog_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	vec3 outgoingLight = vec3( 0.0 );
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	outgoingLight = diffuseColor.rgb;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
}`,ct={alphahash_fragment:nf,alphahash_pars_fragment:sf,alphamap_fragment:rf,alphamap_pars_fragment:af,alphatest_fragment:of,alphatest_pars_fragment:lf,aomap_fragment:cf,aomap_pars_fragment:uf,batching_pars_vertex:hf,batching_vertex:df,begin_vertex:ff,beginnormal_vertex:pf,bsdfs:mf,iridescence_fragment:gf,bumpmap_pars_fragment:_f,clipping_planes_fragment:xf,clipping_planes_pars_fragment:vf,clipping_planes_pars_vertex:yf,clipping_planes_vertex:bf,color_fragment:Mf,color_pars_fragment:Sf,color_pars_vertex:Tf,color_vertex:Ef,common:wf,cube_uv_reflection_fragment:Af,defaultnormal_vertex:Cf,displacementmap_pars_vertex:Rf,displacementmap_vertex:Pf,emissivemap_fragment:If,emissivemap_pars_fragment:Lf,colorspace_fragment:Nf,colorspace_pars_fragment:Df,envmap_fragment:Uf,envmap_common_pars_fragment:Ff,envmap_pars_fragment:kf,envmap_pars_vertex:Of,envmap_physical_pars_fragment:Zf,envmap_vertex:Bf,fog_vertex:zf,fog_pars_vertex:Vf,fog_fragment:Hf,fog_pars_fragment:Gf,gradientmap_pars_fragment:Wf,lightmap_pars_fragment:qf,lights_lambert_fragment:Xf,lights_lambert_pars_fragment:$f,lights_pars_begin:Yf,lights_toon_fragment:jf,lights_toon_pars_fragment:Jf,lights_phong_fragment:Kf,lights_phong_pars_fragment:Qf,lights_physical_fragment:ep,lights_physical_pars_fragment:tp,lights_fragment_begin:np,lights_fragment_maps:ip,lights_fragment_end:sp,lightprobes_pars_fragment:rp,logdepthbuf_fragment:ap,logdepthbuf_pars_fragment:op,logdepthbuf_pars_vertex:lp,logdepthbuf_vertex:cp,map_fragment:up,map_pars_fragment:hp,map_particle_fragment:dp,map_particle_pars_fragment:fp,metalnessmap_fragment:pp,metalnessmap_pars_fragment:mp,morphinstance_vertex:gp,morphcolor_vertex:_p,morphnormal_vertex:xp,morphtarget_pars_vertex:vp,morphtarget_vertex:yp,normal_fragment_begin:bp,normal_fragment_maps:Mp,normal_pars_fragment:Sp,normal_pars_vertex:Tp,normal_vertex:Ep,normalmap_pars_fragment:wp,clearcoat_normal_fragment_begin:Ap,clearcoat_normal_fragment_maps:Cp,clearcoat_pars_fragment:Rp,iridescence_pars_fragment:Pp,opaque_fragment:Ip,packing:Lp,premultiplied_alpha_fragment:Np,project_vertex:Dp,dithering_fragment:Up,dithering_pars_fragment:Fp,roughnessmap_fragment:kp,roughnessmap_pars_fragment:Op,shadowmap_pars_fragment:Bp,shadowmap_pars_vertex:zp,shadowmap_vertex:Vp,shadowmask_pars_fragment:Hp,skinbase_vertex:Gp,skinning_pars_vertex:Wp,skinning_vertex:qp,skinnormal_vertex:Xp,specularmap_fragment:$p,specularmap_pars_fragment:Yp,tonemapping_fragment:Zp,tonemapping_pars_fragment:jp,transmission_fragment:Jp,transmission_pars_fragment:Kp,uv_pars_fragment:Qp,uv_pars_vertex:em,uv_vertex:tm,worldpos_vertex:nm,background_vert:im,background_frag:sm,backgroundCube_vert:rm,backgroundCube_frag:am,cube_vert:om,cube_frag:lm,depth_vert:cm,depth_frag:um,distance_vert:hm,distance_frag:dm,equirect_vert:fm,equirect_frag:pm,linedashed_vert:mm,linedashed_frag:gm,meshbasic_vert:_m,meshbasic_frag:xm,meshlambert_vert:vm,meshlambert_frag:ym,meshmatcap_vert:bm,meshmatcap_frag:Mm,meshnormal_vert:Sm,meshnormal_frag:Tm,meshphong_vert:Em,meshphong_frag:wm,meshphysical_vert:Am,meshphysical_frag:Cm,meshtoon_vert:Rm,meshtoon_frag:Pm,points_vert:Im,points_frag:Lm,shadow_vert:Nm,shadow_frag:Dm,sprite_vert:Um,sprite_frag:Fm},Le={common:{diffuse:{value:new Qe(16777215)},opacity:{value:1},map:{value:null},mapTransform:{value:new st},alphaMap:{value:null},alphaMapTransform:{value:new st},alphaTest:{value:0}},specularmap:{specularMap:{value:null},specularMapTransform:{value:new st}},envmap:{envMap:{value:null},envMapRotation:{value:new st},reflectivity:{value:1},ior:{value:1.5},refractionRatio:{value:.98},dfgLUT:{value:null}},aomap:{aoMap:{value:null},aoMapIntensity:{value:1},aoMapTransform:{value:new st}},lightmap:{lightMap:{value:null},lightMapIntensity:{value:1},lightMapTransform:{value:new st}},bumpmap:{bumpMap:{value:null},bumpMapTransform:{value:new st},bumpScale:{value:1}},normalmap:{normalMap:{value:null},normalMapTransform:{value:new st},normalScale:{value:new De(1,1)}},displacementmap:{displacementMap:{value:null},displacementMapTransform:{value:new st},displacementScale:{value:1},displacementBias:{value:0}},emissivemap:{emissiveMap:{value:null},emissiveMapTransform:{value:new st}},metalnessmap:{metalnessMap:{value:null},metalnessMapTransform:{value:new st}},roughnessmap:{roughnessMap:{value:null},roughnessMapTransform:{value:new st}},gradientmap:{gradientMap:{value:null}},fog:{fogDensity:{value:25e-5},fogNear:{value:1},fogFar:{value:2e3},fogColor:{value:new Qe(16777215)}},lights:{ambientLightColor:{value:[]},lightProbe:{value:[]},sunLights:{value:[],properties:{direction:{},color:{}}},sunLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{}}},sunShadowMatrix:{value:[]},sunShadowCascade:{value:[]},directionalLights:{value:[],properties:{direction:{},color:{}}},directionalLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{}}},directionalShadowMatrix:{value:[]},spotLights:{value:[],properties:{color:{},position:{},direction:{},distance:{},coneCos:{},penumbraCos:{},decay:{}}},spotLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{}}},spotLightMap:{value:[]},spotLightMatrix:{value:[]},pointLights:{value:[],properties:{color:{},position:{},decay:{},distance:{}}},pointLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{},shadowCameraNear:{},shadowCameraFar:{}}},pointShadowMatrix:{value:[]},hemisphereLights:{value:[],properties:{direction:{},skyColor:{},groundColor:{}}},rectAreaLights:{value:[],properties:{color:{},position:{},width:{},height:{}}},ltc_1:{value:null},ltc_2:{value:null},probesSH:{value:null},probesMin:{value:new U},probesMax:{value:new U},probesResolution:{value:new U}},points:{diffuse:{value:new Qe(16777215)},opacity:{value:1},size:{value:1},scale:{value:1},map:{value:null},alphaMap:{value:null},alphaMapTransform:{value:new st},alphaTest:{value:0},uvTransform:{value:new st}},sprite:{diffuse:{value:new Qe(16777215)},opacity:{value:1},center:{value:new De(.5,.5)},rotation:{value:0},map:{value:null},mapTransform:{value:new st},alphaMap:{value:null},alphaMapTransform:{value:new st},alphaTest:{value:0}}},Qn={basic:{uniforms:on([Le.common,Le.specularmap,Le.envmap,Le.aomap,Le.lightmap,Le.fog]),vertexShader:ct.meshbasic_vert,fragmentShader:ct.meshbasic_frag},lambert:{uniforms:on([Le.common,Le.specularmap,Le.envmap,Le.aomap,Le.lightmap,Le.emissivemap,Le.bumpmap,Le.normalmap,Le.displacementmap,Le.fog,Le.lights,{emissive:{value:new Qe(0)},envMapIntensity:{value:1}}]),vertexShader:ct.meshlambert_vert,fragmentShader:ct.meshlambert_frag},phong:{uniforms:on([Le.common,Le.specularmap,Le.envmap,Le.aomap,Le.lightmap,Le.emissivemap,Le.bumpmap,Le.normalmap,Le.displacementmap,Le.fog,Le.lights,{emissive:{value:new Qe(0)},specular:{value:new Qe(1118481)},shininess:{value:30},envMapIntensity:{value:1}}]),vertexShader:ct.meshphong_vert,fragmentShader:ct.meshphong_frag},standard:{uniforms:on([Le.common,Le.envmap,Le.aomap,Le.lightmap,Le.emissivemap,Le.bumpmap,Le.normalmap,Le.displacementmap,Le.roughnessmap,Le.metalnessmap,Le.fog,Le.lights,{emissive:{value:new Qe(0)},roughness:{value:1},metalness:{value:0},envMapIntensity:{value:1}}]),vertexShader:ct.meshphysical_vert,fragmentShader:ct.meshphysical_frag},toon:{uniforms:on([Le.common,Le.aomap,Le.lightmap,Le.emissivemap,Le.bumpmap,Le.normalmap,Le.displacementmap,Le.gradientmap,Le.fog,Le.lights,{emissive:{value:new Qe(0)}}]),vertexShader:ct.meshtoon_vert,fragmentShader:ct.meshtoon_frag},matcap:{uniforms:on([Le.common,Le.bumpmap,Le.normalmap,Le.displacementmap,Le.fog,{matcap:{value:null}}]),vertexShader:ct.meshmatcap_vert,fragmentShader:ct.meshmatcap_frag},points:{uniforms:on([Le.points,Le.fog]),vertexShader:ct.points_vert,fragmentShader:ct.points_frag},dashed:{uniforms:on([Le.common,Le.fog,{scale:{value:1},dashSize:{value:1},totalSize:{value:2}}]),vertexShader:ct.linedashed_vert,fragmentShader:ct.linedashed_frag},depth:{uniforms:on([Le.common,Le.displacementmap]),vertexShader:ct.depth_vert,fragmentShader:ct.depth_frag},normal:{uniforms:on([Le.common,Le.bumpmap,Le.normalmap,Le.displacementmap,{opacity:{value:1}}]),vertexShader:ct.meshnormal_vert,fragmentShader:ct.meshnormal_frag},sprite:{uniforms:on([Le.sprite,Le.fog]),vertexShader:ct.sprite_vert,fragmentShader:ct.sprite_frag},background:{uniforms:{uvTransform:{value:new st},t2D:{value:null},backgroundIntensity:{value:1}},vertexShader:ct.background_vert,fragmentShader:ct.background_frag},backgroundCube:{uniforms:{envMap:{value:null},backgroundBlurriness:{value:0},backgroundIntensity:{value:1},backgroundRotation:{value:new st}},vertexShader:ct.backgroundCube_vert,fragmentShader:ct.backgroundCube_frag},cube:{uniforms:{tCube:{value:null},tFlip:{value:-1},opacity:{value:1}},vertexShader:ct.cube_vert,fragmentShader:ct.cube_frag},equirect:{uniforms:{tEquirect:{value:null}},vertexShader:ct.equirect_vert,fragmentShader:ct.equirect_frag},distance:{uniforms:on([Le.common,Le.displacementmap,{referencePosition:{value:new U},nearDistance:{value:1},farDistance:{value:1e3}}]),vertexShader:ct.distance_vert,fragmentShader:ct.distance_frag},shadow:{uniforms:on([Le.lights,Le.fog,{color:{value:new Qe(0)},opacity:{value:1}}]),vertexShader:ct.shadow_vert,fragmentShader:ct.shadow_frag}};Qn.physical={uniforms:on([Qn.standard.uniforms,{clearcoat:{value:0},clearcoatMap:{value:null},clearcoatMapTransform:{value:new st},clearcoatNormalMap:{value:null},clearcoatNormalMapTransform:{value:new st},clearcoatNormalScale:{value:new De(1,1)},clearcoatRoughness:{value:0},clearcoatRoughnessMap:{value:null},clearcoatRoughnessMapTransform:{value:new st},dispersion:{value:0},retroreflectivity:{value:0},iridescence:{value:0},iridescenceMap:{value:null},iridescenceMapTransform:{value:new st},iridescenceIOR:{value:1.3},iridescenceThicknessMinimum:{value:100},iridescenceThicknessMaximum:{value:400},iridescenceThicknessMap:{value:null},iridescenceThicknessMapTransform:{value:new st},sheen:{value:0},sheenColor:{value:new Qe(0)},sheenColorMap:{value:null},sheenColorMapTransform:{value:new st},sheenRoughness:{value:1},sheenRoughnessMap:{value:null},sheenRoughnessMapTransform:{value:new st},transmission:{value:0},transmissionMap:{value:null},transmissionMapTransform:{value:new st},transmissionSamplerSize:{value:new De},transmissionSamplerMap:{value:null},thickness:{value:0},thicknessMap:{value:null},thicknessMapTransform:{value:new st},attenuationDistance:{value:0},attenuationColor:{value:new Qe(0)},specularColor:{value:new Qe(1,1,1)},specularColorMap:{value:null},specularColorMapTransform:{value:new st},specularIntensity:{value:1},specularIntensityMap:{value:null},specularIntensityMapTransform:{value:new st},anisotropyVector:{value:new De},anisotropyMap:{value:null},anisotropyMapTransform:{value:new st}}]),vertexShader:ct.meshphysical_vert,fragmentShader:ct.meshphysical_frag};var tl={r:0,b:0,g:0},km=new xt,Eh=new st;Eh.set(-1,0,0,0,1,0,0,0,1);function Om(i,e,t,n,s,r){let a=new Qe(0),o=s===!0?0:1,l,c,h=null,f=0,u=null;function d(E){let C=E.isScene===!0?E.background:null;if(C&&C.isTexture){let y=E.backgroundBlurriness>0;C=e.get(C,y)}return C}function g(E){let C=!1,y=d(E);y===null?m(a,o):y&&y.isColor&&(m(y,1),C=!0);let w=i.xr.getEnvironmentBlendMode();w==="additive"?t.buffers.color.setClear(0,0,0,1,r):w==="alpha-blend"&&t.buffers.color.setClear(0,0,0,0,r),(i.autoClear||C)&&(t.buffers.depth.setTest(!0),t.buffers.depth.setMask(!0),t.buffers.color.setMask(!0),i.clear(i.autoClearColor,i.autoClearDepth,i.autoClearStencil))}function b(E,C){let y=d(C);y&&(y.isCubeTexture||y.mapping===Fr)?(c===void 0&&(c=new bt(new Bn(1,1,1),new kt({name:"BackgroundCubeMaterial",uniforms:$i(Qn.backgroundCube.uniforms),vertexShader:Qn.backgroundCube.vertexShader,fragmentShader:Qn.backgroundCube.fragmentShader,side:en,depthTest:!1,depthWrite:!1,fog:!1,allowOverride:!1})),c.geometry.deleteAttribute("normal"),c.geometry.deleteAttribute("uv"),c.onBeforeRender=function(w,T,I){this.matrixWorld.copyPosition(I.matrixWorld)},Object.defineProperty(c.material,"envMap",{get:function(){return this.uniforms.envMap.value}}),n.update(c)),c.material.uniforms.envMap.value=y,c.material.uniforms.backgroundBlurriness.value=C.backgroundBlurriness,c.material.uniforms.backgroundIntensity.value=C.backgroundIntensity,c.material.uniforms.backgroundRotation.value.setFromMatrix4(km.makeRotationFromEuler(C.backgroundRotation)).transpose(),y.isCubeTexture&&y.isRenderTargetTexture===!1&&c.material.uniforms.backgroundRotation.value.premultiply(Eh),c.material.toneMapped=pt.getTransfer(y.colorSpace)!==St,(h!==y||f!==y.version||u!==i.toneMapping)&&(c.material.needsUpdate=!0,h=y,f=y.version,u=i.toneMapping),c.layers.enableAll(),E.unshift(c,c.geometry,c.material,0,0,null)):y&&y.isTexture&&(l===void 0&&(l=new bt(new yr(2,2),new kt({name:"BackgroundMaterial",uniforms:$i(Qn.background.uniforms),vertexShader:Qn.background.vertexShader,fragmentShader:Qn.background.fragmentShader,side:Ti,depthTest:!1,depthWrite:!1,fog:!1,allowOverride:!1})),l.geometry.deleteAttribute("normal"),Object.defineProperty(l.material,"map",{get:function(){return this.uniforms.t2D.value}}),n.update(l)),l.material.uniforms.t2D.value=y,l.material.uniforms.backgroundIntensity.value=C.backgroundIntensity,l.material.toneMapped=pt.getTransfer(y.colorSpace)!==St,y.matrixAutoUpdate===!0&&y.updateMatrix(),l.material.uniforms.uvTransform.value.copy(y.matrix),(h!==y||f!==y.version||u!==i.toneMapping)&&(l.material.needsUpdate=!0,h=y,f=y.version,u=i.toneMapping),l.layers.enableAll(),E.unshift(l,l.geometry,l.material,0,0,null))}function m(E,C){E.getRGB(tl,fc(i)),t.buffers.color.setClear(tl.r,tl.g,tl.b,C,r)}function p(){c!==void 0&&(c.geometry.dispose(),c.material.dispose(),c=void 0),l!==void 0&&(l.geometry.dispose(),l.material.dispose(),l=void 0)}return{getClearColor:function(){return a},setClearColor:function(E,C=1){a.set(E),o=C,m(a,o)},getClearAlpha:function(){return o},setClearAlpha:function(E){o=E,m(a,o)},render:g,addToRenderList:b,dispose:p}}function Bm(i,e){let t=i.getParameter(i.MAX_VERTEX_ATTRIBS),n={},s=u(null),r=s,a=!1;function o(k,G,Y,F,$){let te=!1,re=f(k,F,Y,G);r!==re&&(r=re,c(r.object)),te=d(k,F,Y,$),te&&g(k,F,Y,$),$!==null&&e.update($,i.ELEMENT_ARRAY_BUFFER),(te||a)&&(a=!1,y(k,G,Y,F),$!==null&&i.bindBuffer(i.ELEMENT_ARRAY_BUFFER,e.get($).buffer))}function l(){return i.createVertexArray()}function c(k){return i.bindVertexArray(k)}function h(k){return i.deleteVertexArray(k)}function f(k,G,Y,F){let $=F.wireframe===!0,te=n[G.id];te===void 0&&(te={},n[G.id]=te);let re=k.isInstancedMesh===!0?k.id:0,Z=te[re];Z===void 0&&(Z={},te[re]=Z);let Q=Z[Y.id];Q===void 0&&(Q={},Z[Y.id]=Q);let ce=Q[$];return ce===void 0&&(ce=u(l()),Q[$]=ce),ce}function u(k){let G=[],Y=[],F=[];for(let $=0;$<t;$++)G[$]=0,Y[$]=0,F[$]=0;return{geometry:null,program:null,wireframe:!1,newAttributes:G,enabledAttributes:Y,attributeDivisors:F,object:k,attributes:{},index:null}}function d(k,G,Y,F){let $=r.attributes,te=G.attributes,re=0,Z=Y.getAttributes();for(let Q in Z)if(Z[Q].location>=0){let se=$[Q],Ge=te[Q];if(Ge===void 0&&(Q==="instanceMatrix"&&k.instanceMatrix&&(Ge=k.instanceMatrix),Q==="instanceColor"&&k.instanceColor&&(Ge=k.instanceColor)),se===void 0||se.attribute!==Ge||Ge&&se.data!==Ge.data)return!0;re++}return r.attributesNum!==re||r.index!==F}function g(k,G,Y,F){let $={},te=G.attributes,re=0,Z=Y.getAttributes();for(let Q in Z)if(Z[Q].location>=0){let se=te[Q];se===void 0&&(Q==="instanceMatrix"&&k.instanceMatrix&&(se=k.instanceMatrix),Q==="instanceColor"&&k.instanceColor&&(se=k.instanceColor));let Ge={};Ge.attribute=se,se&&se.data&&(Ge.data=se.data),$[Q]=Ge,re++}r.attributes=$,r.attributesNum=re,r.index=F}function b(){let k=r.newAttributes;for(let G=0,Y=k.length;G<Y;G++)k[G]=0}function m(k){p(k,0)}function p(k,G){let Y=r.newAttributes,F=r.enabledAttributes,$=r.attributeDivisors;Y[k]=1,F[k]===0&&(i.enableVertexAttribArray(k),F[k]=1),$[k]!==G&&(i.vertexAttribDivisor(k,G),$[k]=G)}function E(){let k=r.newAttributes,G=r.enabledAttributes;for(let Y=0,F=G.length;Y<F;Y++)G[Y]!==k[Y]&&(i.disableVertexAttribArray(Y),G[Y]=0)}function C(k,G,Y,F,$,te,re){re===!0?i.vertexAttribIPointer(k,G,Y,$,te):i.vertexAttribPointer(k,G,Y,F,$,te)}function y(k,G,Y,F){b();let $=F.attributes,te=Y.getAttributes(),re=G.defaultAttributeValues;for(let Z in te){let Q=te[Z];if(Q.location>=0){let ce=$[Z];if(ce===void 0&&(Z==="instanceMatrix"&&k.instanceMatrix&&(ce=k.instanceMatrix),Z==="instanceColor"&&k.instanceColor&&(ce=k.instanceColor)),ce!==void 0){let se=ce.normalized,Ge=ce.itemSize,Ce=e.get(ce);if(Ce===void 0)continue;let ut=Ce.buffer,Ze=Ce.type,Xe=Ce.bytesPerElement,ee=Ze===i.INT||Ze===i.UNSIGNED_INT||ce.gpuType===mo;if(ce.isInterleavedBufferAttribute){let ne=ce.data,xe=ne.stride,Pe=ce.offset;if(ne.isInstancedInterleavedBuffer){for(let Re=0;Re<Q.locationSize;Re++)p(Q.location+Re,ne.meshPerAttribute);k.isInstancedMesh!==!0&&F._maxInstanceCount===void 0&&(F._maxInstanceCount=ne.meshPerAttribute*ne.count)}else for(let Re=0;Re<Q.locationSize;Re++)m(Q.location+Re);i.bindBuffer(i.ARRAY_BUFFER,ut);for(let Re=0;Re<Q.locationSize;Re++)C(Q.location+Re,Ge/Q.locationSize,Ze,se,xe*Xe,(Pe+Ge/Q.locationSize*Re)*Xe,ee)}else{if(ce.isInstancedBufferAttribute){for(let ne=0;ne<Q.locationSize;ne++)p(Q.location+ne,ce.meshPerAttribute);k.isInstancedMesh!==!0&&F._maxInstanceCount===void 0&&(F._maxInstanceCount=ce.meshPerAttribute*ce.count)}else for(let ne=0;ne<Q.locationSize;ne++)m(Q.location+ne);i.bindBuffer(i.ARRAY_BUFFER,ut);for(let ne=0;ne<Q.locationSize;ne++)C(Q.location+ne,Ge/Q.locationSize,Ze,se,Ge*Xe,Ge/Q.locationSize*ne*Xe,ee)}}else if(re!==void 0){let se=re[Z];if(se!==void 0)switch(se.length){case 2:i.vertexAttrib2fv(Q.location,se);break;case 3:i.vertexAttrib3fv(Q.location,se);break;case 4:i.vertexAttrib4fv(Q.location,se);break;default:i.vertexAttrib1fv(Q.location,se)}}}}E()}function w(){A();for(let k in n){let G=n[k];for(let Y in G){let F=G[Y];for(let $ in F){let te=F[$];for(let re in te)h(te[re].object),delete te[re];delete F[$]}}delete n[k]}}function T(k){if(n[k.id]===void 0)return;let G=n[k.id];for(let Y in G){let F=G[Y];for(let $ in F){let te=F[$];for(let re in te)h(te[re].object),delete te[re];delete F[$]}}delete n[k.id]}function I(k){for(let G in n){let Y=n[G];for(let F in Y){let $=Y[F];if($[k.id]===void 0)continue;let te=$[k.id];for(let re in te)h(te[re].object),delete te[re];delete $[k.id]}}}function x(k){for(let G in n){let Y=n[G],F=k.isInstancedMesh===!0?k.id:0,$=Y[F];if($!==void 0){for(let te in $){let re=$[te];for(let Z in re)h(re[Z].object),delete re[Z];delete $[te]}delete Y[F],Object.keys(Y).length===0&&delete n[G]}}}function A(){D(),a=!0,r!==s&&(r=s,c(r.object))}function D(){s.geometry=null,s.program=null,s.wireframe=!1}return{setup:o,reset:A,resetDefaultState:D,dispose:w,releaseStatesOfGeometry:T,releaseStatesOfObject:x,releaseStatesOfProgram:I,initAttributes:b,enableAttribute:m,disableUnusedAttributes:E}}function zm(i,e,t){let n;function s(l){n=l}function r(l,c){i.drawArrays(n,l,c),t.update(c,n,1)}function a(l,c,h){h!==0&&(i.drawArraysInstanced(n,l,c,h),t.update(c,n,h))}function o(l,c,h){if(h===0)return;e.get("WEBGL_multi_draw").multiDrawArraysWEBGL(n,l,0,c,0,h);let u=0;for(let d=0;d<h;d++)u+=c[d];t.update(u,n,1)}this.setMode=s,this.render=r,this.renderInstances=a,this.renderMultiDraw=o}function Vm(i,e,t,n){let s;function r(){if(s!==void 0)return s;if(e.has("EXT_texture_filter_anisotropic")===!0){let I=e.get("EXT_texture_filter_anisotropic");s=i.getParameter(I.MAX_TEXTURE_MAX_ANISOTROPY_EXT)}else s=0;return s}function a(I){return!(I!==In&&n.convert(I)!==i.getParameter(i.IMPLEMENTATION_COLOR_READ_FORMAT))}function o(I){let x=I===tn&&(e.has("EXT_color_buffer_half_float")||e.has("EXT_color_buffer_float"));return!(I!==xn&&I!==Pn&&!x&&n.convert(I)!==i.getParameter(i.IMPLEMENTATION_COLOR_READ_TYPE))}function l(I){if(I==="highp"){if(i.getShaderPrecisionFormat(i.VERTEX_SHADER,i.HIGH_FLOAT).precision>0&&i.getShaderPrecisionFormat(i.FRAGMENT_SHADER,i.HIGH_FLOAT).precision>0)return"highp";I="mediump"}return I==="mediump"&&i.getShaderPrecisionFormat(i.VERTEX_SHADER,i.MEDIUM_FLOAT).precision>0&&i.getShaderPrecisionFormat(i.FRAGMENT_SHADER,i.MEDIUM_FLOAT).precision>0?"mediump":"lowp"}let c=t.precision!==void 0?t.precision:"highp",h=l(c);h!==c&&(je("WebGLRenderer:",c,"not supported, using",h,"instead."),c=h);let f=t.logarithmicDepthBuffer===!0,u=t.reversedDepthBuffer===!0&&e.has("EXT_clip_control");t.reversedDepthBuffer===!0&&u===!1&&je("WebGLRenderer: Unable to use reversed depth buffer due to missing EXT_clip_control extension. Fallback to default depth buffer.");let d=i.getParameter(i.MAX_TEXTURE_IMAGE_UNITS),g=i.getParameter(i.MAX_VERTEX_TEXTURE_IMAGE_UNITS),b=i.getParameter(i.MAX_TEXTURE_SIZE),m=i.getParameter(i.MAX_CUBE_MAP_TEXTURE_SIZE),p=i.getParameter(i.MAX_VERTEX_ATTRIBS),E=i.getParameter(i.MAX_VERTEX_UNIFORM_VECTORS),C=i.getParameter(i.MAX_VARYING_VECTORS),y=i.getParameter(i.MAX_FRAGMENT_UNIFORM_VECTORS),w=i.getParameter(i.MAX_SAMPLES),T=i.getParameter(i.SAMPLES);return{isWebGL2:!0,getMaxAnisotropy:r,getMaxPrecision:l,textureFormatReadable:a,textureTypeReadable:o,precision:c,logarithmicDepthBuffer:f,reversedDepthBuffer:u,maxTextures:d,maxVertexTextures:g,maxTextureSize:b,maxCubemapSize:m,maxAttributes:p,maxVertexUniforms:E,maxVaryings:C,maxFragmentUniforms:y,maxSamples:w,samples:T}}function Hm(i){let e=this,t=null,n=0,s=!1,r=!1,a=new Fn,o=new st,l={value:null,needsUpdate:!1};this.uniform=l,this.numPlanes=0,this.numIntersection=0,this.init=function(f,u){let d=f.length!==0||u||n!==0||s;return s=u,n=f.length,d},this.beginShadows=function(){r=!0,h(null)},this.endShadows=function(){r=!1},this.setGlobalState=function(f,u){t=h(f,u,0)},this.setState=function(f,u,d){let g=f.clippingPlanes,b=f.clipIntersection,m=f.clipShadows,p=i.get(f);if(!s||g===null||g.length===0||r&&!m)r?h(null):c();else{let E=r?0:n,C=E*4,y=p.clippingState||null;l.value=y,y=h(g,u,C,d);for(let w=0;w!==C;++w)y[w]=t[w];p.clippingState=y,this.numIntersection=b?this.numPlanes:0,this.numPlanes+=E}};function c(){l.value!==t&&(l.value=t,l.needsUpdate=n>0),e.numPlanes=n,e.numIntersection=0}function h(f,u,d,g){let b=f!==null?f.length:0,m=null;if(b!==0){if(m=l.value,g!==!0||m===null){let p=d+b*4,E=u.matrixWorldInverse;o.getNormalMatrix(E),(m===null||m.length<p)&&(m=new Float32Array(p));for(let C=0,y=d;C!==b;++C,y+=4)a.copy(f[C]).applyMatrix4(E,o),a.normal.toArray(m,y),m[y+3]=a.constant}l.value=m,l.needsUpdate=!0}return e.numPlanes=b,e.numIntersection=0,m}}var Ds=4,Gm=6,Wm=20,qm=256,qr=new Si,ih=new Qe,_c=null,xc=0,vc=0,yc=!1,Xm=new U,Yi=new U,Fs=class{constructor(e){this._renderer=e,this._pingPongRenderTarget=null,this._lodMax=0,this._cubeSize=0,this._sizeLods=[],this._lodMeshes=[],this._backgroundBox=null,this._cubemapMaterial=null,this._equirectMaterial=null,this._blurMaterial=null,this._ggxMaterial=null}fromScene(e,t=0,n=.1,s=100,r={}){let{size:a=256,position:o=Xm}=r;_c=this._renderer.getRenderTarget(),xc=this._renderer.getActiveCubeFace(),vc=this._renderer.getActiveMipmapLevel(),yc=this._renderer.xr.enabled,this._renderer.xr.enabled=!1,this._setSize(a);let l=this._allocateTargets();return l.depthBuffer=!0,this._sceneToCubeUV(e,n,s,l,o),t>0&&this._blur(l,0,0,t),this._applyPMREM(l),this._cleanup(l),l}fromEquirectangular(e,t=null){return this._fromTexture(e,t)}fromCubemap(e,t=null){return this._fromTexture(e,t)}compileCubemapShader(){this._cubemapMaterial===null&&(this._cubemapMaterial=ah(),this._compileMaterial(this._cubemapMaterial))}compileEquirectangularShader(){this._equirectMaterial===null&&(this._equirectMaterial=rh(),this._compileMaterial(this._equirectMaterial))}dispose(){this._dispose(),this._cubemapMaterial!==null&&this._cubemapMaterial.dispose(),this._equirectMaterial!==null&&this._equirectMaterial.dispose(),this._backgroundBox!==null&&(this._backgroundBox.geometry.dispose(),this._backgroundBox.material.dispose())}_setSize(e){this._lodMax=Math.floor(Math.log2(e)),this._cubeSize=Math.pow(2,this._lodMax)}_dispose(){this._blurMaterial!==null&&this._blurMaterial.dispose(),this._ggxMaterial!==null&&this._ggxMaterial.dispose(),this._pingPongRenderTarget!==null&&this._pingPongRenderTarget.dispose();for(let e=0;e<this._lodMeshes.length;e++)this._lodMeshes[e].geometry.dispose()}_cleanup(e){this._renderer.setRenderTarget(_c,xc,vc),this._renderer.xr.enabled=yc,e.scissorTest=!1,Ns(e,0,0,e.width,e.height)}_fromTexture(e,t){e.mapping===Ei||e.mapping===Xi?this._setSize(e.image.length===0?16:e.image[0].width||e.image[0].image.width):this._setSize(e.image.width/4),_c=this._renderer.getRenderTarget(),xc=this._renderer.getActiveCubeFace(),vc=this._renderer.getActiveMipmapLevel(),yc=this._renderer.xr.enabled,this._renderer.xr.enabled=!1;let n=t||this._allocateTargets();return this._textureToCubeUV(e,n),this._applyPMREM(n),this._cleanup(n),n}_allocateTargets(){let e=3*Math.max(this._cubeSize,112),t=4*this._cubeSize,n={magFilter:Qt,minFilter:Qt,generateMipmaps:!1,type:tn,format:In,colorSpace:ir,depthBuffer:!1},s=sh(e,t,n);if(this._pingPongRenderTarget===null||this._pingPongRenderTarget.width!==e||this._pingPongRenderTarget.height!==t){this._pingPongRenderTarget!==null&&this._dispose(),this._pingPongRenderTarget=sh(e,t,n);let{_lodMax:r}=this;({lodMeshes:this._lodMeshes,sizeLods:this._sizeLods}=$m(r)),this._blurMaterial=Zm(r,e,t),this._ggxMaterial=Ym(r,e,t)}return s}_compileMaterial(e){let t=new bt(new Rt,e);this._renderer.compile(t,qr)}_sceneToCubeUV(e,t,n,s,r){let l=new Jt(90,1,t,n),c=[1,-1,1,1,1,1],h=[1,1,1,-1,-1,-1],f=this._renderer,u=f.autoClear,d=f.toneMapping;f.getClearColor(ih),f.toneMapping=zn,f.autoClear=!1,f.state.buffers.depth.getReversed()&&(f.setRenderTarget(s),f.clearDepth(),f.setRenderTarget(null)),this._backgroundBox===null&&(this._backgroundBox=new bt(new Bn,new un({name:"PMREM.Background",side:en,depthWrite:!1,depthTest:!1})));let b=this._backgroundBox,m=b.material,p=!1,E=e.background;E?E.isColor&&(m.color.copy(E),e.background=null,p=!0):(m.color.copy(ih),p=!0);for(let C=0;C<6;C++){let y=C%3;y===0?(l.up.set(0,c[C],0),l.position.set(r.x,r.y,r.z),l.lookAt(r.x+h[C],r.y,r.z)):y===1?(l.up.set(0,0,c[C]),l.position.set(r.x,r.y,r.z),l.lookAt(r.x,r.y+h[C],r.z)):(l.up.set(0,c[C],0),l.position.set(r.x,r.y,r.z),l.lookAt(r.x,r.y,r.z+h[C]));let w=this._cubeSize;Ns(s,y*w,C>2?w:0,w,w),f.setRenderTarget(s),p&&f.render(b,l),f.render(e,l)}f.toneMapping=d,f.autoClear=u,e.background=E}_textureToCubeUV(e,t){let n=this._renderer,s=e.mapping===Ei||e.mapping===Xi;s?(this._cubemapMaterial===null&&(this._cubemapMaterial=ah()),this._cubemapMaterial.uniforms.flipEnvMap.value=e.isRenderTargetTexture===!1?-1:1):this._equirectMaterial===null&&(this._equirectMaterial=rh());let r=s?this._cubemapMaterial:this._equirectMaterial,a=this._lodMeshes[0];a.material=r;let o=r.uniforms;o.envMap.value=e;let l=this._cubeSize;Ns(t,0,0,3*l,2*l),n.setRenderTarget(t),n.render(a,qr)}_applyPMREM(e){let t=this._renderer,n=t.autoClear;t.autoClear=!1;let s=this._lodMeshes.length;for(let r=1;r<s;r++)this._applyGGXFilter(e,r-1,r);t.autoClear=n}_applyGGXFilter(e,t,n){let s=this._renderer,r=this._pingPongRenderTarget,a=this._ggxMaterial,o=this._lodMeshes[n];o.material=a;let l=a.uniforms,c=n/(this._lodMeshes.length-1),h=t/(this._lodMeshes.length-1),f=Math.sqrt(c*c-h*h),u=c*1.25,d=f*u,{_lodMax:g}=this,b=this._sizeLods[n],m=3*b*(n>g-Ds?n-g+Ds:0),p=4*(this._cubeSize-b);l.envMap.value=e.texture,l.roughness.value=d,l.mipInt.value=g-t,Ns(r,m,p,3*b,2*b),s.setRenderTarget(r),s.render(o,qr),l.envMap.value=r.texture,l.roughness.value=0,l.mipInt.value=g-n,Ns(e,m,p,3*b,2*b),s.setRenderTarget(e),s.render(o,qr)}_blur(e,t,n,s){let r=this._pingPongRenderTarget,a=Math.min(s,Math.PI)/Math.SQRT2;this._blurPass(e,r,t,n,a),this._blurPass(r,e,n,n,a)}_blurPass(e,t,n,s,r){let a=this._renderer,o=this._blurMaterial,l=this._lodMeshes[s];l.material=o;let c=o.uniforms;c.envMap.value=e.texture,c.sigma.value=r,c.mipInt.value=this._lodMax-n;let h=this._sizeLods[s],f=3*h*(s>this._lodMax-Ds?s-this._lodMax+Ds:0),u=4*(this._cubeSize-h);Ns(t,f,u,3*h,2*h),a.setRenderTarget(t),a.render(l,qr)}};function $m(i){let e=[],t=[],n=i,s=i-Ds+1+Gm;for(let r=0;r<s;r++){let a=Math.pow(2,n);e.push(a);let o=1/(a-2),l=-o,c=1+o,h=[l,l,c,l,c,c,l,l,c,c,l,c],f=6,u=6,d=3,g=new Float32Array(d*u*f),b=new Float32Array(d*u*f);for(let p=0;p<f;p++){let E=p%3*2/3-1,C=p>2?0:-1,y=[E,C,0,E+2/3,C,0,E+2/3,C+1,0,E,C,0,E+2/3,C+1,0,E,C+1,0];g.set(y,d*u*p);for(let w=0;w<u;w++){let T=h[w*2]*2-1,I=h[w*2+1]*2-1;p===0?Yi.set(1,I,T):p===1?Yi.set(-T,1,-I):p===2?Yi.set(-T,I,1):p===3?Yi.set(-1,I,-T):p===4?Yi.set(-T,-1,I):Yi.set(T,I,-1),Yi.toArray(b,(p*u+w)*d)}}let m=new Rt;m.setAttribute("position",new Kt(g,d)),m.setAttribute("outputDirection",new Kt(b,d)),t.push(new bt(m,null)),n>Ds&&n--}return{lodMeshes:t,sizeLods:e}}function sh(i,e,t){let n=new Vt(i,e,t);return n.texture.mapping=Fr,n.texture.name="PMREM.cubeUv",n.scissorTest=!0,n}function Ns(i,e,t,n,s){i.viewport.set(e,t,n,s),i.scissor.set(e,t,n,s)}function Ym(i,e,t){return new kt({name:"PMREMGGXConvolution",defines:{GGX_SAMPLES:qm,CUBEUV_TEXEL_WIDTH:1/e,CUBEUV_TEXEL_HEIGHT:1/t,CUBEUV_MAX_MIP:`${i}.0`},uniforms:{envMap:{value:null},roughness:{value:0},mipInt:{value:0}},vertexShader:rl(),fragmentShader:`

			precision highp float;
			precision highp int;

			varying vec3 vOutputDirection;

			uniform sampler2D envMap;
			uniform float roughness;
			uniform float mipInt;

			#define ENVMAP_TYPE_CUBE_UV
			#include <cube_uv_reflection_fragment>

			#define PI 3.14159265359

			// Van der Corput radical inverse
			float radicalInverse_VdC(uint bits) {
				bits = (bits << 16u) | (bits >> 16u);
				bits = ((bits & 0x55555555u) << 1u) | ((bits & 0xAAAAAAAAu) >> 1u);
				bits = ((bits & 0x33333333u) << 2u) | ((bits & 0xCCCCCCCCu) >> 2u);
				bits = ((bits & 0x0F0F0F0Fu) << 4u) | ((bits & 0xF0F0F0F0u) >> 4u);
				bits = ((bits & 0x00FF00FFu) << 8u) | ((bits & 0xFF00FF00u) >> 8u);
				return float(bits) * 2.3283064365386963e-10; // / 0x100000000
			}

			// Hammersley sequence
			vec2 hammersley(uint i, uint N) {
				return vec2(float(i) / float(N), radicalInverse_VdC(i));
			}

			// GGX VNDF importance sampling (Eric Heitz 2018)
			// "Sampling the GGX Distribution of Visible Normals"
			// https://jcgt.org/published/0007/04/01/
			vec3 importanceSampleGGX_VNDF(vec2 Xi, vec3 V, float roughness) {
				float alpha = roughness * roughness;

				// Section 4.1: Orthonormal basis
				vec3 T1 = vec3(1.0, 0.0, 0.0);
				vec3 T2 = cross(V, T1);

				// Section 4.2: Parameterization of projected area
				float r = sqrt(Xi.x);
				float phi = 2.0 * PI * Xi.y;
				float t1 = r * cos(phi);
				float t2 = r * sin(phi);
				float s = 0.5 * (1.0 + V.z);
				t2 = (1.0 - s) * sqrt(1.0 - t1 * t1) + s * t2;

				// Section 4.3: Reprojection onto hemisphere
				vec3 Nh = t1 * T1 + t2 * T2 + sqrt(max(0.0, 1.0 - t1 * t1 - t2 * t2)) * V;

				// Section 3.4: Transform back to ellipsoid configuration
				return normalize(vec3(alpha * Nh.x, alpha * Nh.y, max(0.0, Nh.z)));
			}

			void main() {
				vec3 N = normalize(vOutputDirection);
				vec3 V = N; // Assume view direction equals normal for pre-filtering

				vec3 prefilteredColor = vec3(0.0);
				float totalWeight = 0.0;

				// For very low roughness, just sample the environment directly
				if (roughness < 0.001) {
					gl_FragColor = vec4(bilinearCubeUV(envMap, N, mipInt), 1.0);
					return;
				}

				// Tangent space basis for VNDF sampling
				vec3 up = abs(N.z) < 0.999 ? vec3(0.0, 0.0, 1.0) : vec3(1.0, 0.0, 0.0);
				vec3 tangent = normalize(cross(up, N));
				vec3 bitangent = cross(N, tangent);

				for(uint i = 0u; i < uint(GGX_SAMPLES); i++) {
					vec2 Xi = hammersley(i, uint(GGX_SAMPLES));

					// For PMREM, V = N, so in tangent space V is always (0, 0, 1)
					vec3 H_tangent = importanceSampleGGX_VNDF(Xi, vec3(0.0, 0.0, 1.0), roughness);

					// Transform H back to world space
					vec3 H = normalize(tangent * H_tangent.x + bitangent * H_tangent.y + N * H_tangent.z);
					vec3 L = normalize(2.0 * dot(V, H) * H - V);

					float NdotL = max(dot(N, L), 0.0);

					if(NdotL > 0.0) {
						// Sample environment at fixed mip level
						// VNDF importance sampling handles the distribution filtering
						vec3 sampleColor = bilinearCubeUV(envMap, L, mipInt);

						// Weight by NdotL for the split-sum approximation
						// VNDF PDF naturally accounts for the visible microfacet distribution
						prefilteredColor += sampleColor * NdotL;
						totalWeight += NdotL;
					}
				}

				if (totalWeight > 0.0) {
					prefilteredColor = prefilteredColor / totalWeight;
				}

				gl_FragColor = vec4(prefilteredColor, 1.0);
			}
		`,blending:Rn,depthTest:!1,depthWrite:!1})}function Zm(i,e,t){return new kt({name:"SphericalGaussianBlur",defines:{SAMPLES:Wm,CUBEUV_TEXEL_WIDTH:1/e,CUBEUV_TEXEL_HEIGHT:1/t,CUBEUV_MAX_MIP:`${i}.0`},uniforms:{envMap:{value:null},sigma:{value:0},mipInt:{value:0}},vertexShader:rl(),fragmentShader:`

			precision highp float;
			precision highp int;

			varying vec3 vOutputDirection;

			uniform sampler2D envMap;
			uniform float sigma;
			uniform float mipInt;

			#define ENVMAP_TYPE_CUBE_UV
			#include <cube_uv_reflection_fragment>

			#define PI 3.14159265359
			#define GOLDEN_ANGLE 2.39996322973

			void main() {

				if ( sigma == 0.0 ) {

					gl_FragColor = vec4( bilinearCubeUV( envMap, vOutputDirection, mipInt ), 1.0 );
					return;

				}

				vec3 outputDirection = normalize( vOutputDirection );

				vec3 up = abs( outputDirection.z ) < 0.999 ? vec3( 0.0, 0.0, 1.0 ) : vec3( 1.0, 0.0, 0.0 );
				vec3 tangent = normalize( cross( up, outputDirection ) );
				vec3 bitangent = cross( outputDirection, tangent );

				// Truncate the kernel at three standard deviations or at the antipode.
				float thetaMax = min( 3.0 * sigma, PI );
				float truncation = 1.0 - exp( - 0.5 * thetaMax * thetaMax / ( sigma * sigma ) );

				vec3 accumColor = vec3( 0.0 );
				float accumWeight = 0.0;

				for ( int i = 0; i < SAMPLES; i ++ ) {

					// Stratified inverse-CDF sampling of the Gaussian, placed on a golden-angle spiral.
					float stratum = ( float( i ) + 0.5 ) / float( SAMPLES );
					float theta = sigma * sqrt( - 2.0 * log( 1.0 - stratum * truncation ) );
					float phi = float( i ) * GOLDEN_ANGLE;

					vec3 offset = cos( phi ) * tangent + sin( phi ) * bitangent;
					vec3 sampleDirection = cos( theta ) * outputDirection + sin( theta ) * offset;

					// Correct the planar sample density to solid angle.
					float weight = sin( theta ) / theta;

					accumColor += weight * bilinearCubeUV( envMap, sampleDirection, mipInt );
					accumWeight += weight;

				}

				gl_FragColor = vec4( accumColor / accumWeight, 1.0 );

			}
		`,blending:Rn,depthTest:!1,depthWrite:!1})}function rh(){return new kt({name:"EquirectangularToCubeUV",uniforms:{envMap:{value:null}},vertexShader:rl(),fragmentShader:`

			precision mediump float;
			precision mediump int;

			varying vec3 vOutputDirection;

			uniform sampler2D envMap;

			#include <common>

			void main() {

				vec3 outputDirection = normalize( vOutputDirection );
				vec2 uv = equirectUv( outputDirection );

				gl_FragColor = vec4( texture2D ( envMap, uv ).rgb, 1.0 );

			}
		`,blending:Rn,depthTest:!1,depthWrite:!1})}function ah(){return new kt({name:"CubemapToCubeUV",uniforms:{envMap:{value:null},flipEnvMap:{value:-1}},vertexShader:rl(),fragmentShader:`

			precision mediump float;
			precision mediump int;

			uniform float flipEnvMap;

			varying vec3 vOutputDirection;

			uniform samplerCube envMap;

			void main() {

				gl_FragColor = textureCube( envMap, vec3( flipEnvMap * vOutputDirection.x, vOutputDirection.yz ) );

			}
		`,blending:Rn,depthTest:!1,depthWrite:!1})}function rl(){return`

		precision mediump float;
		precision mediump int;

		attribute vec3 outputDirection;

		varying vec3 vOutputDirection;

		void main() {

			vOutputDirection = outputDirection;
			gl_Position = vec4( position, 1.0 );

		}
	`}var il=class extends Vt{constructor(e=1,t={}){super(e,e,t),this.isWebGLCubeRenderTarget=!0;let n={width:e,height:e,depth:1},s=[n,n,n,n,n,n];this.texture=new pr(s),this._setTextureOptions(t),this.texture.isRenderTargetTexture=!0}fromEquirectangularTexture(e,t){this.texture.type=t.type,this.texture.colorSpace=t.colorSpace,this.texture.generateMipmaps=t.generateMipmaps,this.texture.minFilter=t.minFilter,this.texture.magFilter=t.magFilter;let n={uniforms:{tEquirect:{value:null}},vertexShader:`

				varying vec3 vWorldDirection;

				vec3 transformDirection( in vec3 dir, in mat4 matrix ) {

					return normalize( ( matrix * vec4( dir, 0.0 ) ).xyz );

				}

				void main() {

					vWorldDirection = transformDirection( position, modelMatrix );

					#include <begin_vertex>
					#include <project_vertex>

				}
			`,fragmentShader:`

				uniform sampler2D tEquirect;

				varying vec3 vWorldDirection;

				#include <common>

				void main() {

					vec3 direction = normalize( vWorldDirection );

					vec2 sampleUV = equirectUv( direction );

					gl_FragColor = texture2D( tEquirect, sampleUV );

				}
			`},s=new Bn(5,5,5),r=new kt({name:"CubemapFromEquirect",uniforms:$i(n.uniforms),vertexShader:n.vertexShader,fragmentShader:n.fragmentShader,side:en,blending:Rn});r.uniforms.tEquirect.value=t;let a=new bt(s,r),o=t.minFilter;return t.minFilter===wi&&(t.minFilter=Qt),new lo(1,10,this).update(e,a),t.minFilter=o,a.geometry.dispose(),a.material.dispose(),this}clear(e,t=!0,n=!0,s=!0){let r=e.getRenderTarget();for(let a=0;a<6;a++)e.setRenderTarget(this,a),e.clear(t,n,s);e.setRenderTarget(r)}};function jm(i){let e=new WeakMap,t=new WeakMap,n=null;function s(u,d=!1){return u==null?null:d?a(u):r(u)}function r(u){if(u&&u.isTexture){let d=u.mapping;if(d===ho||d===fo)if(e.has(u)){let g=e.get(u).texture;return o(g,u.mapping)}else{let g=u.image;if(g&&g.height>0){let b=new il(g.height);return b.fromEquirectangularTexture(i,u),e.set(u,b),u.addEventListener("dispose",c),o(b.texture,u.mapping)}else return null}}return u}function a(u){if(u&&u.isTexture){let d=u.mapping,g=d===ho||d===fo,b=d===Ei||d===Xi;if(g||b){let m=t.get(u),p=m!==void 0?m.texture.pmremVersion:0;if(u.isRenderTargetTexture&&u.pmremVersion!==p)return n===null&&(n=new Fs(i)),m=g?n.fromEquirectangular(u,m):n.fromCubemap(u,m),m.texture.pmremVersion=u.pmremVersion,t.set(u,m),m.texture;if(m!==void 0)return m.texture;{let E=u.image;return g&&E&&E.height>0||b&&E&&l(E)?(n===null&&(n=new Fs(i)),m=g?n.fromEquirectangular(u):n.fromCubemap(u),m.texture.pmremVersion=u.pmremVersion,t.set(u,m),u.addEventListener("dispose",h),m.texture):null}}}return u}function o(u,d){return d===ho?u.mapping=Ei:d===fo&&(u.mapping=Xi),u}function l(u){let d=0,g=6;for(let b=0;b<g;b++)u[b]!==void 0&&d++;return d===g}function c(u){let d=u.target;d.removeEventListener("dispose",c);let g=e.get(d);g!==void 0&&(e.delete(d),g.dispose())}function h(u){let d=u.target;d.removeEventListener("dispose",h);let g=t.get(d);g!==void 0&&(t.delete(d),g.dispose())}function f(){e=new WeakMap,t=new WeakMap,n!==null&&(n.dispose(),n=null)}return{get:s,dispose:f}}function Jm(i){let e={};function t(n){if(e[n]!==void 0)return e[n];let s=i.getExtension(n);return e[n]=s,s}return{has:function(n){return t(n)!==null},init:function(){t("EXT_color_buffer_float"),t("WEBGL_clip_cull_distance"),t("OES_texture_float_linear"),t("EXT_color_buffer_half_float"),t("WEBGL_multisampled_render_to_texture"),t("WEBGL_render_shared_exponent")},get:function(n){let s=t(n);return s===null&&ki("WebGLRenderer: "+n+" extension not supported."),s}}}function Km(i,e,t,n){let s={},r=new WeakMap;function a(f){let u=f.target;u.index!==null&&e.remove(u.index);for(let g in u.attributes)e.remove(u.attributes[g]);u.removeEventListener("dispose",a),delete s[u.id];let d=r.get(u);d&&(e.remove(d),r.delete(u)),n.releaseStatesOfGeometry(u),u.isInstancedBufferGeometry===!0&&delete u._maxInstanceCount,t.memory.geometries--}function o(f,u){return s[u.id]===!0||(u.addEventListener("dispose",a),s[u.id]=!0,t.memory.geometries++),u}function l(f){let u=f.attributes;for(let d in u)e.update(u[d],i.ARRAY_BUFFER)}function c(f){let u=[],d=f.index,g=f.attributes.position,b=0;if(g===void 0)return;if(d!==null){let E=d.array;b=d.version;for(let C=0,y=E.length;C<y;C+=3){let w=E[C+0],T=E[C+1],I=E[C+2];u.push(w,T,T,I,I,w)}}else{let E=g.array;b=g.version;for(let C=0,y=E.length/3-1;C<y;C+=3){let w=C+0,T=C+1,I=C+2;u.push(w,T,T,I,I,w)}}let m=new(g.count>=65535?cr:lr)(u,1);m.version=b;let p=r.get(f);p&&e.remove(p),r.set(f,m)}function h(f){let u=r.get(f);if(u){let d=f.index;d!==null&&u.version<d.version&&c(f)}else c(f);return r.get(f)}return{get:o,update:l,getWireframeAttribute:h}}function Qm(i,e,t){let n;function s(f){n=f}let r,a;function o(f){r=f.type,a=f.bytesPerElement}function l(f,u){i.drawElements(n,u,r,f*a),t.update(u,n,1)}function c(f,u,d){d!==0&&(i.drawElementsInstanced(n,u,r,f*a,d),t.update(u,n,d))}function h(f,u,d){if(d===0)return;e.get("WEBGL_multi_draw").multiDrawElementsWEBGL(n,u,0,r,f,0,d);let b=0;for(let m=0;m<d;m++)b+=u[m];t.update(b,n,1)}this.setMode=s,this.setIndex=o,this.render=l,this.renderInstances=c,this.renderMultiDraw=h}function eg(i){let e={geometries:0,textures:0},t={frame:0,calls:0,triangles:0,points:0,lines:0};function n(r,a,o){switch(t.calls++,a){case i.TRIANGLES:t.triangles+=o*(r/3);break;case i.LINES:t.lines+=o*(r/2);break;case i.LINE_STRIP:t.lines+=o*(r-1);break;case i.LINE_LOOP:t.lines+=o*r;break;case i.POINTS:t.points+=o*r;break;default:nt("WebGLInfo: Unknown draw mode:",a);break}}function s(){t.calls=0,t.triangles=0,t.points=0,t.lines=0}return{memory:e,render:t,programs:null,autoReset:!0,reset:s,update:n}}function tg(i,e,t){let n=new WeakMap,s=new Ut;function r(a,o,l){let c=a.morphTargetInfluences,h=o.morphAttributes.position||o.morphAttributes.normal||o.morphAttributes.color,f=h!==void 0?h.length:0,u=n.get(o);if(u===void 0||u.count!==f){let A=function(){I.dispose(),n.delete(o),o.removeEventListener("dispose",A)};u!==void 0&&u.texture.dispose();let d=o.morphAttributes.position!==void 0,g=o.morphAttributes.normal!==void 0,b=o.morphAttributes.color!==void 0,m=o.morphAttributes.position||[],p=o.morphAttributes.normal||[],E=o.morphAttributes.color||[],C=0;d===!0&&(C=1),g===!0&&(C=2),b===!0&&(C=3);let y=o.attributes.position.count*C,w=1;y>e.maxTextureSize&&(w=Math.ceil(y/e.maxTextureSize),y=e.maxTextureSize);let T=new Float32Array(y*w*4*f),I=new ar(T,y,w,f);I.type=Pn,I.needsUpdate=!0;let x=C*4;for(let D=0;D<f;D++){let k=m[D],G=p[D],Y=E[D],F=y*w*4*D;for(let $=0;$<k.count;$++){let te=$*x;d===!0&&(s.fromBufferAttribute(k,$),T[F+te+0]=s.x,T[F+te+1]=s.y,T[F+te+2]=s.z,T[F+te+3]=0),g===!0&&(s.fromBufferAttribute(G,$),T[F+te+4]=s.x,T[F+te+5]=s.y,T[F+te+6]=s.z,T[F+te+7]=0),b===!0&&(s.fromBufferAttribute(Y,$),T[F+te+8]=s.x,T[F+te+9]=s.y,T[F+te+10]=s.z,T[F+te+11]=Y.itemSize===4?s.w:1)}}u={count:f,texture:I,size:new De(y,w)},n.set(o,u),o.addEventListener("dispose",A)}if(a.isInstancedMesh===!0&&a.morphTexture!==null)l.getUniforms().setValue(i,"morphTexture",a.morphTexture,t);else{let d=0;for(let b=0;b<c.length;b++)d+=c[b];let g=o.morphTargetsRelative?1:1-d;l.getUniforms().setValue(i,"morphTargetBaseInfluence",g),l.getUniforms().setValue(i,"morphTargetInfluences",c)}l.getUniforms().setValue(i,"morphTargetsTexture",u.texture,t),l.getUniforms().setValue(i,"morphTargetsTextureSize",u.size)}return{update:r}}function ng(i,e,t,n,s){let r=new WeakMap;function a(c){let h=s.render.frame,f=c.geometry,u=e.get(c,f);if(r.get(u)!==h&&(e.update(u),r.set(u,h)),c.isInstancedMesh&&(c.hasEventListener("dispose",l)===!1&&c.addEventListener("dispose",l),r.get(c)!==h&&(t.update(c.instanceMatrix,i.ARRAY_BUFFER),c.instanceColor!==null&&t.update(c.instanceColor,i.ARRAY_BUFFER),r.set(c,h))),c.isSkinnedMesh){let d=c.skeleton;r.get(d)!==h&&(d.update(),r.set(d,h))}return u}function o(){r=new WeakMap}function l(c){let h=c.target;h.removeEventListener("dispose",l),n.releaseStatesOfObject(h),t.remove(h.instanceMatrix),h.instanceColor!==null&&t.remove(h.instanceColor)}return{update:a,dispose:o}}var ig={[Pr]:"LINEAR_TONE_MAPPING",[Ir]:"REINHARD_TONE_MAPPING",[Lr]:"CINEON_TONE_MAPPING",[qi]:"ACES_FILMIC_TONE_MAPPING",[Dr]:"AGX_TONE_MAPPING",[Ur]:"NEUTRAL_TONE_MAPPING",[Nr]:"CUSTOM_TONE_MAPPING"};function sg(i,e,t,n,s,r){let a=new Vt(e,t,{type:i,depthBuffer:s,stencilBuffer:r,samples:n?4:0,storeMultisampledDepthBuffer:!1,storeMultisampledStencilBuffer:!1,resolveDepthBuffer:!1,resolveStencilBuffer:!1}),o=null,l=null,c=new Rt;c.setAttribute("position",new yt([-1,3,0,-1,-1,0,3,-1,0],3)),c.setAttribute("uv",new yt([0,2,0,0,2,0],2));let h=new ws({uniforms:{tDiffuse:{value:null}},vertexShader:`
			precision highp float;

			uniform mat4 modelViewMatrix;
			uniform mat4 projectionMatrix;

			attribute vec3 position;
			attribute vec2 uv;

			varying vec2 vUv;

			void main() {
				vUv = uv;
				gl_Position = projectionMatrix * modelViewMatrix * vec4( position, 1.0 );
			}`,fragmentShader:`
			precision highp float;

			uniform sampler2D tDiffuse;

			varying vec2 vUv;

			#include <tonemapping_pars_fragment>
			#include <colorspace_pars_fragment>

			void main() {
				gl_FragColor = texture2D( tDiffuse, vUv );

				#ifdef LINEAR_TONE_MAPPING
					gl_FragColor.rgb = LinearToneMapping( gl_FragColor.rgb );
				#elif defined( REINHARD_TONE_MAPPING )
					gl_FragColor.rgb = ReinhardToneMapping( gl_FragColor.rgb );
				#elif defined( CINEON_TONE_MAPPING )
					gl_FragColor.rgb = CineonToneMapping( gl_FragColor.rgb );
				#elif defined( ACES_FILMIC_TONE_MAPPING )
					gl_FragColor.rgb = ACESFilmicToneMapping( gl_FragColor.rgb );
				#elif defined( AGX_TONE_MAPPING )
					gl_FragColor.rgb = AgXToneMapping( gl_FragColor.rgb );
				#elif defined( NEUTRAL_TONE_MAPPING )
					gl_FragColor.rgb = NeutralToneMapping( gl_FragColor.rgb );
				#elif defined( CUSTOM_TONE_MAPPING )
					gl_FragColor.rgb = CustomToneMapping( gl_FragColor.rgb );
				#endif

				#ifdef SRGB_TRANSFER
					gl_FragColor = sRGBTransferOETF( gl_FragColor );
				#endif
			}`,depthTest:!1,depthWrite:!1}),f=new bt(c,h),u=new Si(-1,1,1,-1,0,1),d=null,g=null,b=!1,m,p=null,E=[],C=!1;this.setSize=function(y,w){a.setSize(y,w),o!==null&&o.setSize(y,w),l!==null&&l.setSize(y,w);for(let T=0;T<E.length;T++){let I=E[T];I.setSize&&I.setSize(y,w)}},this.setEffects=function(y){E=y,C=E.length>0&&E[0].isRenderPass===!0;let w=a.width,T=a.height;E.length>0&&o===null&&(o=new Vt(w,T,{type:tn,depthBuffer:!1,stencilBuffer:!1}),l=new Vt(w,T,{type:tn,depthBuffer:!1,stencilBuffer:!1}));for(let I=0;I<E.length;I++){let x=E[I];x.setSize&&x.setSize(w,T)}},this.begin=function(y,w){if(b||y.toneMapping===zn&&E.length===0)return!1;if(p=w,w!==null){let T=w.width,I=w.height;(a.width!==T||a.height!==I)&&this.setSize(T,I)}return C===!1&&y.setRenderTarget(a),m=y.toneMapping,y.toneMapping=zn,!0},this.hasRenderPass=function(){return C},this.end=function(y,w){y.toneMapping=m,b=!0;let T=a,I=o;for(let x=0;x<E.length;x++){let A=E[x];A.enabled!==!1&&(A.render(y,I,T,w),A.needsSwap!==!1&&(T=I,I=I===o?l:o))}if(d!==y.outputColorSpace||g!==y.toneMapping){d=y.outputColorSpace,g=y.toneMapping,h.defines={},pt.getTransfer(d)===St&&(h.defines.SRGB_TRANSFER="");let x=ig[g];x&&(h.defines[x]=""),h.needsUpdate=!0}h.uniforms.tDiffuse.value=T.texture,y.setRenderTarget(p),y.render(f,u),p=null,b=!1},this.isCompositing=function(){return b},this.dispose=function(){a.dispose(),o!==null&&o.dispose(),l!==null&&l.dispose(),c.dispose(),h.dispose()}}var wh=new mn,Sc=new vi(1,1),Ah=new ar,Ch=new Ba,Rh=new pr,oh=[],lh=[],ch=new Float32Array(16),uh=new Float32Array(9),hh=new Float32Array(4);function ks(i,e,t){let n=i[0];if(n<=0||n>0)return i;let s=e*t,r=oh[s];if(r===void 0&&(r=new Float32Array(s),oh[s]=r),e!==0){n.toArray(r,0);for(let a=1,o=0;a!==e;++a)o+=t,i[a].toArray(r,o)}return r}function Wt(i,e){if(i.length!==e.length)return!1;for(let t=0,n=i.length;t<n;t++)if(i[t]!==e[t])return!1;return!0}function qt(i,e){for(let t=0,n=e.length;t<n;t++)i[t]=e[t]}function al(i,e){let t=lh[e];t===void 0&&(t=new Int32Array(e),lh[e]=t);for(let n=0;n!==e;++n)t[n]=i.allocateTextureUnit();return t}function rg(i,e){let t=this.cache;t[0]!==e&&(i.uniform1f(this.addr,e),t[0]=e)}function ag(i,e){let t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y)&&(i.uniform2f(this.addr,e.x,e.y),t[0]=e.x,t[1]=e.y);else{if(Wt(t,e))return;i.uniform2fv(this.addr,e),qt(t,e)}}function og(i,e){let t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z)&&(i.uniform3f(this.addr,e.x,e.y,e.z),t[0]=e.x,t[1]=e.y,t[2]=e.z);else if(e.r!==void 0)(t[0]!==e.r||t[1]!==e.g||t[2]!==e.b)&&(i.uniform3f(this.addr,e.r,e.g,e.b),t[0]=e.r,t[1]=e.g,t[2]=e.b);else{if(Wt(t,e))return;i.uniform3fv(this.addr,e),qt(t,e)}}function lg(i,e){let t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z||t[3]!==e.w)&&(i.uniform4f(this.addr,e.x,e.y,e.z,e.w),t[0]=e.x,t[1]=e.y,t[2]=e.z,t[3]=e.w);else{if(Wt(t,e))return;i.uniform4fv(this.addr,e),qt(t,e)}}function cg(i,e){let t=this.cache,n=e.elements;if(n===void 0){if(Wt(t,e))return;i.uniformMatrix2fv(this.addr,!1,e),qt(t,e)}else{if(Wt(t,n))return;hh.set(n),i.uniformMatrix2fv(this.addr,!1,hh),qt(t,n)}}function ug(i,e){let t=this.cache,n=e.elements;if(n===void 0){if(Wt(t,e))return;i.uniformMatrix3fv(this.addr,!1,e),qt(t,e)}else{if(Wt(t,n))return;uh.set(n),i.uniformMatrix3fv(this.addr,!1,uh),qt(t,n)}}function hg(i,e){let t=this.cache,n=e.elements;if(n===void 0){if(Wt(t,e))return;i.uniformMatrix4fv(this.addr,!1,e),qt(t,e)}else{if(Wt(t,n))return;ch.set(n),i.uniformMatrix4fv(this.addr,!1,ch),qt(t,n)}}function dg(i,e){let t=this.cache;t[0]!==e&&(i.uniform1i(this.addr,e),t[0]=e)}function fg(i,e){let t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y)&&(i.uniform2i(this.addr,e.x,e.y),t[0]=e.x,t[1]=e.y);else{if(Wt(t,e))return;i.uniform2iv(this.addr,e),qt(t,e)}}function pg(i,e){let t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z)&&(i.uniform3i(this.addr,e.x,e.y,e.z),t[0]=e.x,t[1]=e.y,t[2]=e.z);else{if(Wt(t,e))return;i.uniform3iv(this.addr,e),qt(t,e)}}function mg(i,e){let t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z||t[3]!==e.w)&&(i.uniform4i(this.addr,e.x,e.y,e.z,e.w),t[0]=e.x,t[1]=e.y,t[2]=e.z,t[3]=e.w);else{if(Wt(t,e))return;i.uniform4iv(this.addr,e),qt(t,e)}}function gg(i,e){let t=this.cache;t[0]!==e&&(i.uniform1ui(this.addr,e),t[0]=e)}function _g(i,e){let t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y)&&(i.uniform2ui(this.addr,e.x,e.y),t[0]=e.x,t[1]=e.y);else{if(Wt(t,e))return;i.uniform2uiv(this.addr,e),qt(t,e)}}function xg(i,e){let t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z)&&(i.uniform3ui(this.addr,e.x,e.y,e.z),t[0]=e.x,t[1]=e.y,t[2]=e.z);else{if(Wt(t,e))return;i.uniform3uiv(this.addr,e),qt(t,e)}}function vg(i,e){let t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z||t[3]!==e.w)&&(i.uniform4ui(this.addr,e.x,e.y,e.z,e.w),t[0]=e.x,t[1]=e.y,t[2]=e.z,t[3]=e.w);else{if(Wt(t,e))return;i.uniform4uiv(this.addr,e),qt(t,e)}}function yg(i,e,t){let n=this.cache,s=t.allocateTextureUnit();n[0]!==s&&(i.uniform1i(this.addr,s),n[0]=s);let r;this.type===i.SAMPLER_2D_SHADOW?(Sc.compareFunction=t.isReversedDepthBuffer()?Qo:Ko,r=Sc):r=wh,t.setTexture2D(e||r,s)}function bg(i,e,t){let n=this.cache,s=t.allocateTextureUnit();n[0]!==s&&(i.uniform1i(this.addr,s),n[0]=s),t.setTexture3D(e||Ch,s)}function Mg(i,e,t){let n=this.cache,s=t.allocateTextureUnit();n[0]!==s&&(i.uniform1i(this.addr,s),n[0]=s),t.setTextureCube(e||Rh,s)}function Sg(i,e,t){let n=this.cache,s=t.allocateTextureUnit();n[0]!==s&&(i.uniform1i(this.addr,s),n[0]=s),t.setTexture2DArray(e||Ah,s)}function Tg(i){switch(i){case 5126:return rg;case 35664:return ag;case 35665:return og;case 35666:return lg;case 35674:return cg;case 35675:return ug;case 35676:return hg;case 5124:case 35670:return dg;case 35667:case 35671:return fg;case 35668:case 35672:return pg;case 35669:case 35673:return mg;case 5125:return gg;case 36294:return _g;case 36295:return xg;case 36296:return vg;case 35678:case 36198:case 36298:case 36306:case 35682:return yg;case 35679:case 36299:case 36307:return bg;case 35680:case 36300:case 36308:case 36293:return Mg;case 36289:case 36303:case 36311:case 36292:return Sg}}function Eg(i,e){i.uniform1fv(this.addr,e)}function wg(i,e){let t=ks(e,this.size,2);i.uniform2fv(this.addr,t)}function Ag(i,e){let t=ks(e,this.size,3);i.uniform3fv(this.addr,t)}function Cg(i,e){let t=ks(e,this.size,4);i.uniform4fv(this.addr,t)}function Rg(i,e){let t=ks(e,this.size,4);i.uniformMatrix2fv(this.addr,!1,t)}function Pg(i,e){let t=ks(e,this.size,9);i.uniformMatrix3fv(this.addr,!1,t)}function Ig(i,e){let t=ks(e,this.size,16);i.uniformMatrix4fv(this.addr,!1,t)}function Lg(i,e){i.uniform1iv(this.addr,e)}function Ng(i,e){i.uniform2iv(this.addr,e)}function Dg(i,e){i.uniform3iv(this.addr,e)}function Ug(i,e){i.uniform4iv(this.addr,e)}function Fg(i,e){i.uniform1uiv(this.addr,e)}function kg(i,e){i.uniform2uiv(this.addr,e)}function Og(i,e){i.uniform3uiv(this.addr,e)}function Bg(i,e){i.uniform4uiv(this.addr,e)}function zg(i,e,t){let n=this.cache,s=e.length,r=al(t,s);Wt(n,r)||(i.uniform1iv(this.addr,r),qt(n,r));let a;this.type===i.SAMPLER_2D_SHADOW?a=Sc:a=wh;for(let o=0;o!==s;++o)t.setTexture2D(e[o]||a,r[o])}function Vg(i,e,t){let n=this.cache,s=e.length,r=al(t,s);Wt(n,r)||(i.uniform1iv(this.addr,r),qt(n,r));for(let a=0;a!==s;++a)t.setTexture3D(e[a]||Ch,r[a])}function Hg(i,e,t){let n=this.cache,s=e.length,r=al(t,s);Wt(n,r)||(i.uniform1iv(this.addr,r),qt(n,r));for(let a=0;a!==s;++a)t.setTextureCube(e[a]||Rh,r[a])}function Gg(i,e,t){let n=this.cache,s=e.length,r=al(t,s);Wt(n,r)||(i.uniform1iv(this.addr,r),qt(n,r));for(let a=0;a!==s;++a)t.setTexture2DArray(e[a]||Ah,r[a])}function Wg(i){switch(i){case 5126:return Eg;case 35664:return wg;case 35665:return Ag;case 35666:return Cg;case 35674:return Rg;case 35675:return Pg;case 35676:return Ig;case 5124:case 35670:return Lg;case 35667:case 35671:return Ng;case 35668:case 35672:return Dg;case 35669:case 35673:return Ug;case 5125:return Fg;case 36294:return kg;case 36295:return Og;case 36296:return Bg;case 35678:case 36198:case 36298:case 36306:case 35682:return zg;case 35679:case 36299:case 36307:return Vg;case 35680:case 36300:case 36308:case 36293:return Hg;case 36289:case 36303:case 36311:case 36292:return Gg}}var Tc=class{constructor(e,t,n){this.id=e,this.addr=n,this.cache=[],this.type=t.type,this.setValue=Tg(t.type)}},Ec=class{constructor(e,t,n){this.id=e,this.addr=n,this.cache=[],this.type=t.type,this.size=t.size,this.setValue=Wg(t.type)}},wc=class{constructor(e){this.id=e,this.seq=[],this.map={}}setValue(e,t,n){let s=this.seq;for(let r=0,a=s.length;r!==a;++r){let o=s[r];o.setValue(e,t[o.id],n)}}},bc=/(\w+)(\])?(\[|\.)?/g;function dh(i,e){i.seq.push(e),i.map[e.id]=e}function qg(i,e,t){let n=i.name,s=n.length;for(bc.lastIndex=0;;){let r=bc.exec(n),a=bc.lastIndex,o=r[1],l=r[2]==="]",c=r[3];if(l&&(o=o|0),c===void 0||c==="["&&a+2===s){dh(t,c===void 0?new Tc(o,i,e):new Ec(o,i,e));break}else{let f=t.map[o];f===void 0&&(f=new wc(o),dh(t,f)),t=f}}}var Us=class{constructor(e,t){this.seq=[],this.map={};let n=e.getProgramParameter(t,e.ACTIVE_UNIFORMS);for(let a=0;a<n;++a){let o=e.getActiveUniform(t,a),l=e.getUniformLocation(t,o.name);qg(o,l,this)}let s=[],r=[];for(let a of this.seq)a.type===e.SAMPLER_2D_SHADOW||a.type===e.SAMPLER_CUBE_SHADOW||a.type===e.SAMPLER_2D_ARRAY_SHADOW?s.push(a):r.push(a);s.length>0&&(this.seq=s.concat(r))}setValue(e,t,n,s){let r=this.map[t];r!==void 0&&r.setValue(e,n,s)}setOptional(e,t,n){let s=t[n];s!==void 0&&this.setValue(e,n,s)}static upload(e,t,n,s){for(let r=0,a=t.length;r!==a;++r){let o=t[r],l=n[o.id];l.needsUpdate!==!1&&o.setValue(e,l.value,s)}}static seqWithValue(e,t){let n=[];for(let s=0,r=e.length;s!==r;++s){let a=e[s];a.id in t&&n.push(a)}return n}};function fh(i,e,t){let n=i.createShader(e);return i.shaderSource(n,t),i.compileShader(n),n}var Xg=37297,$g=0;function Yg(i,e){let t=i.split(`
`),n=[],s=Math.max(e-6,0),r=Math.min(e+6,t.length);for(let a=s;a<r;a++){let o=a+1;n.push(`${o===e?">":" "} ${o}: ${t[a]}`)}return n.join(`
`)}var ph=new st;function Zg(i){pt._getMatrix(ph,pt.workingColorSpace,i);let e=`mat3( ${ph.elements.map(t=>t.toFixed(4))} )`;switch(pt.getTransfer(i)){case sr:return[e,"LinearTransferOETF"];case St:return[e,"sRGBTransferOETF"];default:return je("WebGLProgram: Unsupported color space: ",i),[e,"LinearTransferOETF"]}}function mh(i,e,t){let n=i.getShaderParameter(e,i.COMPILE_STATUS),r=(i.getShaderInfoLog(e)||"").trim();if(n&&r==="")return"";let a=/ERROR: 0:(\d+)/.exec(r);if(a){let o=parseInt(a[1]);return t.toUpperCase()+`

`+r+`

`+Yg(i.getShaderSource(e),o)}else return r}function jg(i,e){let t=Zg(e);return[`vec4 ${i}( vec4 value ) {`,`	return ${t[1]}( vec4( value.rgb * ${t[0]}, value.a ) );`,"}"].join(`
`)}var Jg={[Pr]:"Linear",[Ir]:"Reinhard",[Lr]:"Cineon",[qi]:"ACESFilmic",[Dr]:"AgX",[Ur]:"Neutral",[Nr]:"Custom"};function Kg(i,e){let t=Jg[e];return t===void 0?(je("WebGLProgram: Unsupported toneMapping:",e),"vec3 "+i+"( vec3 color ) { return LinearToneMapping( color ); }"):"vec3 "+i+"( vec3 color ) { return "+t+"ToneMapping( color ); }"}var nl=new U;function Qg(){pt.getLuminanceCoefficients(nl);let i=nl.x.toFixed(4),e=nl.y.toFixed(4),t=nl.z.toFixed(4);return["float luminance( const in vec3 rgb ) {",`	const vec3 weights = vec3( ${i}, ${e}, ${t} );`,"	return dot( weights, rgb );","}"].join(`
`)}function e0(i){return[i.extensionClipCullDistance?"#extension GL_ANGLE_clip_cull_distance : require":"",i.extensionMultiDraw?"#extension GL_ANGLE_multi_draw : require":""].filter($r).join(`
`)}function t0(i){let e=[];for(let t in i){let n=i[t];n!==!1&&e.push("#define "+t+" "+n)}return e.join(`
`)}function n0(i,e){let t={},n=i.getProgramParameter(e,i.ACTIVE_ATTRIBUTES);for(let s=0;s<n;s++){let r=i.getActiveAttrib(e,s),a=r.name,o=1;r.type===i.FLOAT_MAT2&&(o=2),r.type===i.FLOAT_MAT3&&(o=3),r.type===i.FLOAT_MAT4&&(o=4),t[a]={type:r.type,location:i.getAttribLocation(e,a),locationSize:o}}return t}function $r(i){return i!==""}function gh(i,e){let t=e.numSpotLightShadows+e.numSpotLightMaps-e.numSpotLightShadowsWithMaps;return i.replace(/NUM_SUN_LIGHTS/g,e.numSunLights).replace(/NUM_DIR_LIGHTS/g,e.numDirLights).replace(/NUM_SPOT_LIGHTS/g,e.numSpotLights).replace(/NUM_SPOT_LIGHT_MAPS/g,e.numSpotLightMaps).replace(/NUM_SPOT_LIGHT_COORDS/g,t).replace(/NUM_RECT_AREA_LIGHTS/g,e.numRectAreaLights).replace(/NUM_POINT_LIGHTS/g,e.numPointLights).replace(/NUM_HEMI_LIGHTS/g,e.numHemiLights).replace(/NUM_SUN_LIGHT_SHADOWS/g,e.numSunLightShadows).replace(/NUM_DIR_LIGHT_SHADOWS/g,e.numDirLightShadows).replace(/NUM_SPOT_LIGHT_SHADOWS_WITH_MAPS/g,e.numSpotLightShadowsWithMaps).replace(/NUM_SPOT_LIGHT_SHADOWS/g,e.numSpotLightShadows).replace(/NUM_POINT_LIGHT_SHADOWS/g,e.numPointLightShadows)}function _h(i,e){return i.replace(/NUM_CLIPPING_PLANES/g,e.numClippingPlanes).replace(/UNION_CLIPPING_PLANES/g,e.numClippingPlanes-e.numClipIntersection)}var i0=/^[ \t]*#include +<([\w\d./]+)>/gm;function Ac(i){return i.replace(i0,r0)}var s0=new Map;function r0(i,e){let t=ct[e];if(t===void 0){let n=s0.get(e);if(n!==void 0)t=ct[n],je('WebGLRenderer: Shader chunk "%s" has been deprecated. Use "%s" instead.',e,n);else throw new Error("THREE.WebGLProgram: Can not resolve #include <"+e+">")}return Ac(t)}var a0=/#pragma unroll_loop_start\s+for\s*\(\s*int\s+i\s*=\s*(\d+)\s*;\s*i\s*<\s*(\d+)\s*;\s*i\s*\+\+\s*\)\s*{([\s\S]+?)}\s+#pragma unroll_loop_end/g;function xh(i){return i.replace(a0,o0)}function o0(i,e,t,n){let s="";for(let r=parseInt(e);r<parseInt(t);r++)s+=n.replace(/\[\s*i\s*\]/g,"[ "+r+" ]").replace(/UNROLLED_LOOP_INDEX/g,r);return s}function vh(i){let e=`precision ${i.precision} float;
	precision ${i.precision} int;
	precision ${i.precision} sampler2D;
	precision ${i.precision} samplerCube;
	precision ${i.precision} sampler3D;
	precision ${i.precision} sampler2DArray;
	precision ${i.precision} sampler2DShadow;
	precision ${i.precision} samplerCubeShadow;
	precision ${i.precision} sampler2DArrayShadow;
	precision ${i.precision} isampler2D;
	precision ${i.precision} isampler3D;
	precision ${i.precision} isamplerCube;
	precision ${i.precision} isampler2DArray;
	precision ${i.precision} usampler2D;
	precision ${i.precision} usampler3D;
	precision ${i.precision} usamplerCube;
	precision ${i.precision} usampler2DArray;
	`;return i.precision==="highp"?e+=`
#define HIGH_PRECISION`:i.precision==="mediump"?e+=`
#define MEDIUM_PRECISION`:i.precision==="lowp"&&(e+=`
#define LOW_PRECISION`),e}var l0={[Rr]:"SHADOWMAP_TYPE_PCF",[Cs]:"SHADOWMAP_TYPE_VSM"};function c0(i){return l0[i.shadowMapType]||"SHADOWMAP_TYPE_BASIC"}var u0={[Ei]:"ENVMAP_TYPE_CUBE",[Xi]:"ENVMAP_TYPE_CUBE",[Fr]:"ENVMAP_TYPE_CUBE_UV"};function h0(i){return i.envMap===!1?"ENVMAP_TYPE_CUBE":u0[i.envMapMode]||"ENVMAP_TYPE_CUBE"}var d0={[Xi]:"ENVMAP_MODE_REFRACTION"};function f0(i){return i.envMap===!1?"ENVMAP_MODE_REFLECTION":d0[i.envMapMode]||"ENVMAP_MODE_REFLECTION"}var p0={[uo]:"ENVMAP_BLENDING_MULTIPLY",[ku]:"ENVMAP_BLENDING_MIX",[Ou]:"ENVMAP_BLENDING_ADD"};function m0(i){return i.envMap===!1?"ENVMAP_BLENDING_NONE":p0[i.combine]||"ENVMAP_BLENDING_NONE"}function g0(i){let e=i.envMapCubeUVHeight;if(e===null)return null;let t=Math.log2(e)-2,n=1/e;return{texelWidth:1/(3*Math.max(Math.pow(2,t),112)),texelHeight:n,maxMip:t}}function _0(i,e,t,n){let s=i.getContext(),r=t.defines,a=t.vertexShader,o=t.fragmentShader,l=c0(t),c=h0(t),h=f0(t),f=m0(t),u=g0(t),d=e0(t),g=t0(r),b=s.createProgram(),m,p,E=t.glslVersion?"#version "+t.glslVersion+`
`:"";t.isRawShaderMaterial?(m=["#define SHADER_TYPE "+t.shaderType,"#define SHADER_NAME "+t.shaderName,g].filter($r).join(`
`),m.length>0&&(m+=`
`),p=["#define SHADER_TYPE "+t.shaderType,"#define SHADER_NAME "+t.shaderName,g].filter($r).join(`
`),p.length>0&&(p+=`
`)):(m=[vh(t),"#define SHADER_TYPE "+t.shaderType,"#define SHADER_NAME "+t.shaderName,g,t.extensionClipCullDistance?"#define USE_CLIP_DISTANCE":"",t.batching?"#define USE_BATCHING":"",t.batchingColor?"#define USE_BATCHING_COLOR":"",t.instancing?"#define USE_INSTANCING":"",t.instancingColor?"#define USE_INSTANCING_COLOR":"",t.instancingMorph?"#define USE_INSTANCING_MORPH":"",t.useFog&&t.fog?"#define USE_FOG":"",t.useFog&&t.fogExp2?"#define FOG_EXP2":"",t.map?"#define USE_MAP":"",t.envMap?"#define USE_ENVMAP":"",t.envMap?"#define "+h:"",t.lightMap?"#define USE_LIGHTMAP":"",t.aoMap?"#define USE_AOMAP":"",t.bumpMap?"#define USE_BUMPMAP":"",t.normalMap?"#define USE_NORMALMAP":"",t.normalMapObjectSpace?"#define USE_NORMALMAP_OBJECTSPACE":"",t.normalMapTangentSpace?"#define USE_NORMALMAP_TANGENTSPACE":"",t.displacementMap?"#define USE_DISPLACEMENTMAP":"",t.emissiveMap?"#define USE_EMISSIVEMAP":"",t.anisotropy?"#define USE_ANISOTROPY":"",t.anisotropyMap?"#define USE_ANISOTROPYMAP":"",t.clearcoatMap?"#define USE_CLEARCOATMAP":"",t.clearcoatRoughnessMap?"#define USE_CLEARCOAT_ROUGHNESSMAP":"",t.clearcoatNormalMap?"#define USE_CLEARCOAT_NORMALMAP":"",t.iridescenceMap?"#define USE_IRIDESCENCEMAP":"",t.iridescenceThicknessMap?"#define USE_IRIDESCENCE_THICKNESSMAP":"",t.specularMap?"#define USE_SPECULARMAP":"",t.specularColorMap?"#define USE_SPECULAR_COLORMAP":"",t.specularIntensityMap?"#define USE_SPECULAR_INTENSITYMAP":"",t.roughnessMap?"#define USE_ROUGHNESSMAP":"",t.metalnessMap?"#define USE_METALNESSMAP":"",t.alphaMap?"#define USE_ALPHAMAP":"",t.alphaHash?"#define USE_ALPHAHASH":"",t.transmission?"#define USE_TRANSMISSION":"",t.transmissionMap?"#define USE_TRANSMISSIONMAP":"",t.thicknessMap?"#define USE_THICKNESSMAP":"",t.sheenColorMap?"#define USE_SHEEN_COLORMAP":"",t.sheenRoughnessMap?"#define USE_SHEEN_ROUGHNESSMAP":"",t.mapUv?"#define MAP_UV "+t.mapUv:"",t.alphaMapUv?"#define ALPHAMAP_UV "+t.alphaMapUv:"",t.lightMapUv?"#define LIGHTMAP_UV "+t.lightMapUv:"",t.aoMapUv?"#define AOMAP_UV "+t.aoMapUv:"",t.emissiveMapUv?"#define EMISSIVEMAP_UV "+t.emissiveMapUv:"",t.bumpMapUv?"#define BUMPMAP_UV "+t.bumpMapUv:"",t.normalMapUv?"#define NORMALMAP_UV "+t.normalMapUv:"",t.displacementMapUv?"#define DISPLACEMENTMAP_UV "+t.displacementMapUv:"",t.metalnessMapUv?"#define METALNESSMAP_UV "+t.metalnessMapUv:"",t.roughnessMapUv?"#define ROUGHNESSMAP_UV "+t.roughnessMapUv:"",t.anisotropyMapUv?"#define ANISOTROPYMAP_UV "+t.anisotropyMapUv:"",t.clearcoatMapUv?"#define CLEARCOATMAP_UV "+t.clearcoatMapUv:"",t.clearcoatNormalMapUv?"#define CLEARCOAT_NORMALMAP_UV "+t.clearcoatNormalMapUv:"",t.clearcoatRoughnessMapUv?"#define CLEARCOAT_ROUGHNESSMAP_UV "+t.clearcoatRoughnessMapUv:"",t.iridescenceMapUv?"#define IRIDESCENCEMAP_UV "+t.iridescenceMapUv:"",t.iridescenceThicknessMapUv?"#define IRIDESCENCE_THICKNESSMAP_UV "+t.iridescenceThicknessMapUv:"",t.sheenColorMapUv?"#define SHEEN_COLORMAP_UV "+t.sheenColorMapUv:"",t.sheenRoughnessMapUv?"#define SHEEN_ROUGHNESSMAP_UV "+t.sheenRoughnessMapUv:"",t.specularMapUv?"#define SPECULARMAP_UV "+t.specularMapUv:"",t.specularColorMapUv?"#define SPECULAR_COLORMAP_UV "+t.specularColorMapUv:"",t.specularIntensityMapUv?"#define SPECULAR_INTENSITYMAP_UV "+t.specularIntensityMapUv:"",t.transmissionMapUv?"#define TRANSMISSIONMAP_UV "+t.transmissionMapUv:"",t.thicknessMapUv?"#define THICKNESSMAP_UV "+t.thicknessMapUv:"",t.vertexTangents&&t.flatShading===!1?"#define USE_TANGENT":"",t.vertexNormals?"#define HAS_NORMAL":"",t.vertexColors?"#define USE_COLOR":"",t.vertexAlphas?"#define USE_COLOR_ALPHA":"",t.vertexUv1s?"#define USE_UV1":"",t.vertexUv2s?"#define USE_UV2":"",t.vertexUv3s?"#define USE_UV3":"",t.pointsUvs?"#define USE_POINTS_UV":"",t.flatShading?"#define FLAT_SHADED":"",t.skinning?"#define USE_SKINNING":"",t.morphTargets?"#define USE_MORPHTARGETS":"",t.morphNormals&&t.flatShading===!1?"#define USE_MORPHNORMALS":"",t.morphColors?"#define USE_MORPHCOLORS":"",t.morphTargetsCount>0?"#define MORPHTARGETS_TEXTURE_STRIDE "+t.morphTextureStride:"",t.morphTargetsCount>0?"#define MORPHTARGETS_COUNT "+t.morphTargetsCount:"",t.doubleSided?"#define DOUBLE_SIDED":"",t.flipSided?"#define FLIP_SIDED":"",t.shadowMapEnabled?"#define USE_SHADOWMAP":"",t.shadowMapEnabled?"#define "+l:"",t.sizeAttenuation?"#define USE_SIZEATTENUATION":"",t.numLightProbes>0?"#define USE_LIGHT_PROBES":"",t.logarithmicDepthBuffer?"#define USE_LOGARITHMIC_DEPTH_BUFFER":"",t.reversedDepthBuffer?"#define USE_REVERSED_DEPTH_BUFFER":"","uniform mat4 modelMatrix;","uniform mat4 modelViewMatrix;","uniform mat4 projectionMatrix;","uniform mat4 viewMatrix;","uniform mat3 normalMatrix;","uniform vec3 cameraPosition;","uniform bool isOrthographic;","#ifdef USE_INSTANCING","	attribute mat4 instanceMatrix;","#endif","#ifdef USE_INSTANCING_COLOR","	attribute vec3 instanceColor;","#endif","#ifdef USE_INSTANCING_MORPH","	uniform sampler2D morphTexture;","#endif","attribute vec3 position;","attribute vec3 normal;","attribute vec2 uv;","#ifdef USE_UV1","	attribute vec2 uv1;","#endif","#ifdef USE_UV2","	attribute vec2 uv2;","#endif","#ifdef USE_UV3","	attribute vec2 uv3;","#endif","#ifdef USE_TANGENT","	attribute vec4 tangent;","#endif","#if defined( USE_COLOR_ALPHA )","	attribute vec4 color;","#elif defined( USE_COLOR )","	attribute vec3 color;","#endif","#ifdef USE_SKINNING","	attribute vec4 skinIndex;","	attribute vec4 skinWeight;","#endif",`
`].filter($r).join(`
`),p=[vh(t),"#define SHADER_TYPE "+t.shaderType,"#define SHADER_NAME "+t.shaderName,g,t.useFog&&t.fog?"#define USE_FOG":"",t.useFog&&t.fogExp2?"#define FOG_EXP2":"",t.alphaToCoverage?"#define ALPHA_TO_COVERAGE":"",t.map?"#define USE_MAP":"",t.matcap?"#define USE_MATCAP":"",t.envMap?"#define USE_ENVMAP":"",t.envMap?"#define "+c:"",t.envMap?"#define "+h:"",t.envMap?"#define "+f:"",u?"#define CUBEUV_TEXEL_WIDTH "+u.texelWidth:"",u?"#define CUBEUV_TEXEL_HEIGHT "+u.texelHeight:"",u?"#define CUBEUV_MAX_MIP "+u.maxMip+".0":"",t.lightMap?"#define USE_LIGHTMAP":"",t.aoMap?"#define USE_AOMAP":"",t.bumpMap?"#define USE_BUMPMAP":"",t.normalMap?"#define USE_NORMALMAP":"",t.normalMapObjectSpace?"#define USE_NORMALMAP_OBJECTSPACE":"",t.normalMapTangentSpace?"#define USE_NORMALMAP_TANGENTSPACE":"",t.packedNormalMap?"#define USE_PACKED_NORMALMAP":"",t.emissiveMap?"#define USE_EMISSIVEMAP":"",t.anisotropy?"#define USE_ANISOTROPY":"",t.anisotropyMap?"#define USE_ANISOTROPYMAP":"",t.clearcoat?"#define USE_CLEARCOAT":"",t.clearcoatMap?"#define USE_CLEARCOATMAP":"",t.clearcoatRoughnessMap?"#define USE_CLEARCOAT_ROUGHNESSMAP":"",t.clearcoatNormalMap?"#define USE_CLEARCOAT_NORMALMAP":"",t.dispersion?"#define USE_DISPERSION":"",t.retroreflection?"#define USE_RETROREFLECTION":"",t.iridescence?"#define USE_IRIDESCENCE":"",t.iridescenceMap?"#define USE_IRIDESCENCEMAP":"",t.iridescenceThicknessMap?"#define USE_IRIDESCENCE_THICKNESSMAP":"",t.specularMap?"#define USE_SPECULARMAP":"",t.specularColorMap?"#define USE_SPECULAR_COLORMAP":"",t.specularIntensityMap?"#define USE_SPECULAR_INTENSITYMAP":"",t.roughnessMap?"#define USE_ROUGHNESSMAP":"",t.metalnessMap?"#define USE_METALNESSMAP":"",t.alphaMap?"#define USE_ALPHAMAP":"",t.alphaTest?"#define USE_ALPHATEST":"",t.alphaHash?"#define USE_ALPHAHASH":"",t.sheen?"#define USE_SHEEN":"",t.sheenColorMap?"#define USE_SHEEN_COLORMAP":"",t.sheenRoughnessMap?"#define USE_SHEEN_ROUGHNESSMAP":"",t.transmission?"#define USE_TRANSMISSION":"",t.transmissionMap?"#define USE_TRANSMISSIONMAP":"",t.thicknessMap?"#define USE_THICKNESSMAP":"",t.vertexTangents&&t.flatShading===!1?"#define USE_TANGENT":"",t.vertexColors||t.instancingColor?"#define USE_COLOR":"",t.vertexAlphas||t.batchingColor?"#define USE_COLOR_ALPHA":"",t.vertexUv1s?"#define USE_UV1":"",t.vertexUv2s?"#define USE_UV2":"",t.vertexUv3s?"#define USE_UV3":"",t.pointsUvs?"#define USE_POINTS_UV":"",t.gradientMap?"#define USE_GRADIENTMAP":"",t.flatShading?"#define FLAT_SHADED":"",t.doubleSided?"#define DOUBLE_SIDED":"",t.flipSided?"#define FLIP_SIDED":"",t.shadowMapEnabled?"#define USE_SHADOWMAP":"",t.shadowMapEnabled?"#define "+l:"",t.premultipliedAlpha?"#define PREMULTIPLIED_ALPHA":"",t.numLightProbes>0?"#define USE_LIGHT_PROBES":"",t.numLightProbeGrids>0?"#define USE_LIGHT_PROBES_GRID":"",t.decodeVideoTexture?"#define DECODE_VIDEO_TEXTURE":"",t.decodeVideoTextureEmissive?"#define DECODE_VIDEO_TEXTURE_EMISSIVE":"",t.logarithmicDepthBuffer?"#define USE_LOGARITHMIC_DEPTH_BUFFER":"",t.reversedDepthBuffer?"#define USE_REVERSED_DEPTH_BUFFER":"","uniform mat4 viewMatrix;","uniform vec3 cameraPosition;","uniform bool isOrthographic;",t.toneMapping!==zn?"#define TONE_MAPPING":"",t.toneMapping!==zn?ct.tonemapping_pars_fragment:"",t.toneMapping!==zn?Kg("toneMapping",t.toneMapping):"",t.dithering?"#define DITHERING":"",t.opaque?"#define OPAQUE":"",ct.colorspace_pars_fragment,jg("linearToOutputTexel",t.outputColorSpace),Qg(),t.useDepthPacking?"#define DEPTH_PACKING "+t.depthPacking:"",`
`].filter($r).join(`
`)),a=Ac(a),a=gh(a,t),a=_h(a,t),o=Ac(o),o=gh(o,t),o=_h(o,t),a=xh(a),o=xh(o),t.isRawShaderMaterial!==!0&&(E=`#version 300 es
`,m=[d,"#define attribute in","#define varying out","#define texture2D texture"].join(`
`)+`
`+m,p=["#define varying in",t.glslVersion===cc?"":"layout(location = 0) out highp vec4 pc_fragColor;",t.glslVersion===cc?"":"#define gl_FragColor pc_fragColor","#define gl_FragDepthEXT gl_FragDepth","#define texture2D texture","#define textureCube texture","#define texture2DProj textureProj","#define texture2DLodEXT textureLod","#define texture2DProjLodEXT textureProjLod","#define textureCubeLodEXT textureLod","#define texture2DGradEXT textureGrad","#define texture2DProjGradEXT textureProjGrad","#define textureCubeGradEXT textureGrad"].join(`
`)+`
`+p);let C=E+m+a,y=E+p+o,w=fh(s,s.VERTEX_SHADER,C),T=fh(s,s.FRAGMENT_SHADER,y);s.attachShader(b,w),s.attachShader(b,T),t.index0AttributeName!==void 0?s.bindAttribLocation(b,0,t.index0AttributeName):t.hasPositionAttribute===!0&&s.bindAttribLocation(b,0,"position"),s.linkProgram(b);function I(k){if(i.debug.checkShaderErrors){let G=s.getProgramInfoLog(b)||"",Y=s.getShaderInfoLog(w)||"",F=s.getShaderInfoLog(T)||"",$=G.trim(),te=Y.trim(),re=F.trim(),Z=!0,Q=!0;if(s.getProgramParameter(b,s.LINK_STATUS)===!1)if(Z=!1,typeof i.debug.onShaderError=="function")i.debug.onShaderError(s,b,w,T);else{let ce=mh(s,w,"vertex"),se=mh(s,T,"fragment");nt("WebGLProgram: Shader Error "+s.getError()+" - VALIDATE_STATUS "+s.getProgramParameter(b,s.VALIDATE_STATUS)+`

Material Name: `+k.name+`
Material Type: `+k.type+`

Program Info Log: `+$+`
`+ce+`
`+se)}else $!==""?je("WebGLProgram: Program Info Log:",$):(te===""||re==="")&&(Q=!1);Q&&(k.diagnostics={runnable:Z,programLog:$,vertexShader:{log:te,prefix:m},fragmentShader:{log:re,prefix:p}})}s.deleteShader(w),s.deleteShader(T),x=new Us(s,b),A=n0(s,b)}let x;this.getUniforms=function(){return x===void 0&&I(this),x};let A;this.getAttributes=function(){return A===void 0&&I(this),A};let D=t.rendererExtensionParallelShaderCompile===!1;return this.isReady=function(){return D===!1&&(D=s.getProgramParameter(b,Xg)),D},this.destroy=function(){n.releaseStatesOfProgram(this),s.deleteProgram(b),this.program=void 0},this.type=t.shaderType,this.name=t.shaderName,this.id=$g++,this.cacheKey=e,this.usedTimes=1,this.program=b,this.vertexShader=w,this.fragmentShader=T,this}var x0=0,Cc=class{constructor(){this.shaderCache=new Map,this.materialCache=new Map}update(e,t,n){let s=this._getShaderCacheForMaterial(e);return s.has(t)===!1&&(s.add(t),t.usedTimes++),s.has(n)===!1&&(s.add(n),n.usedTimes++),this}remove(e){let t=this.materialCache.get(e);for(let n of t)n.usedTimes--,n.usedTimes===0&&this.shaderCache.delete(n.code);return this.materialCache.delete(e),this}getVertexShaderStage(e){return this._getShaderStage(e.vertexShader)}getFragmentShaderStage(e){return this._getShaderStage(e.fragmentShader)}dispose(){this.shaderCache.clear(),this.materialCache.clear()}_getShaderCacheForMaterial(e){let t=this.materialCache,n=t.get(e);return n===void 0&&(n=new Set,t.set(e,n)),n}_getShaderStage(e){let t=this.shaderCache,n=t.get(e);return n===void 0&&(n=new Rc(e),t.set(e,n)),n}},Rc=class{constructor(e){this.id=x0++,this.code=e,this.usedTimes=0}};function v0(i){return i===Ci||i===Hr||i===Gr}function y0(i,e,t,n,s,r){let a=new vs,o=new Cc,l=new Set,c=[],h=new Map,f=n.logarithmicDepthBuffer,u=n.precision,d={MeshDepthMaterial:"depth",MeshDistanceMaterial:"distance",MeshNormalMaterial:"normal",MeshBasicMaterial:"basic",MeshLambertMaterial:"lambert",MeshPhongMaterial:"phong",MeshToonMaterial:"toon",MeshStandardMaterial:"physical",MeshPhysicalMaterial:"physical",MeshMatcapMaterial:"matcap",LineBasicMaterial:"basic",LineDashedMaterial:"dashed",PointsMaterial:"points",ShadowMaterial:"shadow",SpriteMaterial:"sprite"};function g(x){return l.add(x),x===0?"uv":`uv${x}`}function b(x,A,D,k,G,Y){let F=k.fog,$=G.geometry,te=x.isMeshStandardMaterial||x.isMeshLambertMaterial||x.isMeshPhongMaterial?k.environment:null,re=x.isMeshStandardMaterial||x.isMeshLambertMaterial&&!x.envMap||x.isMeshPhongMaterial&&!x.envMap,Z=e.get(x.envMap||te,re),Q=Z&&Z.mapping===Fr?Z.image.height:null,ce=d[x.type];x.precision!==null&&(u=n.getMaxPrecision(x.precision),u!==x.precision&&je("WebGLProgram.getParameters:",x.precision,"not supported, using",u,"instead."));let se=$.morphAttributes.position||$.morphAttributes.normal||$.morphAttributes.color,Ge=se!==void 0?se.length:0,Ce=0;$.morphAttributes.position!==void 0&&(Ce=1),$.morphAttributes.normal!==void 0&&(Ce=2),$.morphAttributes.color!==void 0&&(Ce=3);let ut,Ze,Xe,ee;if(ce){let Ct=Qn[ce];ut=Ct.vertexShader,Ze=Ct.fragmentShader}else{ut=x.vertexShader,Ze=x.fragmentShader;let Ct=o.getVertexShaderStage(x),Mt=o.getFragmentShaderStage(x);o.update(x,Ct,Mt),Xe=Ct.id,ee=Mt.id}let ne=i.getRenderTarget(),xe=i.state.buffers.depth.getReversed(),Pe=G.isInstancedMesh===!0,Re=G.isBatchedMesh===!0,Je=!!x.map,dt=!!x.matcap,it=!!Z,ot=!!x.aoMap,gt=!!x.lightMap,rt=!!x.bumpMap&&x.wireframe===!1,at=!!x.normalMap,Dt=!!x.displacementMap,Lt=!!x.emissiveMap,_t=!!x.metalnessMap,Tt=!!x.roughnessMap,z=x.anisotropy>0,Et=x.clearcoat>0,lt=x.dispersion>0,P=x.retroreflectivity>0,_=x.iridescence>0,X=x.sheen>0,K=x.transmission>0,ae=z&&!!x.anisotropyMap,be=Et&&!!x.clearcoatMap,Ee=Et&&!!x.clearcoatNormalMap,N=Et&&!!x.clearcoatRoughnessMap,V=_&&!!x.iridescenceMap,ie=_&&!!x.iridescenceThicknessMap,ge=X&&!!x.sheenColorMap,ue=X&&!!x.sheenRoughnessMap,pe=!!x.specularMap,_e=!!x.specularColorMap,Se=!!x.specularIntensityMap,Be=K&&!!x.transmissionMap,O=K&&!!x.thicknessMap,Me=!!x.gradientMap,J=!!x.alphaMap,ve=x.alphaTest>0,we=!!x.alphaHash,fe=!!x.extensions,We=zn;x.toneMapped&&(ne===null||ne.isXRRenderTarget===!0)&&(We=i.toneMapping);let Ve={shaderID:ce,shaderType:x.type,shaderName:x.name,vertexShader:ut,fragmentShader:Ze,defines:x.defines,customVertexShaderID:Xe,customFragmentShaderID:ee,isRawShaderMaterial:x.isRawShaderMaterial===!0,glslVersion:x.glslVersion,precision:u,batching:Re,batchingColor:Re&&G._colorsTexture!==null,instancing:Pe,instancingColor:Pe&&G.instanceColor!==null,instancingMorph:Pe&&G.morphTexture!==null,outputColorSpace:ne===null?i.outputColorSpace:ne.isXRRenderTarget===!0?ne.texture.colorSpace:pt.workingColorSpace,alphaToCoverage:!!x.alphaToCoverage,map:Je,matcap:dt,envMap:it,envMapMode:it&&Z.mapping,envMapCubeUVHeight:Q,aoMap:ot,lightMap:gt,bumpMap:rt,normalMap:at,displacementMap:Dt,emissiveMap:Lt,normalMapObjectSpace:at&&x.normalMapType===Vu,normalMapTangentSpace:at&&x.normalMapType===Wr,packedNormalMap:at&&x.normalMapType===Wr&&v0(x.normalMap.format),metalnessMap:_t,roughnessMap:Tt,anisotropy:z,anisotropyMap:ae,clearcoat:Et,clearcoatMap:be,clearcoatNormalMap:Ee,clearcoatRoughnessMap:N,dispersion:lt,retroreflection:P,iridescence:_,iridescenceMap:V,iridescenceThicknessMap:ie,sheen:X,sheenColorMap:ge,sheenRoughnessMap:ue,specularMap:pe,specularColorMap:_e,specularIntensityMap:Se,transmission:K,transmissionMap:Be,thicknessMap:O,gradientMap:Me,opaque:x.transparent===!1&&x.blending===Rs&&x.alphaToCoverage===!1,alphaMap:J,alphaTest:ve,alphaHash:we,combine:x.combine,mapUv:Je&&g(x.map.channel),aoMapUv:ot&&g(x.aoMap.channel),lightMapUv:gt&&g(x.lightMap.channel),bumpMapUv:rt&&g(x.bumpMap.channel),normalMapUv:at&&g(x.normalMap.channel),displacementMapUv:Dt&&g(x.displacementMap.channel),emissiveMapUv:Lt&&g(x.emissiveMap.channel),metalnessMapUv:_t&&g(x.metalnessMap.channel),roughnessMapUv:Tt&&g(x.roughnessMap.channel),anisotropyMapUv:ae&&g(x.anisotropyMap.channel),clearcoatMapUv:be&&g(x.clearcoatMap.channel),clearcoatNormalMapUv:Ee&&g(x.clearcoatNormalMap.channel),clearcoatRoughnessMapUv:N&&g(x.clearcoatRoughnessMap.channel),iridescenceMapUv:V&&g(x.iridescenceMap.channel),iridescenceThicknessMapUv:ie&&g(x.iridescenceThicknessMap.channel),sheenColorMapUv:ge&&g(x.sheenColorMap.channel),sheenRoughnessMapUv:ue&&g(x.sheenRoughnessMap.channel),specularMapUv:pe&&g(x.specularMap.channel),specularColorMapUv:_e&&g(x.specularColorMap.channel),specularIntensityMapUv:Se&&g(x.specularIntensityMap.channel),transmissionMapUv:Be&&g(x.transmissionMap.channel),thicknessMapUv:O&&g(x.thicknessMap.channel),alphaMapUv:J&&g(x.alphaMap.channel),vertexTangents:!!$.attributes.tangent&&(at||z),vertexNormals:!!$.attributes.normal,vertexColors:x.vertexColors,vertexAlphas:x.vertexColors===!0&&!!$.attributes.color&&$.attributes.color.itemSize===4,pointsUvs:G.isPoints===!0&&!!$.attributes.uv&&(Je||J),fog:!!F,useFog:x.fog===!0,fogExp2:!!F&&F.isFogExp2,flatShading:x.wireframe===!1&&(x.flatShading===!0||$.attributes.normal===void 0&&at===!1&&(x.isMeshLambertMaterial||x.isMeshPhongMaterial||x.isMeshStandardMaterial||x.isMeshPhysicalMaterial)),sizeAttenuation:x.sizeAttenuation===!0,logarithmicDepthBuffer:f,reversedDepthBuffer:xe,skinning:G.isSkinnedMesh===!0,hasPositionAttribute:$.attributes.position!==void 0,morphTargets:$.morphAttributes.position!==void 0,morphNormals:$.morphAttributes.normal!==void 0,morphColors:$.morphAttributes.color!==void 0,morphTargetsCount:Ge,morphTextureStride:Ce,numSunLights:A.sun.length,numDirLights:A.directional.length,numPointLights:A.point.length,numSpotLights:A.spot.length,numSpotLightMaps:A.spotLightMap.length,numRectAreaLights:A.rectArea.length,numHemiLights:A.hemi.length,numSunLightShadows:A.sunShadowMap.length,numDirLightShadows:A.directionalShadowMap.length,numPointLightShadows:A.pointShadowMap.length,numSpotLightShadows:A.spotShadowMap.length,numSpotLightShadowsWithMaps:A.numSpotLightShadowsWithMaps,numLightProbes:A.numLightProbes,numLightProbeGrids:Y.length,numClippingPlanes:r.numPlanes,numClipIntersection:r.numIntersection,dithering:x.dithering,shadowMapEnabled:i.shadowMap.enabled&&D.length>0,shadowMapType:i.shadowMap.type,toneMapping:We,decodeVideoTexture:Je&&x.map.isVideoTexture===!0&&pt.getTransfer(x.map.colorSpace)===St,decodeVideoTextureEmissive:Lt&&x.emissiveMap.isVideoTexture===!0&&pt.getTransfer(x.emissiveMap.colorSpace)===St,premultipliedAlpha:x.premultipliedAlpha,doubleSided:x.side===Jn,flipSided:x.side===en,useDepthPacking:x.depthPacking>=0,depthPacking:x.depthPacking||0,index0AttributeName:x.index0AttributeName,extensionClipCullDistance:fe&&x.extensions.clipCullDistance===!0&&t.has("WEBGL_clip_cull_distance"),extensionMultiDraw:(fe&&x.extensions.multiDraw===!0||Re)&&t.has("WEBGL_multi_draw"),rendererExtensionParallelShaderCompile:t.has("KHR_parallel_shader_compile"),customProgramCacheKey:x.customProgramCacheKey()};return Ve.vertexUv1s=l.has(1),Ve.vertexUv2s=l.has(2),Ve.vertexUv3s=l.has(3),l.clear(),Ve}function m(x){let A=[];if(x.shaderID?A.push(x.shaderID):(A.push(x.customVertexShaderID),A.push(x.customFragmentShaderID)),x.defines!==void 0)for(let D in x.defines)A.push(D),A.push(x.defines[D]);return x.isRawShaderMaterial===!1&&(p(A,x),E(A,x),A.push(i.outputColorSpace)),A.push(x.customProgramCacheKey),A.join()}function p(x,A){x.push(A.precision),x.push(A.outputColorSpace),x.push(A.envMapMode),x.push(A.envMapCubeUVHeight),x.push(A.mapUv),x.push(A.alphaMapUv),x.push(A.lightMapUv),x.push(A.aoMapUv),x.push(A.bumpMapUv),x.push(A.normalMapUv),x.push(A.displacementMapUv),x.push(A.emissiveMapUv),x.push(A.metalnessMapUv),x.push(A.roughnessMapUv),x.push(A.anisotropyMapUv),x.push(A.clearcoatMapUv),x.push(A.clearcoatNormalMapUv),x.push(A.clearcoatRoughnessMapUv),x.push(A.iridescenceMapUv),x.push(A.iridescenceThicknessMapUv),x.push(A.sheenColorMapUv),x.push(A.sheenRoughnessMapUv),x.push(A.specularMapUv),x.push(A.specularColorMapUv),x.push(A.specularIntensityMapUv),x.push(A.transmissionMapUv),x.push(A.thicknessMapUv),x.push(A.combine),x.push(A.fogExp2),x.push(A.sizeAttenuation),x.push(A.morphTargetsCount),x.push(A.morphAttributeCount),x.push(A.numSunLights),x.push(A.numDirLights),x.push(A.numPointLights),x.push(A.numSpotLights),x.push(A.numSpotLightMaps),x.push(A.numHemiLights),x.push(A.numRectAreaLights),x.push(A.numSunLightShadows),x.push(A.numDirLightShadows),x.push(A.numPointLightShadows),x.push(A.numSpotLightShadows),x.push(A.numSpotLightShadowsWithMaps),x.push(A.numLightProbes),x.push(A.shadowMapType),x.push(A.toneMapping),x.push(A.numClippingPlanes),x.push(A.numClipIntersection),x.push(A.depthPacking)}function E(x,A){a.disableAll(),A.instancing&&a.enable(0),A.instancingColor&&a.enable(1),A.instancingMorph&&a.enable(2),A.matcap&&a.enable(3),A.envMap&&a.enable(4),A.normalMapObjectSpace&&a.enable(5),A.normalMapTangentSpace&&a.enable(6),A.clearcoat&&a.enable(7),A.iridescence&&a.enable(8),A.alphaTest&&a.enable(9),A.vertexColors&&a.enable(10),A.vertexAlphas&&a.enable(11),A.vertexUv1s&&a.enable(12),A.vertexUv2s&&a.enable(13),A.vertexUv3s&&a.enable(14),A.vertexTangents&&a.enable(15),A.anisotropy&&a.enable(16),A.alphaHash&&a.enable(17),A.batching&&a.enable(18),A.dispersion&&a.enable(19),A.retroreflection&&a.enable(24),A.batchingColor&&a.enable(20),A.gradientMap&&a.enable(21),A.packedNormalMap&&a.enable(22),A.vertexNormals&&a.enable(23),x.push(a.mask),a.disableAll(),A.fog&&a.enable(0),A.useFog&&a.enable(1),A.flatShading&&a.enable(2),A.logarithmicDepthBuffer&&a.enable(3),A.reversedDepthBuffer&&a.enable(4),A.skinning&&a.enable(5),A.morphTargets&&a.enable(6),A.morphNormals&&a.enable(7),A.morphColors&&a.enable(8),A.premultipliedAlpha&&a.enable(9),A.shadowMapEnabled&&a.enable(10),A.doubleSided&&a.enable(11),A.flipSided&&a.enable(12),A.useDepthPacking&&a.enable(13),A.dithering&&a.enable(14),A.transmission&&a.enable(15),A.sheen&&a.enable(16),A.opaque&&a.enable(17),A.pointsUvs&&a.enable(18),A.decodeVideoTexture&&a.enable(19),A.decodeVideoTextureEmissive&&a.enable(20),A.alphaToCoverage&&a.enable(21),A.numLightProbeGrids>0&&a.enable(22),A.hasPositionAttribute&&a.enable(23),x.push(a.mask)}function C(x){let A=d[x.type],D;if(A){let k=Qn[A];D=ci.clone(k.uniforms)}else D=x.uniforms;return D}function y(x,A){let D=h.get(A);return D!==void 0?++D.usedTimes:(D=new _0(i,A,x,s),c.push(D),h.set(A,D)),D}function w(x){if(--x.usedTimes===0){let A=c.indexOf(x);c[A]=c[c.length-1],c.pop(),h.delete(x.cacheKey),x.destroy()}}function T(x){o.remove(x)}function I(){o.dispose()}return{getParameters:b,getProgramCacheKey:m,getUniforms:C,acquireProgram:y,releaseProgram:w,releaseShaderCache:T,programs:c,dispose:I}}function b0(){let i=new WeakMap;function e(a){return i.has(a)}function t(a){let o=i.get(a);return o===void 0&&(o={},i.set(a,o)),o}function n(a){i.delete(a)}function s(a,o,l){i.get(a)[o]=l}function r(){i=new WeakMap}return{has:e,get:t,remove:n,update:s,dispose:r}}function M0(i,e){return i.groupOrder!==e.groupOrder?i.groupOrder-e.groupOrder:i.renderOrder!==e.renderOrder?i.renderOrder-e.renderOrder:i.material.id!==e.material.id?i.material.id-e.material.id:i.materialVariant!==e.materialVariant?i.materialVariant-e.materialVariant:i.z!==e.z?i.z-e.z:i.id-e.id}function yh(i,e){return i.groupOrder!==e.groupOrder?i.groupOrder-e.groupOrder:i.renderOrder!==e.renderOrder?i.renderOrder-e.renderOrder:i.z!==e.z?e.z-i.z:i.id-e.id}function bh(){let i=[],e=0,t=[],n=[],s=[];function r(){e=0,t.length=0,n.length=0,s.length=0}function a(u){let d=0;return u.isInstancedMesh&&(d+=2),u.isSkinnedMesh&&(d+=1),d}function o(u,d,g,b,m,p){let E=i[e];return E===void 0?(E={id:u.id,object:u,geometry:d,material:g,materialVariant:a(u),groupOrder:b,renderOrder:u.renderOrder,z:m,group:p},i[e]=E):(E.id=u.id,E.object=u,E.geometry=d,E.material=g,E.materialVariant=a(u),E.groupOrder=b,E.renderOrder=u.renderOrder,E.z=m,E.group=p),e++,E}function l(u,d,g,b,m,p,E){E.reversedDepth===!0&&(m=-m);let C=o(u,d,g,b,m,p);g.transmission>0?n.push(C):g.transparent===!0?s.push(C):t.push(C)}function c(u,d,g,b,m,p){let E=o(u,d,g,b,m,p);g.transmission>0?n.unshift(E):g.transparent===!0?s.unshift(E):t.unshift(E)}function h(u,d){t.length>1&&t.sort(u||M0),n.length>1&&n.sort(d||yh),s.length>1&&s.sort(d||yh)}function f(){for(let u=e,d=i.length;u<d;u++){let g=i[u];if(g.id===null)break;g.id=null,g.object=null,g.geometry=null,g.material=null,g.group=null}}return{opaque:t,transmissive:n,transparent:s,init:r,push:l,unshift:c,finish:f,sort:h}}function S0(){let i=new WeakMap;function e(n,s){let r=i.get(n),a;return r===void 0?(a=new bh,i.set(n,[a])):s>=r.length?(a=new bh,r.push(a)):a=r[s],a}function t(){i=new WeakMap}return{get:e,dispose:t}}function T0(){let i={};return{get:function(e){if(i[e.id]!==void 0)return i[e.id];let t;switch(e.type){case"SunLight":case"DirectionalLight":t={direction:new U,color:new Qe};break;case"SpotLight":t={position:new U,direction:new U,color:new Qe,distance:0,coneCos:0,penumbraCos:0,decay:0};break;case"PointLight":t={position:new U,color:new Qe,distance:0,decay:0};break;case"HemisphereLight":t={direction:new U,skyColor:new Qe,groundColor:new Qe};break;case"RectAreaLight":t={color:new Qe,position:new U,halfWidth:new U,halfHeight:new U};break}return i[e.id]=t,t}}}function E0(){let i={};return{get:function(e){if(i[e.id]!==void 0)return i[e.id];let t;switch(e.type){case"SunLight":case"DirectionalLight":t={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new De};break;case"SpotLight":t={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new De};break;case"PointLight":t={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new De,shadowCameraNear:1,shadowCameraFar:1e3};break}return i[e.id]=t,t}}}var w0=0;function A0(i,e){return(e.castShadow?2:0)-(i.castShadow?2:0)+(e.map?1:0)-(i.map?1:0)}function C0(i){let e=new T0,t=E0(),n={version:0,hash:{sunLength:-1,directionalLength:-1,pointLength:-1,spotLength:-1,rectAreaLength:-1,hemiLength:-1,numSunShadows:-1,numDirectionalShadows:-1,numPointShadows:-1,numSpotShadows:-1,numSpotMaps:-1,numLightProbes:-1},ambient:[0,0,0],probe:[],sun:[],sunShadow:[],sunShadowMap:[],sunShadowMatrix:[],sunShadowCascade:[],directional:[],directionalShadow:[],directionalShadowMap:[],directionalShadowMatrix:[],spot:[],spotLightMap:[],spotShadow:[],spotShadowMap:[],spotLightMatrix:[],rectArea:[],rectAreaLTC1:null,rectAreaLTC2:null,point:[],pointShadow:[],pointShadowMap:[],pointShadowMatrix:[],hemi:[],numSpotLightShadowsWithMaps:0,numLightProbes:0};for(let c=0;c<9;c++)n.probe.push(new U);let s=new U,r=new xt,a=new xt;function o(c){let h=0,f=0,u=0;for(let G=0;G<9;G++)n.probe[G].set(0,0,0);let d=0,g=0,b=0,m=0,p=0,E=0,C=0,y=0,w=0,T=0,I=0,x=0,A=0,D=0;c.sort(A0);for(let G=0,Y=c.length;G<Y;G++){let F=c[G],$=F.color,te=F.intensity,re=F.distance,Z=null;if(F.shadow&&F.shadow.map&&(F.shadow.map.texture.format===Ci?Z=F.shadow.map.texture:Z=F.shadow.map.depthTexture||F.shadow.map.texture),F.isAmbientLight)h+=$.r*te,f+=$.g*te,u+=$.b*te;else if(F.isLightProbe){for(let Q=0;Q<9;Q++)n.probe[Q].addScaledVector(F.sh.coefficients[Q],te);D++}else if(F.isSunLight){let Q=e.get(F);if(Q.color.copy(F.color).multiplyScalar(F.intensity),F.castShadow){let ce=F.shadow,se=t.get(F);se.shadowIntensity=ce.intensity,se.shadowBias=ce.bias,se.shadowNormalBias=ce.normalBias,se.shadowRadius=ce.radius,se.shadowMapSize.copy(ce.mapSize).multiply(ce.getFrameExtents()),n.sunShadow[g]=se,n.sunShadowMap[g]=Z;let Ge=ce.getViewportCount();for(let Ce=0;Ce<Ge;Ce++)n.sunShadowMatrix[b+Ce]=ce.getMatrix(Ce),n.sunShadowCascade[b+Ce]=ce._cascadeData[Ce];b+=Ge,g++}n.sun[d]=Q,d++}else if(F.isDirectionalLight){let Q=e.get(F);if(Q.color.copy(F.color).multiplyScalar(F.intensity),F.castShadow){let ce=F.shadow,se=t.get(F);se.shadowIntensity=ce.intensity,se.shadowBias=ce.bias,se.shadowNormalBias=ce.normalBias,se.shadowRadius=ce.radius,se.shadowMapSize=ce.mapSize,n.directionalShadow[m]=se,n.directionalShadowMap[m]=Z,n.directionalShadowMatrix[m]=F.shadow.matrix,w++}n.directional[m]=Q,m++}else if(F.isSpotLight){let Q=e.get(F);Q.position.setFromMatrixPosition(F.matrixWorld),Q.color.copy($).multiplyScalar(te),Q.distance=re,Q.coneCos=Math.cos(F.angle),Q.penumbraCos=Math.cos(F.angle*(1-F.penumbra)),Q.decay=F.decay,n.spot[E]=Q;let ce=F.shadow;if(F.map&&(n.spotLightMap[x]=F.map,x++,ce.updateMatrices(F),F.castShadow&&A++),n.spotLightMatrix[E]=ce.matrix,F.castShadow){let se=t.get(F);se.shadowIntensity=ce.intensity,se.shadowBias=ce.bias,se.shadowNormalBias=ce.normalBias,se.shadowRadius=ce.radius,se.shadowMapSize=ce.mapSize,n.spotShadow[E]=se,n.spotShadowMap[E]=Z,I++}E++}else if(F.isRectAreaLight){let Q=e.get(F);Q.color.copy($).multiplyScalar(te),Q.halfWidth.set(F.width*.5,0,0),Q.halfHeight.set(0,F.height*.5,0),n.rectArea[C]=Q,C++}else if(F.isPointLight){let Q=e.get(F);if(Q.color.copy(F.color).multiplyScalar(F.intensity),Q.distance=F.distance,Q.decay=F.decay,F.castShadow){let ce=F.shadow,se=t.get(F);se.shadowIntensity=ce.intensity,se.shadowBias=ce.bias,se.shadowNormalBias=ce.normalBias,se.shadowRadius=ce.radius,se.shadowMapSize=ce.mapSize,se.shadowCameraNear=ce.camera.near,se.shadowCameraFar=ce.camera.far,n.pointShadow[p]=se,n.pointShadowMap[p]=Z,n.pointShadowMatrix[p]=F.shadow.matrix,T++}n.point[p]=Q,p++}else if(F.isHemisphereLight){let Q=e.get(F);Q.skyColor.copy(F.color).multiplyScalar(te),Q.groundColor.copy(F.groundColor).multiplyScalar(te),n.hemi[y]=Q,y++}}C>0&&(i.has("OES_texture_float_linear")===!0?(n.rectAreaLTC1=Le.LTC_FLOAT_1,n.rectAreaLTC2=Le.LTC_FLOAT_2):(n.rectAreaLTC1=Le.LTC_HALF_1,n.rectAreaLTC2=Le.LTC_HALF_2)),n.ambient[0]=h,n.ambient[1]=f,n.ambient[2]=u;let k=n.hash;(k.sunLength!==d||k.directionalLength!==m||k.pointLength!==p||k.spotLength!==E||k.rectAreaLength!==C||k.hemiLength!==y||k.numSunShadows!==g||k.numDirectionalShadows!==w||k.numPointShadows!==T||k.numSpotShadows!==I||k.numSpotMaps!==x||k.numLightProbes!==D)&&(n.sun.length=d,n.directional.length=m,n.spot.length=E,n.rectArea.length=C,n.point.length=p,n.hemi.length=y,n.sunShadow.length=g,n.sunShadowMap.length=g,n.sunShadowMatrix.length=b,n.sunShadowCascade.length=b,n.directionalShadow.length=w,n.directionalShadowMap.length=w,n.directionalShadowMatrix.length=w,n.pointShadow.length=T,n.pointShadowMap.length=T,n.pointShadowMatrix.length=T,n.spotShadow.length=I,n.spotShadowMap.length=I,n.spotLightMatrix.length=I+x-A,n.spotLightMap.length=x,n.numSpotLightShadowsWithMaps=A,n.numLightProbes=D,k.sunLength=d,k.directionalLength=m,k.pointLength=p,k.spotLength=E,k.rectAreaLength=C,k.hemiLength=y,k.numSunShadows=g,k.numDirectionalShadows=w,k.numPointShadows=T,k.numSpotShadows=I,k.numSpotMaps=x,k.numLightProbes=D,n.version=w0++)}function l(c,h){let f=0,u=0,d=0,g=0,b=0,m=0,p=h.matrixWorldInverse;for(let E=0,C=c.length;E<C;E++){let y=c[E];if(y.isSunLight){let w=n.sun[f];w.direction.setFromMatrixPosition(y.matrixWorld),w.direction.transformDirection(p),f++}else if(y.isDirectionalLight){let w=n.directional[u];w.direction.setFromMatrixPosition(y.matrixWorld),s.setFromMatrixPosition(y.target.matrixWorld),w.direction.sub(s),w.direction.transformDirection(p),u++}else if(y.isSpotLight){let w=n.spot[g];w.position.setFromMatrixPosition(y.matrixWorld),w.position.applyMatrix4(p),w.direction.setFromMatrixPosition(y.matrixWorld),s.setFromMatrixPosition(y.target.matrixWorld),w.direction.sub(s),w.direction.transformDirection(p),g++}else if(y.isRectAreaLight){let w=n.rectArea[b];w.position.setFromMatrixPosition(y.matrixWorld),w.position.applyMatrix4(p),a.identity(),r.copy(y.matrixWorld),r.premultiply(p),a.extractRotation(r),w.halfWidth.set(y.width*.5,0,0),w.halfHeight.set(0,y.height*.5,0),w.halfWidth.applyMatrix4(a),w.halfHeight.applyMatrix4(a),b++}else if(y.isPointLight){let w=n.point[d];w.position.setFromMatrixPosition(y.matrixWorld),w.position.applyMatrix4(p),d++}else if(y.isHemisphereLight){let w=n.hemi[m];w.direction.setFromMatrixPosition(y.matrixWorld),w.direction.transformDirection(p),m++}}}return{setup:o,setupView:l,state:n}}function Mh(i){let e=new C0(i),t=[],n=[],s=[];function r(u){f.camera=u,t.length=0,n.length=0,s.length=0}function a(u){t.push(u)}function o(u){n.push(u)}function l(u){s.push(u)}function c(){e.setup(t)}function h(u){e.setupView(t,u)}let f={lightsArray:t,shadowsArray:n,lightProbeGridArray:s,camera:null,lights:e,transmissionRenderTarget:{},textureUnits:0};return{init:r,state:f,setupLights:c,setupLightsView:h,pushLight:a,pushShadow:o,pushLightProbeGrid:l}}function R0(i){let e=new WeakMap;function t(s,r=0){let a=e.get(s),o;return a===void 0?(o=new Mh(i),e.set(s,[o])):r>=a.length?(o=new Mh(i),a.push(o)):o=a[r],o}function n(){e=new WeakMap}return{get:t,dispose:n}}var P0=`void main() {
	gl_Position = vec4( position, 1.0 );
}`,I0=`uniform sampler2D shadow_pass;
uniform vec2 resolution;
uniform float radius;
void main() {
	const float samples = float( VSM_SAMPLES );
	float mean = 0.0;
	float squared_mean = 0.0;
	float uvStride = samples <= 1.0 ? 0.0 : 2.0 / ( samples - 1.0 );
	float uvStart = samples <= 1.0 ? 0.0 : - 1.0;
	for ( float i = 0.0; i < samples; i ++ ) {
		float uvOffset = uvStart + i * uvStride;
		#ifdef HORIZONTAL_PASS
			vec2 distribution = texture2D( shadow_pass, ( gl_FragCoord.xy + vec2( uvOffset, 0.0 ) * radius ) / resolution ).rg;
			mean += distribution.x;
			squared_mean += distribution.y * distribution.y + distribution.x * distribution.x;
		#else
			float depth = texture2D( shadow_pass, ( gl_FragCoord.xy + vec2( 0.0, uvOffset ) * radius ) / resolution ).r;
			mean += depth;
			squared_mean += depth * depth;
		#endif
	}
	mean = mean / samples;
	squared_mean = squared_mean / samples;
	float std_dev = sqrt( max( 0.0, squared_mean - mean * mean ) );
	gl_FragColor = vec4( mean, std_dev, 0.0, 1.0 );
}`,L0=[new U(1,0,0),new U(-1,0,0),new U(0,1,0),new U(0,-1,0),new U(0,0,1),new U(0,0,-1)],N0=[new U(0,-1,0),new U(0,-1,0),new U(0,0,1),new U(0,0,-1),new U(0,-1,0),new U(0,-1,0)],Sh=new xt,Xr=new U,Mc=new U;function D0(i,e,t){let n=new bs,s=new De,r=new De,a=new Ut,o=new ja,l=new Ja,c={},h=t.maxTextureSize,f={[Ti]:en,[en]:Ti,[Jn]:Jn},u=new kt({defines:{VSM_SAMPLES:8},uniforms:{shadow_pass:{value:null},resolution:{value:new De},radius:{value:4}},vertexShader:P0,fragmentShader:I0}),d=u.clone();d.defines.HORIZONTAL_PASS=1;let g=new Rt;g.setAttribute("position",new Kt(new Float32Array([-1,-1,.5,3,-1,.5,-1,3,.5]),3));let b=new bt(g,u),m=this;this.enabled=!1,this.autoUpdate=!0,this.needsUpdate=!1,this.type=Rr;let p=this.type;this.render=function(T,I,x){if(m.enabled===!1||m.autoUpdate===!1&&m.needsUpdate===!1||T.length===0)return;this.type===xu&&(je("WebGLShadowMap: PCFSoftShadowMap has been removed. Using PCFShadowMap instead."),this.type=Rr);let A=i.getRenderTarget(),D=i.getActiveCubeFace(),k=i.getActiveMipmapLevel(),G=i.state;G.setBlending(Rn),G.buffers.depth.getReversed()===!0?G.buffers.color.setClear(0,0,0,0):G.buffers.color.setClear(1,1,1,1),G.buffers.depth.setTest(!0),G.setScissorTest(!1);let Y=p!==this.type;Y&&I.traverse(function(F){F.material&&(Array.isArray(F.material)?F.material.forEach($=>$.needsUpdate=!0):F.material.needsUpdate=!0)});for(let F=0,$=T.length;F<$;F++){let te=T[F],re=te.shadow;if(re===void 0){je("WebGLShadowMap:",te,"has no shadow.");continue}if(re.autoUpdate===!1&&re.needsUpdate===!1)continue;s.copy(re.mapSize);let Z=re.getFrameExtents();s.multiply(Z),r.copy(re.mapSize),(s.x>h||s.y>h)&&(s.x>h&&(r.x=Math.floor(h/Z.x),s.x=r.x*Z.x,re.mapSize.x=r.x),s.y>h&&(r.y=Math.floor(h/Z.y),s.y=r.y*Z.y,re.mapSize.y=r.y));let Q=i.state.buffers.depth.getReversed();if(re.camera._reversedDepth=Q,re.map===null||Y===!0){if(re.map!==null&&(re.map.depthTexture!==null&&(re.map.depthTexture.dispose(),re.map.depthTexture=null),re.map.dispose()),this.type===Cs){if(te.isPointLight){je("WebGLShadowMap: VSM shadow maps are not supported for PointLights. Use PCF or BasicShadowMap instead.");continue}re.map=new Vt(s.x,s.y,{format:Ci,type:tn,minFilter:Qt,magFilter:Qt,generateMipmaps:!1}),re.map.texture.name=te.name+".shadowMap",re.map.depthTexture=new vi(s.x,s.y,Pn),re.map.depthTexture.name=te.name+".shadowMapDepth",re.map.depthTexture.format=Xn,re.map.depthTexture.compareFunction=null,re.map.depthTexture.minFilter=Yt,re.map.depthTexture.magFilter=Yt}else te.isPointLight?(re.map=new il(s.x),re.map.depthTexture=new Ha(s.x,Vn)):(re.map=new Vt(s.x,s.y),re.map.depthTexture=new vi(s.x,s.y,Vn)),re.map.depthTexture.name=te.name+".shadowMap",re.map.depthTexture.format=Xn,this.type===Rr?(re.map.depthTexture.compareFunction=Q?Qo:Ko,re.map.depthTexture.minFilter=Qt,re.map.depthTexture.magFilter=Qt):(re.map.depthTexture.compareFunction=null,re.map.depthTexture.minFilter=Yt,re.map.depthTexture.magFilter=Yt);re.camera.updateProjectionMatrix()}re.map.isWebGLCubeRenderTarget!==!0&&(re.map.width!==s.x||re.map.height!==s.y)&&re.map.setSize(s.x,s.y);let ce=re.map.isWebGLCubeRenderTarget?6:re.getViewportCount();te.isPointLight!==!0&&re.updateMatrices(te,x);for(let se=0;se<ce;se++){let Ge=re.getCamera(se);if(te.isPointLight){let Ce=re.camera,ut=re.matrix,Ze=te.distance||Ce.far;Ze!==Ce.far&&(Ce.far=Ze,Ce.updateProjectionMatrix()),Xr.setFromMatrixPosition(te.matrixWorld),Ce.position.copy(Xr),Mc.copy(Ce.position),Mc.add(L0[se]),Ce.up.copy(N0[se]),Ce.lookAt(Mc),Ce.updateMatrixWorld(),ut.makeTranslation(-Xr.x,-Xr.y,-Xr.z),Sh.multiplyMatrices(Ce.projectionMatrix,Ce.matrixWorldInverse),re._frustum.setFromProjectionMatrix(Sh,Ce.coordinateSystem,Ce.reversedDepth)}if(re.map.isWebGLCubeRenderTarget)i.setRenderTarget(re.map,se),i.clear();else{se===0&&(i.setRenderTarget(re.map),i.clear());let Ce=re.getViewport(se);a.set(r.x*Ce.x,r.y*Ce.y,r.x*Ce.z,r.y*Ce.w),G.viewport(a)}n=re.getFrustum(se),y(I,x,Ge,te,this.type)}re.isPointLightShadow!==!0&&this.type===Cs&&E(re,x),re.needsUpdate=!1}p=this.type,m.needsUpdate=!1,i.setRenderTarget(A,D,k)};function E(T,I){let x=e.update(b);u.defines.VSM_SAMPLES!==T.blurSamples&&(u.defines.VSM_SAMPLES=T.blurSamples,d.defines.VSM_SAMPLES=T.blurSamples,u.needsUpdate=!0,d.needsUpdate=!0),T.mapPass===null?T.mapPass=new Vt(s.x,s.y,{format:Ci,type:tn}):(T.mapPass.width!==T.map.width||T.mapPass.height!==T.map.height)&&T.mapPass.setSize(T.map.width,T.map.height),u.uniforms.shadow_pass.value=T.map.depthTexture,u.uniforms.resolution.value.set(T.map.width,T.map.height),u.uniforms.radius.value=T.radius,i.setRenderTarget(T.mapPass),i.clear(),i.renderBufferDirect(I,null,x,u,b,null),d.uniforms.shadow_pass.value=T.mapPass.texture,d.uniforms.resolution.value.set(T.map.width,T.map.height),d.uniforms.radius.value=T.radius,i.setRenderTarget(T.map),i.clear(),i.renderBufferDirect(I,null,x,d,b,null)}function C(T,I,x,A){let D=null,k=x.isPointLight===!0?T.customDistanceMaterial:T.customDepthMaterial;if(k!==void 0)D=k;else if(D=x.isPointLight===!0?l:o,i.localClippingEnabled&&I.clipShadows===!0&&Array.isArray(I.clippingPlanes)&&I.clippingPlanes.length!==0||I.displacementMap&&I.displacementScale!==0||I.alphaMap&&I.alphaTest>0||I.map&&I.alphaTest>0||I.alphaToCoverage===!0){let G=D.uuid,Y=I.uuid,F=c[G];F===void 0&&(F={},c[G]=F);let $=F[Y];$===void 0&&($=D.clone(),F[Y]=$,I.addEventListener("dispose",w)),D=$}if(D.visible=I.visible,D.wireframe=I.wireframe,A===Cs?D.side=I.shadowSide!==null?I.shadowSide:I.side:D.side=I.shadowSide!==null?I.shadowSide:f[I.side],D.alphaMap=I.alphaMap,D.alphaTest=I.alphaToCoverage===!0?.5:I.alphaTest,D.map=I.map,D.clipShadows=I.clipShadows,D.clippingPlanes=I.clippingPlanes,D.clipIntersection=I.clipIntersection,D.displacementMap=I.displacementMap,D.displacementScale=I.displacementScale,D.displacementBias=I.displacementBias,D.wireframeLinewidth=I.wireframeLinewidth,D.linewidth=I.linewidth,x.isPointLight===!0&&D.isMeshDistanceMaterial===!0){let G=i.properties.get(D);G.light=x}return D}function y(T,I,x,A,D){if(T.visible===!1)return;if(T.layers.test(I.layers)&&(T.isMesh||T.isLine||T.isPoints)&&(T.castShadow||T.receiveShadow&&D===Cs)&&(!T.frustumCulled||T.intersectsFrustum(n))){T.modelViewMatrix.multiplyMatrices(x.matrixWorldInverse,T.matrixWorld);let Y=e.update(T),F=T.material;if(Array.isArray(F)){let $=Y.groups;for(let te=0,re=$.length;te<re;te++){let Z=$[te],Q=F[Z.materialIndex];if(Q&&Q.visible){let ce=C(T,Q,A,D);T.onBeforeShadow(i,T,I,x,Y,ce,Z),i.renderBufferDirect(x,null,Y,ce,T,Z),T.onAfterShadow(i,T,I,x,Y,ce,Z)}}}else if(F.visible){let $=C(T,F,A,D);T.onBeforeShadow(i,T,I,x,Y,$,null),i.renderBufferDirect(x,null,Y,$,T,null),T.onAfterShadow(i,T,I,x,Y,$,null)}}let G=T.children;for(let Y=0,F=G.length;Y<F;Y++)y(G[Y],I,x,A,D)}function w(T){T.target.removeEventListener("dispose",w);for(let x in c){let A=c[x],D=T.target.uuid;D in A&&(A[D].dispose(),delete A[D])}}}function U0(i,e){function t(){let O=!1,Me=new Ut,J=null,ve=new Ut(0,0,0,0);return{setMask:function(we){J!==we&&!O&&(i.colorMask(we,we,we,we),J=we)},setLocked:function(we){O=we},setClear:function(we,fe,We,Ve,Ct){Ct===!0&&(we*=Ve,fe*=Ve,We*=Ve),Me.set(we,fe,We,Ve),ve.equals(Me)===!1&&(i.clearColor(we,fe,We,Ve),ve.copy(Me))},reset:function(){O=!1,J=null,ve.set(-1,0,0,0)}}}function n(){let O=!1,Me=!1,J=null,ve=null,we=null;return{setReversed:function(fe){if(Me!==fe){let We=e.get("EXT_clip_control");fe?We.clipControlEXT(We.LOWER_LEFT_EXT,We.ZERO_TO_ONE_EXT):We.clipControlEXT(We.LOWER_LEFT_EXT,We.NEGATIVE_ONE_TO_ONE_EXT),Me=fe;let Ve=we;we=null,this.setClear(Ve)}},getReversed:function(){return Me},setTest:function(fe){fe?ne(i.DEPTH_TEST):xe(i.DEPTH_TEST)},setMask:function(fe){J!==fe&&!O&&(i.depthMask(fe),J=fe)},setFunc:function(fe){if(Me&&(fe=Qu[fe]),ve!==fe){switch(fe){case Aa:i.depthFunc(i.NEVER);break;case Ca:i.depthFunc(i.ALWAYS);break;case Ra:i.depthFunc(i.LESS);break;case ps:i.depthFunc(i.LEQUAL);break;case Pa:i.depthFunc(i.EQUAL);break;case Ia:i.depthFunc(i.GEQUAL);break;case La:i.depthFunc(i.GREATER);break;case Na:i.depthFunc(i.NOTEQUAL);break;default:i.depthFunc(i.LEQUAL)}ve=fe}},setLocked:function(fe){O=fe},setClear:function(fe){we!==fe&&(we=fe,Me&&(fe=1-fe),i.clearDepth(fe))},reset:function(){O=!1,J=null,ve=null,we=null,Me=!1}}}function s(){let O=!1,Me=null,J=null,ve=null,we=null,fe=null,We=null,Ve=null,Ct=null;return{setTest:function(Mt){O||(Mt?ne(i.STENCIL_TEST):xe(i.STENCIL_TEST))},setMask:function(Mt){Me!==Mt&&!O&&(i.stencilMask(Mt),Me=Mt)},setFunc:function(Mt,nn,sn){(J!==Mt||ve!==nn||we!==sn)&&(i.stencilFunc(Mt,nn,sn),J=Mt,ve=nn,we=sn)},setOp:function(Mt,nn,sn){(fe!==Mt||We!==nn||Ve!==sn)&&(i.stencilOp(Mt,nn,sn),fe=Mt,We=nn,Ve=sn)},setLocked:function(Mt){O=Mt},setClear:function(Mt){Ct!==Mt&&(i.clearStencil(Mt),Ct=Mt)},reset:function(){O=!1,Me=null,J=null,ve=null,we=null,fe=null,We=null,Ve=null,Ct=null}}}let r=new t,a=new n,o=new s,l=new WeakMap,c=new WeakMap,h={},f={},u={},d=new WeakMap,g=[],b=null,m=!1,p=null,E=null,C=null,y=null,w=null,T=null,I=null,x=new Qe(0,0,0),A=0,D=!1,k=null,G=null,Y=null,F=null,$=null,te=i.getParameter(i.MAX_COMBINED_TEXTURE_IMAGE_UNITS),re=!1,Z=0,Q=i.getParameter(i.VERSION);Q.indexOf("WebGL")!==-1?(Z=parseFloat(/^WebGL (\d)/.exec(Q)[1]),re=Z>=1):Q.indexOf("OpenGL ES")!==-1&&(Z=parseFloat(/^OpenGL ES (\d)/.exec(Q)[1]),re=Z>=2);let ce=null,se={},Ge=i.getParameter(i.SCISSOR_BOX),Ce=i.getParameter(i.VIEWPORT),ut=new Ut().fromArray(Ge),Ze=new Ut().fromArray(Ce);function Xe(O,Me,J,ve){let we=new Uint8Array(4),fe=i.createTexture();i.bindTexture(O,fe),i.texParameteri(O,i.TEXTURE_MIN_FILTER,i.NEAREST),i.texParameteri(O,i.TEXTURE_MAG_FILTER,i.NEAREST);for(let We=0;We<J;We++)O===i.TEXTURE_3D||O===i.TEXTURE_2D_ARRAY?i.texImage3D(Me,0,i.RGBA,1,1,ve,0,i.RGBA,i.UNSIGNED_BYTE,we):i.texImage2D(Me+We,0,i.RGBA,1,1,0,i.RGBA,i.UNSIGNED_BYTE,we);return fe}let ee={};ee[i.TEXTURE_2D]=Xe(i.TEXTURE_2D,i.TEXTURE_2D,1),ee[i.TEXTURE_CUBE_MAP]=Xe(i.TEXTURE_CUBE_MAP,i.TEXTURE_CUBE_MAP_POSITIVE_X,6),ee[i.TEXTURE_2D_ARRAY]=Xe(i.TEXTURE_2D_ARRAY,i.TEXTURE_2D_ARRAY,1,1),ee[i.TEXTURE_3D]=Xe(i.TEXTURE_3D,i.TEXTURE_3D,1,1),r.setClear(0,0,0,1),a.setClear(1),o.setClear(0),ne(i.DEPTH_TEST),a.setFunc(ps),rt(!1),at(jl),ne(i.CULL_FACE),ot(Rn);function ne(O){h[O]!==!0&&(i.enable(O),h[O]=!0)}function xe(O){h[O]!==!1&&(i.disable(O),h[O]=!1)}function Pe(O,Me){return u[O]!==Me?(i.bindFramebuffer(O,Me),u[O]=Me,O===i.DRAW_FRAMEBUFFER&&(u[i.FRAMEBUFFER]=Me),O===i.FRAMEBUFFER&&(u[i.DRAW_FRAMEBUFFER]=Me),!0):!1}function Re(O,Me){let J=g,ve=!1;if(O){J=d.get(Me),J===void 0&&(J=[],d.set(Me,J));let we=O.textures;if(J.length!==we.length||J[0]!==i.COLOR_ATTACHMENT0){for(let fe=0,We=we.length;fe<We;fe++)J[fe]=i.COLOR_ATTACHMENT0+fe;J.length=we.length,ve=!0}}else J[0]!==i.BACK&&(J[0]=i.BACK,ve=!0);ve&&i.drawBuffers(J)}function Je(O){return b!==O?(i.useProgram(O),b=O,!0):!1}let dt={[Wi]:i.FUNC_ADD,[yu]:i.FUNC_SUBTRACT,[bu]:i.FUNC_REVERSE_SUBTRACT};dt[Mu]=i.MIN,dt[Su]=i.MAX;let it={[Tu]:i.ZERO,[Eu]:i.ONE,[wu]:i.SRC_COLOR,[Ql]:i.SRC_ALPHA,[Lu]:i.SRC_ALPHA_SATURATE,[Pu]:i.DST_COLOR,[Cu]:i.DST_ALPHA,[Au]:i.ONE_MINUS_SRC_COLOR,[ec]:i.ONE_MINUS_SRC_ALPHA,[Iu]:i.ONE_MINUS_DST_COLOR,[Ru]:i.ONE_MINUS_DST_ALPHA,[Nu]:i.CONSTANT_COLOR,[Du]:i.ONE_MINUS_CONSTANT_COLOR,[Uu]:i.CONSTANT_ALPHA,[Fu]:i.ONE_MINUS_CONSTANT_ALPHA};function ot(O,Me,J,ve,we,fe,We,Ve,Ct,Mt){if(O===Rn){m===!0&&(xe(i.BLEND),m=!1);return}if(m===!1&&(ne(i.BLEND),m=!0),O!==vu){if(O!==p||Mt!==D){if((E!==Wi||w!==Wi)&&(i.blendEquation(i.FUNC_ADD),E=Wi,w=Wi),Mt)switch(O){case Rs:i.blendFuncSeparate(i.ONE,i.ONE_MINUS_SRC_ALPHA,i.ONE,i.ONE_MINUS_SRC_ALPHA);break;case Gi:i.blendFunc(i.ONE,i.ONE);break;case Jl:i.blendFuncSeparate(i.ZERO,i.ONE_MINUS_SRC_COLOR,i.ZERO,i.ONE);break;case Kl:i.blendFuncSeparate(i.DST_COLOR,i.ONE_MINUS_SRC_ALPHA,i.ZERO,i.ONE);break;default:nt("WebGLState: Invalid blending: ",O);break}else switch(O){case Rs:i.blendFuncSeparate(i.SRC_ALPHA,i.ONE_MINUS_SRC_ALPHA,i.ONE,i.ONE_MINUS_SRC_ALPHA);break;case Gi:i.blendFuncSeparate(i.SRC_ALPHA,i.ONE,i.ONE,i.ONE);break;case Jl:nt("WebGLState: SubtractiveBlending requires material.premultipliedAlpha = true");break;case Kl:nt("WebGLState: MultiplyBlending requires material.premultipliedAlpha = true");break;default:nt("WebGLState: Invalid blending: ",O);break}C=null,y=null,T=null,I=null,x.set(0,0,0),A=0,p=O,D=Mt}return}we=we||Me,fe=fe||J,We=We||ve,(Me!==E||we!==w)&&(i.blendEquationSeparate(dt[Me],dt[we]),E=Me,w=we),(J!==C||ve!==y||fe!==T||We!==I)&&(i.blendFuncSeparate(it[J],it[ve],it[fe],it[We]),C=J,y=ve,T=fe,I=We),(Ve.equals(x)===!1||Ct!==A)&&(i.blendColor(Ve.r,Ve.g,Ve.b,Ct),x.copy(Ve),A=Ct),p=O,D=!1}function gt(O,Me){O.side===Jn?xe(i.CULL_FACE):ne(i.CULL_FACE);let J=O.side===en;Me&&(J=!J),rt(J),O.blending===Rs&&O.transparent===!1?ot(Rn):ot(O.blending,O.blendEquation,O.blendSrc,O.blendDst,O.blendEquationAlpha,O.blendSrcAlpha,O.blendDstAlpha,O.blendColor,O.blendAlpha,O.premultipliedAlpha),a.setFunc(O.depthFunc),a.setTest(O.depthTest),a.setMask(O.depthWrite),r.setMask(O.colorWrite);let ve=O.stencilWrite;o.setTest(ve),ve&&(o.setMask(O.stencilWriteMask),o.setFunc(O.stencilFunc,O.stencilRef,O.stencilFuncMask),o.setOp(O.stencilFail,O.stencilZFail,O.stencilZPass)),Lt(O.polygonOffset,O.polygonOffsetFactor,O.polygonOffsetUnits),O.alphaToCoverage===!0?ne(i.SAMPLE_ALPHA_TO_COVERAGE):xe(i.SAMPLE_ALPHA_TO_COVERAGE)}function rt(O){k!==O&&(O?i.frontFace(i.CW):i.frontFace(i.CCW),k=O)}function at(O){O!==gu?(ne(i.CULL_FACE),O!==G&&(O===jl?i.cullFace(i.BACK):O===_u?i.cullFace(i.FRONT):i.cullFace(i.FRONT_AND_BACK))):xe(i.CULL_FACE),G=O}function Dt(O){O!==Y&&(re&&i.lineWidth(O),Y=O)}function Lt(O,Me,J){O?(ne(i.POLYGON_OFFSET_FILL),(F!==Me||$!==J)&&(F=Me,$=J,a.getReversed()&&(Me=-Me),i.polygonOffset(Me,J))):xe(i.POLYGON_OFFSET_FILL)}function _t(O){O?ne(i.SCISSOR_TEST):xe(i.SCISSOR_TEST)}function Tt(O){O===void 0&&(O=i.TEXTURE0+te-1),ce!==O&&(i.activeTexture(O),ce=O)}function z(O,Me,J){J===void 0&&(ce===null?J=i.TEXTURE0+te-1:J=ce);let ve=se[J];ve===void 0&&(ve={type:void 0,texture:void 0},se[J]=ve),(ve.type!==O||ve.texture!==Me)&&(ce!==J&&(i.activeTexture(J),ce=J),i.bindTexture(O,Me||ee[O]),ve.type=O,ve.texture=Me)}function Et(){let O=se[ce];O!==void 0&&O.type!==void 0&&(i.bindTexture(O.type,null),O.type=void 0,O.texture=void 0)}function lt(){try{i.compressedTexImage2D(...arguments)}catch(O){nt("WebGLState:",O)}}function P(){try{i.compressedTexImage3D(...arguments)}catch(O){nt("WebGLState:",O)}}function _(){try{i.texSubImage2D(...arguments)}catch(O){nt("WebGLState:",O)}}function X(){try{i.texSubImage3D(...arguments)}catch(O){nt("WebGLState:",O)}}function K(){try{i.compressedTexSubImage2D(...arguments)}catch(O){nt("WebGLState:",O)}}function ae(){try{i.compressedTexSubImage3D(...arguments)}catch(O){nt("WebGLState:",O)}}function be(){try{i.texStorage2D(...arguments)}catch(O){nt("WebGLState:",O)}}function Ee(){try{i.texStorage3D(...arguments)}catch(O){nt("WebGLState:",O)}}function N(){try{i.texImage2D(...arguments)}catch(O){nt("WebGLState:",O)}}function V(){try{i.texImage3D(...arguments)}catch(O){nt("WebGLState:",O)}}function ie(O){return f[O]!==void 0?f[O]:i.getParameter(O)}function ge(O,Me){f[O]!==Me&&(i.pixelStorei(O,Me),f[O]=Me)}function ue(O){ut.equals(O)===!1&&(i.scissor(O.x,O.y,O.z,O.w),ut.copy(O))}function pe(O){Ze.equals(O)===!1&&(i.viewport(O.x,O.y,O.z,O.w),Ze.copy(O))}function _e(O,Me){let J=c.get(Me);J===void 0&&(J=new WeakMap,c.set(Me,J));let ve=J.get(O);ve===void 0&&(ve=i.getUniformBlockIndex(Me,O.name),J.set(O,ve))}function Se(O,Me){let ve=c.get(Me).get(O);l.get(Me)!==ve&&(i.uniformBlockBinding(Me,ve,O.__bindingPointIndex),l.set(Me,ve))}function Be(){i.disable(i.BLEND),i.disable(i.CULL_FACE),i.disable(i.DEPTH_TEST),i.disable(i.POLYGON_OFFSET_FILL),i.disable(i.SCISSOR_TEST),i.disable(i.STENCIL_TEST),i.disable(i.SAMPLE_ALPHA_TO_COVERAGE),i.blendEquation(i.FUNC_ADD),i.blendFunc(i.ONE,i.ZERO),i.blendFuncSeparate(i.ONE,i.ZERO,i.ONE,i.ZERO),i.blendColor(0,0,0,0),i.colorMask(!0,!0,!0,!0),i.clearColor(0,0,0,0),i.depthMask(!0),i.depthFunc(i.LESS),a.setReversed(!1),i.clearDepth(1),i.stencilMask(4294967295),i.stencilFunc(i.ALWAYS,0,4294967295),i.stencilOp(i.KEEP,i.KEEP,i.KEEP),i.clearStencil(0),i.cullFace(i.BACK),i.frontFace(i.CCW),i.polygonOffset(0,0),i.activeTexture(i.TEXTURE0),i.bindFramebuffer(i.FRAMEBUFFER,null),i.bindFramebuffer(i.DRAW_FRAMEBUFFER,null),i.bindFramebuffer(i.READ_FRAMEBUFFER,null),i.useProgram(null),i.lineWidth(1),i.scissor(0,0,i.canvas.width,i.canvas.height),i.viewport(0,0,i.canvas.width,i.canvas.height),i.pixelStorei(i.PACK_ALIGNMENT,4),i.pixelStorei(i.UNPACK_ALIGNMENT,4),i.pixelStorei(i.UNPACK_FLIP_Y_WEBGL,!1),i.pixelStorei(i.UNPACK_PREMULTIPLY_ALPHA_WEBGL,!1),i.pixelStorei(i.UNPACK_COLORSPACE_CONVERSION_WEBGL,i.BROWSER_DEFAULT_WEBGL),i.pixelStorei(i.PACK_ROW_LENGTH,0),i.pixelStorei(i.PACK_SKIP_PIXELS,0),i.pixelStorei(i.PACK_SKIP_ROWS,0),i.pixelStorei(i.UNPACK_ROW_LENGTH,0),i.pixelStorei(i.UNPACK_IMAGE_HEIGHT,0),i.pixelStorei(i.UNPACK_SKIP_PIXELS,0),i.pixelStorei(i.UNPACK_SKIP_ROWS,0),i.pixelStorei(i.UNPACK_SKIP_IMAGES,0),h={},f={},ce=null,se={},u={},d=new WeakMap,g=[],b=null,m=!1,p=null,E=null,C=null,y=null,w=null,T=null,I=null,x=new Qe(0,0,0),A=0,D=!1,k=null,G=null,Y=null,F=null,$=null,ut.set(0,0,i.canvas.width,i.canvas.height),Ze.set(0,0,i.canvas.width,i.canvas.height),r.reset(),a.reset(),o.reset()}return{buffers:{color:r,depth:a,stencil:o},enable:ne,disable:xe,bindFramebuffer:Pe,drawBuffers:Re,useProgram:Je,setBlending:ot,setMaterial:gt,setFlipSided:rt,setCullFace:at,setLineWidth:Dt,setPolygonOffset:Lt,setScissorTest:_t,activeTexture:Tt,bindTexture:z,unbindTexture:Et,compressedTexImage2D:lt,compressedTexImage3D:P,texImage2D:N,texImage3D:V,pixelStorei:ge,getParameter:ie,updateUBOMapping:_e,uniformBlockBinding:Se,texStorage2D:be,texStorage3D:Ee,texSubImage2D:_,texSubImage3D:X,compressedTexSubImage2D:K,compressedTexSubImage3D:ae,scissor:ue,viewport:pe,reset:Be}}function F0(i,e,t,n,s,r,a){let o=e.has("WEBGL_multisampled_render_to_texture")?e.get("WEBGL_multisampled_render_to_texture"):null,l=typeof navigator>"u"?!1:/OculusBrowser/g.test(navigator.userAgent),c=new De,h=new WeakMap,f=new Set,u,d=new WeakMap,g=!1;try{g=typeof OffscreenCanvas<"u"&&new OffscreenCanvas(1,1).getContext("2d")!==null}catch{}function b(P,_){return g?new OffscreenCanvas(P,_):rr("canvas")}function m(P,_,X){let K=1,ae=lt(P);if((ae.width>X||ae.height>X)&&(K=X/Math.max(ae.width,ae.height)),K<1)if(typeof HTMLImageElement<"u"&&P instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&P instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&P instanceof ImageBitmap||typeof VideoFrame<"u"&&P instanceof VideoFrame){let be=Math.floor(K*ae.width),Ee=Math.floor(K*ae.height);u===void 0&&(u=b(be,Ee));let N=_?b(be,Ee):u;return N.width=be,N.height=Ee,N.getContext("2d").drawImage(P,0,0,be,Ee),je("WebGLRenderer: Texture has been resized from ("+ae.width+"x"+ae.height+") to ("+be+"x"+Ee+")."),N}else return"data"in P&&je("WebGLRenderer: Image in DataTexture is too big ("+ae.width+"x"+ae.height+")."),P;return P}function p(P){return P.generateMipmaps}function E(P){i.generateMipmap(P)}function C(P){return P.isWebGLCubeRenderTarget?i.TEXTURE_CUBE_MAP:P.isWebGL3DRenderTarget?i.TEXTURE_3D:P.isWebGLArrayRenderTarget||P.isCompressedArrayTexture?i.TEXTURE_2D_ARRAY:i.TEXTURE_2D}function y(P,_,X,K,ae,be=!1){if(P!==null){if(i[P]!==void 0)return i[P];je("WebGLRenderer: Attempt to use non-existing WebGL internal format '"+P+"'")}let Ee;K&&(Ee=e.get("EXT_texture_norm16"),Ee||je("WebGLRenderer: Unable to use normalized textures without EXT_texture_norm16 extension"));let N=_;if(_===i.RED&&(X===i.FLOAT&&(N=i.R32F),X===i.HALF_FLOAT&&(N=i.R16F),X===i.UNSIGNED_BYTE&&(N=i.R8),X===i.UNSIGNED_SHORT&&Ee&&(N=Ee.R16_EXT),X===i.SHORT&&Ee&&(N=Ee.R16_SNORM_EXT)),_===i.RED_INTEGER&&(X===i.UNSIGNED_BYTE&&(N=i.R8UI),X===i.UNSIGNED_SHORT&&(N=i.R16UI),X===i.UNSIGNED_INT&&(N=i.R32UI),X===i.BYTE&&(N=i.R8I),X===i.SHORT&&(N=i.R16I),X===i.INT&&(N=i.R32I)),_===i.RG&&(X===i.FLOAT&&(N=i.RG32F),X===i.HALF_FLOAT&&(N=i.RG16F),X===i.UNSIGNED_BYTE&&(N=i.RG8),X===i.UNSIGNED_SHORT&&Ee&&(N=Ee.RG16_EXT),X===i.SHORT&&Ee&&(N=Ee.RG16_SNORM_EXT)),_===i.RG_INTEGER&&(X===i.UNSIGNED_BYTE&&(N=i.RG8UI),X===i.UNSIGNED_SHORT&&(N=i.RG16UI),X===i.UNSIGNED_INT&&(N=i.RG32UI),X===i.BYTE&&(N=i.RG8I),X===i.SHORT&&(N=i.RG16I),X===i.INT&&(N=i.RG32I)),_===i.RGB_INTEGER&&(X===i.UNSIGNED_BYTE&&(N=i.RGB8UI),X===i.UNSIGNED_SHORT&&(N=i.RGB16UI),X===i.UNSIGNED_INT&&(N=i.RGB32UI),X===i.BYTE&&(N=i.RGB8I),X===i.SHORT&&(N=i.RGB16I),X===i.INT&&(N=i.RGB32I)),_===i.RGBA_INTEGER&&(X===i.UNSIGNED_BYTE&&(N=i.RGBA8UI),X===i.UNSIGNED_SHORT&&(N=i.RGBA16UI),X===i.UNSIGNED_INT&&(N=i.RGBA32UI),X===i.BYTE&&(N=i.RGBA8I),X===i.SHORT&&(N=i.RGBA16I),X===i.INT&&(N=i.RGBA32I)),_===i.RGB&&(X===i.UNSIGNED_SHORT&&Ee&&(N=Ee.RGB16_EXT),X===i.SHORT&&Ee&&(N=Ee.RGB16_SNORM_EXT),X===i.UNSIGNED_INT_5_9_9_9_REV&&(N=i.RGB9_E5),X===i.UNSIGNED_INT_10F_11F_11F_REV&&(N=i.R11F_G11F_B10F)),_===i.RGBA){let V=be?sr:pt.getTransfer(ae);X===i.FLOAT&&(N=i.RGBA32F),X===i.HALF_FLOAT&&(N=i.RGBA16F),X===i.UNSIGNED_BYTE&&(N=V===St?i.SRGB8_ALPHA8:i.RGBA8),X===i.UNSIGNED_SHORT&&Ee&&(N=Ee.RGBA16_EXT),X===i.SHORT&&Ee&&(N=Ee.RGBA16_SNORM_EXT),X===i.UNSIGNED_SHORT_4_4_4_4&&(N=i.RGBA4),X===i.UNSIGNED_SHORT_5_5_5_1&&(N=i.RGB5_A1)}return(N===i.R16F||N===i.R32F||N===i.RG16F||N===i.RG32F||N===i.RGBA16F||N===i.RGBA32F)&&e.get("EXT_color_buffer_float"),N}function w(P,_){let X;return P?_===null||_===Vn||_===Is?X=i.DEPTH24_STENCIL8:_===Pn?X=i.DEPTH32F_STENCIL8:_===Ps&&(X=i.DEPTH24_STENCIL8,je("DepthTexture: 16 bit depth attachment is not supported with stencil. Using 24-bit attachment.")):_===null||_===Vn||_===Is?X=i.DEPTH_COMPONENT24:_===Pn?X=i.DEPTH_COMPONENT32F:_===Ps&&(X=i.DEPTH_COMPONENT16),X}function T(P,_){return p(P)===!0||P.isFramebufferTexture&&P.minFilter!==Yt&&P.minFilter!==Qt?Math.log2(Math.max(_.width,_.height))+1:P.mipmaps!==void 0&&P.mipmaps.length>0?P.mipmaps.length:P.isCompressedTexture&&Array.isArray(P.image)?_.mipmaps.length:1}function I(P){let _=P.target;_.removeEventListener("dispose",I),A(_),_.isVideoTexture&&h.delete(_),_.isHTMLTexture&&f.delete(_)}function x(P){let _=P.target;_.removeEventListener("dispose",x),k(_)}function A(P){let _=n.get(P);if(_.__webglInit===void 0)return;let X=P.source,K=d.get(X);if(K){let ae=K[_.__cacheKey];ae.usedTimes--,ae.usedTimes===0&&D(P),Object.keys(K).length===0&&d.delete(X)}n.remove(P)}function D(P){let _=n.get(P);i.deleteTexture(_.__webglTexture);let X=P.source,K=d.get(X);delete K[_.__cacheKey],a.memory.textures--}function k(P){let _=n.get(P);if(P.depthTexture&&(P.depthTexture.dispose(),n.remove(P.depthTexture)),P.isWebGLCubeRenderTarget)for(let K=0;K<6;K++){if(Array.isArray(_.__webglFramebuffer[K]))for(let ae=0;ae<_.__webglFramebuffer[K].length;ae++)i.deleteFramebuffer(_.__webglFramebuffer[K][ae]);else i.deleteFramebuffer(_.__webglFramebuffer[K]);_.__webglDepthbuffer&&i.deleteRenderbuffer(_.__webglDepthbuffer[K])}else{if(Array.isArray(_.__webglFramebuffer))for(let K=0;K<_.__webglFramebuffer.length;K++)i.deleteFramebuffer(_.__webglFramebuffer[K]);else i.deleteFramebuffer(_.__webglFramebuffer);if(_.__webglDepthbuffer&&i.deleteRenderbuffer(_.__webglDepthbuffer),_.__webglMultisampledFramebuffer&&i.deleteFramebuffer(_.__webglMultisampledFramebuffer),_.__webglColorRenderbuffer)for(let K=0;K<_.__webglColorRenderbuffer.length;K++)_.__webglColorRenderbuffer[K]&&i.deleteRenderbuffer(_.__webglColorRenderbuffer[K]);_.__webglDepthRenderbuffer&&i.deleteRenderbuffer(_.__webglDepthRenderbuffer)}let X=P.textures;for(let K=0,ae=X.length;K<ae;K++){let be=n.get(X[K]);be.__webglTexture&&(i.deleteTexture(be.__webglTexture),a.memory.textures--),n.remove(X[K])}n.remove(P)}let G=0;function Y(){G=0}function F(){return G}function $(P){G=P}function te(){let P=G;return P>=s.maxTextures&&je("WebGLTextures: Trying to use "+(P+1)+" texture units while this GPU supports only "+s.maxTextures),G+=1,P}function re(P){let _=[];return _.push(P.wrapS),_.push(P.wrapT),_.push(P.wrapR||0),_.push(P.magFilter),_.push(P.minFilter),_.push(P.anisotropy),_.push(P.internalFormat),_.push(P.format),_.push(P.type),_.push(P.generateMipmaps),_.push(P.premultiplyAlpha),_.push(P.flipY),_.push(P.unpackAlignment),_.push(P.colorSpace),_.join()}function Z(P,_){let X=n.get(P);if(P.isVideoTexture&&z(P),P.isRenderTargetTexture===!1&&P.isExternalTexture!==!0&&P.version>0&&X.__version!==P.version){let K=P.image;if(K===null)je("WebGLRenderer: Texture marked for update but no image data found.");else if(K.complete===!1)je("WebGLRenderer: Texture marked for update but image is incomplete");else{xe(X,P,_);return}}else P.isExternalTexture&&(X.__webglTexture=P.sourceTexture?P.sourceTexture:null);t.bindTexture(i.TEXTURE_2D,X.__webglTexture,i.TEXTURE0+_)}function Q(P,_){let X=n.get(P);if(P.isRenderTargetTexture===!1&&P.version>0&&X.__version!==P.version){xe(X,P,_);return}else P.isExternalTexture&&(X.__webglTexture=P.sourceTexture?P.sourceTexture:null);t.bindTexture(i.TEXTURE_2D_ARRAY,X.__webglTexture,i.TEXTURE0+_)}function ce(P,_){let X=n.get(P);if(P.isRenderTargetTexture===!1&&P.version>0&&X.__version!==P.version){xe(X,P,_);return}t.bindTexture(i.TEXTURE_3D,X.__webglTexture,i.TEXTURE0+_)}function se(P,_){let X=n.get(P);if(P.isCubeDepthTexture!==!0&&P.version>0&&X.__version!==P.version){Pe(X,P,_);return}t.bindTexture(i.TEXTURE_CUBE_MAP,X.__webglTexture,i.TEXTURE0+_)}let Ge={[Da]:i.REPEAT,[qn]:i.CLAMP_TO_EDGE,[Ua]:i.MIRRORED_REPEAT},Ce={[Yt]:i.NEAREST,[Bu]:i.NEAREST_MIPMAP_NEAREST,[kr]:i.NEAREST_MIPMAP_LINEAR,[Qt]:i.LINEAR,[po]:i.LINEAR_MIPMAP_NEAREST,[wi]:i.LINEAR_MIPMAP_LINEAR},ut={[Gu]:i.NEVER,[Yu]:i.ALWAYS,[Wu]:i.LESS,[Ko]:i.LEQUAL,[qu]:i.EQUAL,[Qo]:i.GEQUAL,[Xu]:i.GREATER,[$u]:i.NOTEQUAL};function Ze(P,_){if(_.type===Pn&&e.has("OES_texture_float_linear")===!1&&(_.magFilter===Qt||_.magFilter===po||_.magFilter===kr||_.magFilter===wi||_.minFilter===Qt||_.minFilter===po||_.minFilter===kr||_.minFilter===wi)&&je("WebGLRenderer: Unable to use linear filtering with floating point textures. OES_texture_float_linear not supported on this device."),i.texParameteri(P,i.TEXTURE_WRAP_S,Ge[_.wrapS]),i.texParameteri(P,i.TEXTURE_WRAP_T,Ge[_.wrapT]),(P===i.TEXTURE_3D||P===i.TEXTURE_2D_ARRAY)&&i.texParameteri(P,i.TEXTURE_WRAP_R,Ge[_.wrapR]),i.texParameteri(P,i.TEXTURE_MAG_FILTER,Ce[_.magFilter]),i.texParameteri(P,i.TEXTURE_MIN_FILTER,Ce[_.minFilter]),_.compareFunction&&(i.texParameteri(P,i.TEXTURE_COMPARE_MODE,i.COMPARE_REF_TO_TEXTURE),i.texParameteri(P,i.TEXTURE_COMPARE_FUNC,ut[_.compareFunction])),e.has("EXT_texture_filter_anisotropic")===!0){if(_.magFilter===Yt||_.minFilter!==kr&&_.minFilter!==wi||_.type===Pn&&e.has("OES_texture_float_linear")===!1)return;if(_.anisotropy>1||n.get(_).__currentAnisotropy){let X=e.get("EXT_texture_filter_anisotropic");i.texParameterf(P,X.TEXTURE_MAX_ANISOTROPY_EXT,Math.min(_.anisotropy,s.getMaxAnisotropy())),n.get(_).__currentAnisotropy=_.anisotropy}}}function Xe(P,_){let X=!1;P.__webglInit===void 0&&(P.__webglInit=!0,_.addEventListener("dispose",I));let K=_.source,ae=d.get(K);ae===void 0&&(ae={},d.set(K,ae));let be=re(_);if(be!==P.__cacheKey){ae[be]===void 0&&(ae[be]={texture:i.createTexture(),usedTimes:0},a.memory.textures++,X=!0),ae[be].usedTimes++;let Ee=ae[P.__cacheKey];Ee!==void 0&&(ae[P.__cacheKey].usedTimes--,Ee.usedTimes===0&&D(_)),P.__cacheKey=be,P.__webglTexture=ae[be].texture}return X}function ee(P,_,X){return Math.floor(Math.floor(P/X)/_)}function ne(P,_,X,K){let be=P.updateRanges;if(be.length===0)t.texSubImage2D(i.TEXTURE_2D,0,0,0,_.width,_.height,X,K,_.data);else{be.sort((ge,ue)=>ge.start-ue.start);let Ee=0;for(let ge=1;ge<be.length;ge++){let ue=be[Ee],pe=be[ge],_e=ue.start+ue.count,Se=ee(pe.start,_.width,4),Be=ee(ue.start,_.width,4);pe.start<=_e+1&&Se===Be&&ee(pe.start+pe.count-1,_.width,4)===Se?ue.count=Math.max(ue.count,pe.start+pe.count-ue.start):(++Ee,be[Ee]=pe)}be.length=Ee+1;let N=t.getParameter(i.UNPACK_ROW_LENGTH),V=t.getParameter(i.UNPACK_SKIP_PIXELS),ie=t.getParameter(i.UNPACK_SKIP_ROWS);t.pixelStorei(i.UNPACK_ROW_LENGTH,_.width);for(let ge=0,ue=be.length;ge<ue;ge++){let pe=be[ge],_e=Math.floor(pe.start/4),Se=Math.ceil(pe.count/4),Be=_e%_.width,O=Math.floor(_e/_.width),Me=Se,J=1;t.pixelStorei(i.UNPACK_SKIP_PIXELS,Be),t.pixelStorei(i.UNPACK_SKIP_ROWS,O),t.texSubImage2D(i.TEXTURE_2D,0,Be,O,Me,J,X,K,_.data)}P.clearUpdateRanges(),t.pixelStorei(i.UNPACK_ROW_LENGTH,N),t.pixelStorei(i.UNPACK_SKIP_PIXELS,V),t.pixelStorei(i.UNPACK_SKIP_ROWS,ie)}}function xe(P,_,X){let K=i.TEXTURE_2D;(_.isDataArrayTexture||_.isCompressedArrayTexture)&&(K=i.TEXTURE_2D_ARRAY),_.isData3DTexture&&(K=i.TEXTURE_3D);let ae=Xe(P,_),be=_.source;t.bindTexture(K,P.__webglTexture,i.TEXTURE0+X);let Ee=n.get(be);if(be.version!==Ee.__version||ae===!0){if(t.activeTexture(i.TEXTURE0+X),(typeof ImageBitmap<"u"&&_.image instanceof ImageBitmap)===!1){let J=pt.getPrimaries(pt.workingColorSpace),ve=_.colorSpace===li?null:pt.getPrimaries(_.colorSpace),we=_.colorSpace===li||J===ve?i.NONE:i.BROWSER_DEFAULT_WEBGL;t.pixelStorei(i.UNPACK_FLIP_Y_WEBGL,_.flipY),t.pixelStorei(i.UNPACK_PREMULTIPLY_ALPHA_WEBGL,_.premultiplyAlpha),t.pixelStorei(i.UNPACK_COLORSPACE_CONVERSION_WEBGL,we)}t.pixelStorei(i.UNPACK_ALIGNMENT,_.unpackAlignment);let V=m(_.image,!1,s.maxTextureSize);V=Et(_,V);let ie=r.convert(_.format,_.colorSpace),ge=r.convert(_.type),ue=y(_.internalFormat,ie,ge,_.normalized,_.colorSpace,_.isVideoTexture);Ze(K,_);let pe,_e=_.mipmaps,Se=_.isVideoTexture!==!0,Be=Ee.__version===void 0||ae===!0,O=be.dataReady,Me=T(_,V);if(_.isDepthTexture)ue=w(_.format===Ai,_.type),Be&&(Se?t.texStorage2D(i.TEXTURE_2D,1,ue,V.width,V.height):t.texImage2D(i.TEXTURE_2D,0,ue,V.width,V.height,0,ie,ge,null));else if(_.isDataTexture)if(_e.length>0){Se&&Be&&t.texStorage2D(i.TEXTURE_2D,Me,ue,_e[0].width,_e[0].height);for(let J=0,ve=_e.length;J<ve;J++)pe=_e[J],Se?O&&t.texSubImage2D(i.TEXTURE_2D,J,0,0,pe.width,pe.height,ie,ge,pe.data):t.texImage2D(i.TEXTURE_2D,J,ue,pe.width,pe.height,0,ie,ge,pe.data);_.generateMipmaps=!1}else Se?(Be&&t.texStorage2D(i.TEXTURE_2D,Me,ue,V.width,V.height),O&&ne(_,V,ie,ge)):t.texImage2D(i.TEXTURE_2D,0,ue,V.width,V.height,0,ie,ge,V.data);else if(_.isCompressedTexture)if(_.isCompressedArrayTexture){Se&&Be&&t.texStorage3D(i.TEXTURE_2D_ARRAY,Me,ue,_e[0].width,_e[0].height,V.depth);for(let J=0,ve=_e.length;J<ve;J++)if(pe=_e[J],_.format!==In)if(ie!==null)if(Se){if(O)if(_.layerUpdates.size>0){let we=gc(pe.width,pe.height,_.format,_.type);for(let fe of _.layerUpdates){let We=pe.data.subarray(fe*we/pe.data.BYTES_PER_ELEMENT,(fe+1)*we/pe.data.BYTES_PER_ELEMENT);t.compressedTexSubImage3D(i.TEXTURE_2D_ARRAY,J,0,0,fe,pe.width,pe.height,1,ie,We)}}else t.compressedTexSubImage3D(i.TEXTURE_2D_ARRAY,J,0,0,0,pe.width,pe.height,V.depth,ie,pe.data)}else t.compressedTexImage3D(i.TEXTURE_2D_ARRAY,J,ue,pe.width,pe.height,V.depth,0,pe.data,0,0);else je("WebGLRenderer: Attempt to load unsupported compressed texture format in .uploadTexture()");else Se?O&&t.texSubImage3D(i.TEXTURE_2D_ARRAY,J,0,0,0,pe.width,pe.height,V.depth,ie,ge,pe.data):t.texImage3D(i.TEXTURE_2D_ARRAY,J,ue,pe.width,pe.height,V.depth,0,ie,ge,pe.data);_.layerUpdates.size>0&&_.clearLayerUpdates()}else{Se&&Be&&t.texStorage2D(i.TEXTURE_2D,Me,ue,_e[0].width,_e[0].height);for(let J=0,ve=_e.length;J<ve;J++)pe=_e[J],_.format!==In?ie!==null?Se?O&&t.compressedTexSubImage2D(i.TEXTURE_2D,J,0,0,pe.width,pe.height,ie,pe.data):t.compressedTexImage2D(i.TEXTURE_2D,J,ue,pe.width,pe.height,0,pe.data):je("WebGLRenderer: Attempt to load unsupported compressed texture format in .uploadTexture()"):Se?O&&t.texSubImage2D(i.TEXTURE_2D,J,0,0,pe.width,pe.height,ie,ge,pe.data):t.texImage2D(i.TEXTURE_2D,J,ue,pe.width,pe.height,0,ie,ge,pe.data)}else if(_.isDataArrayTexture)if(Se){if(Be&&t.texStorage3D(i.TEXTURE_2D_ARRAY,Me,ue,V.width,V.height,V.depth),O)if(_.layerUpdates.size>0){let J=gc(V.width,V.height,_.format,_.type);for(let ve of _.layerUpdates){let we=V.data.subarray(ve*J/V.data.BYTES_PER_ELEMENT,(ve+1)*J/V.data.BYTES_PER_ELEMENT);t.texSubImage3D(i.TEXTURE_2D_ARRAY,0,0,0,ve,V.width,V.height,1,ie,ge,we)}_.clearLayerUpdates()}else t.texSubImage3D(i.TEXTURE_2D_ARRAY,0,0,0,0,V.width,V.height,V.depth,ie,ge,V.data)}else t.texImage3D(i.TEXTURE_2D_ARRAY,0,ue,V.width,V.height,V.depth,0,ie,ge,V.data);else if(_.isData3DTexture)Se?(Be&&t.texStorage3D(i.TEXTURE_3D,Me,ue,V.width,V.height,V.depth),O&&t.texSubImage3D(i.TEXTURE_3D,0,0,0,0,V.width,V.height,V.depth,ie,ge,V.data)):t.texImage3D(i.TEXTURE_3D,0,ue,V.width,V.height,V.depth,0,ie,ge,V.data);else if(_.isFramebufferTexture){if(Be)if(Se)t.texStorage2D(i.TEXTURE_2D,Me,ue,V.width,V.height);else{let J=V.width,ve=V.height;for(let we=0;we<Me;we++)t.texImage2D(i.TEXTURE_2D,we,ue,J,ve,0,ie,ge,null),J>>=1,ve>>=1}}else if(_.isHTMLTexture){if("texElementImage2D"in i){let J=i.canvas;if(J.hasAttribute("layoutsubtree")||J.setAttribute("layoutsubtree","true"),V.parentNode!==J){J.appendChild(V),f.add(_),J.onpaint=ve=>{let we=ve.changedElements;for(let fe of f)we.includes(fe.image)&&(fe.needsUpdate=!0)},J.requestPaint();return}if(i.texElementImage2D.length===3)i.texElementImage2D(i.TEXTURE_2D,i.RGBA8,V);else{let we=i.RGBA,fe=i.RGBA,We=i.UNSIGNED_BYTE;i.texElementImage2D(i.TEXTURE_2D,0,we,fe,We,V)}i.texParameteri(i.TEXTURE_2D,i.TEXTURE_MIN_FILTER,i.LINEAR),i.texParameteri(i.TEXTURE_2D,i.TEXTURE_WRAP_S,i.CLAMP_TO_EDGE),i.texParameteri(i.TEXTURE_2D,i.TEXTURE_WRAP_T,i.CLAMP_TO_EDGE)}}else if(_e.length>0){if(Se&&Be){let J=lt(_e[0]);t.texStorage2D(i.TEXTURE_2D,Me,ue,J.width,J.height)}for(let J=0,ve=_e.length;J<ve;J++)pe=_e[J],Se?O&&t.texSubImage2D(i.TEXTURE_2D,J,0,0,ie,ge,pe):t.texImage2D(i.TEXTURE_2D,J,ue,ie,ge,pe);_.generateMipmaps=!1}else if(Se){if(Be){let J=lt(V);t.texStorage2D(i.TEXTURE_2D,Me,ue,J.width,J.height)}O&&t.texSubImage2D(i.TEXTURE_2D,0,0,0,ie,ge,V)}else t.texImage2D(i.TEXTURE_2D,0,ue,ie,ge,V);p(_)&&E(K),Ee.__version=be.version,_.onUpdate&&_.onUpdate(_)}P.__version=_.version}function Pe(P,_,X){if(_.image.length!==6)return;let K=Xe(P,_),ae=_.source;t.bindTexture(i.TEXTURE_CUBE_MAP,P.__webglTexture,i.TEXTURE0+X);let be=n.get(ae);if(ae.version!==be.__version||K===!0){t.activeTexture(i.TEXTURE0+X);let Ee=pt.getPrimaries(pt.workingColorSpace),N=_.colorSpace===li?null:pt.getPrimaries(_.colorSpace),V=_.colorSpace===li||Ee===N?i.NONE:i.BROWSER_DEFAULT_WEBGL;t.pixelStorei(i.UNPACK_FLIP_Y_WEBGL,_.flipY),t.pixelStorei(i.UNPACK_PREMULTIPLY_ALPHA_WEBGL,_.premultiplyAlpha),t.pixelStorei(i.UNPACK_ALIGNMENT,_.unpackAlignment),t.pixelStorei(i.UNPACK_COLORSPACE_CONVERSION_WEBGL,V);let ie=_.isCompressedTexture||_.image[0].isCompressedTexture,ge=_.image[0]&&_.image[0].isDataTexture,ue=[];for(let fe=0;fe<6;fe++)!ie&&!ge?ue[fe]=m(_.image[fe],!0,s.maxCubemapSize):ue[fe]=ge?_.image[fe].image:_.image[fe],ue[fe]=Et(_,ue[fe]);let pe=ue[0],_e=r.convert(_.format,_.colorSpace),Se=r.convert(_.type),Be=y(_.internalFormat,_e,Se,_.normalized,_.colorSpace),O=_.isVideoTexture!==!0,Me=be.__version===void 0||K===!0,J=ae.dataReady,ve=T(_,pe);Ze(i.TEXTURE_CUBE_MAP,_);let we;if(ie){O&&Me&&t.texStorage2D(i.TEXTURE_CUBE_MAP,ve,Be,pe.width,pe.height);for(let fe=0;fe<6;fe++){we=ue[fe].mipmaps;for(let We=0;We<we.length;We++){let Ve=we[We];_.format!==In?_e!==null?O?J&&t.compressedTexSubImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+fe,We,0,0,Ve.width,Ve.height,_e,Ve.data):t.compressedTexImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+fe,We,Be,Ve.width,Ve.height,0,Ve.data):je("WebGLRenderer: Attempt to load unsupported compressed texture format in .setTextureCube()"):O?J&&t.texSubImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+fe,We,0,0,Ve.width,Ve.height,_e,Se,Ve.data):t.texImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+fe,We,Be,Ve.width,Ve.height,0,_e,Se,Ve.data)}}}else{if(we=_.mipmaps,O&&Me){we.length>0&&ve++;let fe=lt(ue[0]);t.texStorage2D(i.TEXTURE_CUBE_MAP,ve,Be,fe.width,fe.height)}for(let fe=0;fe<6;fe++)if(ge){O?J&&t.texSubImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+fe,0,0,0,ue[fe].width,ue[fe].height,_e,Se,ue[fe].data):t.texImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+fe,0,Be,ue[fe].width,ue[fe].height,0,_e,Se,ue[fe].data);for(let We=0;We<we.length;We++){let Ct=we[We].image[fe].image;O?J&&t.texSubImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+fe,We+1,0,0,Ct.width,Ct.height,_e,Se,Ct.data):t.texImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+fe,We+1,Be,Ct.width,Ct.height,0,_e,Se,Ct.data)}}else{O?J&&t.texSubImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+fe,0,0,0,_e,Se,ue[fe]):t.texImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+fe,0,Be,_e,Se,ue[fe]);for(let We=0;We<we.length;We++){let Ve=we[We];O?J&&t.texSubImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+fe,We+1,0,0,_e,Se,Ve.image[fe]):t.texImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+fe,We+1,Be,_e,Se,Ve.image[fe])}}}p(_)&&E(i.TEXTURE_CUBE_MAP),be.__version=ae.version,_.onUpdate&&_.onUpdate(_)}P.__version=_.version}function Re(P,_,X,K,ae,be){let Ee=r.convert(X.format,X.colorSpace),N=r.convert(X.type),V=y(X.internalFormat,Ee,N,X.normalized,X.colorSpace),ie=n.get(_),ge=n.get(X);if(ge.__renderTarget=_,!ie.__hasExternalTextures){let ue=Math.max(1,_.width>>be),pe=Math.max(1,_.height>>be);ae===i.TEXTURE_3D||ae===i.TEXTURE_2D_ARRAY?t.texImage3D(ae,be,V,ue,pe,_.depth,0,Ee,N,null):t.texImage2D(ae,be,V,ue,pe,0,Ee,N,null)}t.bindFramebuffer(i.FRAMEBUFFER,P),Tt(_)?o.framebufferTexture2DMultisampleEXT(i.FRAMEBUFFER,K,ae,ge.__webglTexture,0,_t(_)):(ae===i.TEXTURE_2D||ae>=i.TEXTURE_CUBE_MAP_POSITIVE_X&&ae<=i.TEXTURE_CUBE_MAP_NEGATIVE_Z)&&i.framebufferTexture2D(i.FRAMEBUFFER,K,ae,ge.__webglTexture,be),t.bindFramebuffer(i.FRAMEBUFFER,null)}function Je(P,_,X){if(i.bindRenderbuffer(i.RENDERBUFFER,P),_.depthBuffer){let K=_.depthTexture,ae=K&&K.isDepthTexture?K.type:null,be=w(_.stencilBuffer,ae),Ee=_.stencilBuffer?i.DEPTH_STENCIL_ATTACHMENT:i.DEPTH_ATTACHMENT;Tt(_)?o.renderbufferStorageMultisampleEXT(i.RENDERBUFFER,_t(_),be,_.width,_.height):X?i.renderbufferStorageMultisample(i.RENDERBUFFER,_t(_),be,_.width,_.height):i.renderbufferStorage(i.RENDERBUFFER,be,_.width,_.height),i.framebufferRenderbuffer(i.FRAMEBUFFER,Ee,i.RENDERBUFFER,P)}else{let K=_.textures;for(let ae=0;ae<K.length;ae++){let be=K[ae],Ee=r.convert(be.format,be.colorSpace),N=r.convert(be.type),V=y(be.internalFormat,Ee,N,be.normalized,be.colorSpace);Tt(_)?o.renderbufferStorageMultisampleEXT(i.RENDERBUFFER,_t(_),V,_.width,_.height):X?i.renderbufferStorageMultisample(i.RENDERBUFFER,_t(_),V,_.width,_.height):i.renderbufferStorage(i.RENDERBUFFER,V,_.width,_.height)}}i.bindRenderbuffer(i.RENDERBUFFER,null)}function dt(P,_,X){let K=_.isWebGLCubeRenderTarget===!0;if(t.bindFramebuffer(i.FRAMEBUFFER,P),!(_.depthTexture&&_.depthTexture.isDepthTexture))throw new Error("THREE.WebGLTextures: renderTarget.depthTexture must be an instance of THREE.DepthTexture.");let ae=n.get(_.depthTexture);if(ae.__renderTarget=_,(!ae.__webglTexture||_.depthTexture.image.width!==_.width||_.depthTexture.image.height!==_.height)&&(_.depthTexture.image.width=_.width,_.depthTexture.image.height=_.height,_.depthTexture.needsUpdate=!0),K){if(ae.__webglInit===void 0&&(ae.__webglInit=!0,_.depthTexture.addEventListener("dispose",I)),ae.__webglTexture===void 0){ae.__webglTexture=i.createTexture(),t.bindTexture(i.TEXTURE_CUBE_MAP,ae.__webglTexture),Ze(i.TEXTURE_CUBE_MAP,_.depthTexture);let ie=r.convert(_.depthTexture.format),ge=r.convert(_.depthTexture.type),ue;_.depthTexture.format===Xn?ue=i.DEPTH_COMPONENT24:_.depthTexture.format===Ai&&(ue=i.DEPTH24_STENCIL8);for(let pe=0;pe<6;pe++)i.texImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+pe,0,ue,_.width,_.height,0,ie,ge,null)}}else Z(_.depthTexture,0);let be=ae.__webglTexture,Ee=_t(_),N=K?i.TEXTURE_CUBE_MAP_POSITIVE_X+X:i.TEXTURE_2D,V=_.depthTexture.format===Ai?i.DEPTH_STENCIL_ATTACHMENT:i.DEPTH_ATTACHMENT;if(_.depthTexture.format===Xn)Tt(_)?o.framebufferTexture2DMultisampleEXT(i.FRAMEBUFFER,V,N,be,0,Ee):i.framebufferTexture2D(i.FRAMEBUFFER,V,N,be,0);else if(_.depthTexture.format===Ai)Tt(_)?o.framebufferTexture2DMultisampleEXT(i.FRAMEBUFFER,V,N,be,0,Ee):i.framebufferTexture2D(i.FRAMEBUFFER,V,N,be,0);else throw new Error("THREE.WebGLTextures: Unknown depthTexture format.")}function it(P){let _=n.get(P),X=P.isWebGLCubeRenderTarget===!0;if(_.__boundDepthTexture!==P.depthTexture){let K=P.depthTexture;if(_.__depthDisposeCallback&&_.__depthDisposeCallback(),K){let ae=()=>{delete _.__boundDepthTexture,delete _.__depthDisposeCallback,K.removeEventListener("dispose",ae)};K.addEventListener("dispose",ae),_.__depthDisposeCallback=ae}_.__boundDepthTexture=K}if(P.depthTexture&&!_.__autoAllocateDepthBuffer)if(X)for(let K=0;K<6;K++)dt(_.__webglFramebuffer[K],P,K);else{let K=P.texture.mipmaps;K&&K.length>0?dt(_.__webglFramebuffer[0],P,0):dt(_.__webglFramebuffer,P,0)}else if(X){_.__webglDepthbuffer=[];for(let K=0;K<6;K++)if(t.bindFramebuffer(i.FRAMEBUFFER,_.__webglFramebuffer[K]),_.__webglDepthbuffer[K]===void 0)_.__webglDepthbuffer[K]=i.createRenderbuffer(),Je(_.__webglDepthbuffer[K],P,!1);else{let ae=P.stencilBuffer?i.DEPTH_STENCIL_ATTACHMENT:i.DEPTH_ATTACHMENT,be=_.__webglDepthbuffer[K];i.bindRenderbuffer(i.RENDERBUFFER,be),i.framebufferRenderbuffer(i.FRAMEBUFFER,ae,i.RENDERBUFFER,be)}}else{let K=P.texture.mipmaps;if(K&&K.length>0?t.bindFramebuffer(i.FRAMEBUFFER,_.__webglFramebuffer[0]):t.bindFramebuffer(i.FRAMEBUFFER,_.__webglFramebuffer),_.__webglDepthbuffer===void 0)_.__webglDepthbuffer=i.createRenderbuffer(),Je(_.__webglDepthbuffer,P,!1);else{let ae=P.stencilBuffer?i.DEPTH_STENCIL_ATTACHMENT:i.DEPTH_ATTACHMENT,be=_.__webglDepthbuffer;i.bindRenderbuffer(i.RENDERBUFFER,be),i.framebufferRenderbuffer(i.FRAMEBUFFER,ae,i.RENDERBUFFER,be)}}t.bindFramebuffer(i.FRAMEBUFFER,null)}function ot(P,_,X){let K=n.get(P);_!==void 0&&Re(K.__webglFramebuffer,P,P.texture,i.COLOR_ATTACHMENT0,i.TEXTURE_2D,0),X!==void 0&&it(P)}function gt(P){let _=P.texture,X=n.get(P),K=n.get(_);P.addEventListener("dispose",x);let ae=P.textures,be=P.isWebGLCubeRenderTarget===!0,Ee=ae.length>1;if(Ee||(K.__webglTexture===void 0&&(K.__webglTexture=i.createTexture()),K.__version=_.version,a.memory.textures++),be){X.__webglFramebuffer=[];for(let N=0;N<6;N++)if(_.mipmaps&&_.mipmaps.length>0){X.__webglFramebuffer[N]=[];for(let V=0;V<_.mipmaps.length;V++)X.__webglFramebuffer[N][V]=i.createFramebuffer()}else X.__webglFramebuffer[N]=i.createFramebuffer()}else{if(_.mipmaps&&_.mipmaps.length>0){X.__webglFramebuffer=[];for(let N=0;N<_.mipmaps.length;N++)X.__webglFramebuffer[N]=i.createFramebuffer()}else X.__webglFramebuffer=i.createFramebuffer();if(Ee)for(let N=0,V=ae.length;N<V;N++){let ie=n.get(ae[N]);ie.__webglTexture===void 0&&(ie.__webglTexture=i.createTexture(),a.memory.textures++)}if(P.samples>0&&Tt(P)===!1){X.__webglMultisampledFramebuffer=i.createFramebuffer(),X.__webglColorRenderbuffer=[],t.bindFramebuffer(i.FRAMEBUFFER,X.__webglMultisampledFramebuffer);for(let N=0;N<ae.length;N++){let V=ae[N];X.__webglColorRenderbuffer[N]=i.createRenderbuffer(),i.bindRenderbuffer(i.RENDERBUFFER,X.__webglColorRenderbuffer[N]);let ie=r.convert(V.format,V.colorSpace),ge=r.convert(V.type),ue=y(V.internalFormat,ie,ge,V.normalized,V.colorSpace,P.isXRRenderTarget===!0),pe=_t(P);i.renderbufferStorageMultisample(i.RENDERBUFFER,pe,ue,P.width,P.height),i.framebufferRenderbuffer(i.FRAMEBUFFER,i.COLOR_ATTACHMENT0+N,i.RENDERBUFFER,X.__webglColorRenderbuffer[N])}i.bindRenderbuffer(i.RENDERBUFFER,null),P.depthBuffer&&(X.__webglDepthRenderbuffer=i.createRenderbuffer(),Je(X.__webglDepthRenderbuffer,P,!0)),t.bindFramebuffer(i.FRAMEBUFFER,null)}}if(be){t.bindTexture(i.TEXTURE_CUBE_MAP,K.__webglTexture),Ze(i.TEXTURE_CUBE_MAP,_);for(let N=0;N<6;N++)if(_.mipmaps&&_.mipmaps.length>0)for(let V=0;V<_.mipmaps.length;V++)Re(X.__webglFramebuffer[N][V],P,_,i.COLOR_ATTACHMENT0,i.TEXTURE_CUBE_MAP_POSITIVE_X+N,V);else Re(X.__webglFramebuffer[N],P,_,i.COLOR_ATTACHMENT0,i.TEXTURE_CUBE_MAP_POSITIVE_X+N,0);p(_)&&E(i.TEXTURE_CUBE_MAP),t.unbindTexture()}else if(Ee){for(let N=0,V=ae.length;N<V;N++){let ie=ae[N],ge=n.get(ie),ue=i.TEXTURE_2D;(P.isWebGL3DRenderTarget||P.isWebGLArrayRenderTarget)&&(ue=P.isWebGL3DRenderTarget?i.TEXTURE_3D:i.TEXTURE_2D_ARRAY),t.bindTexture(ue,ge.__webglTexture),Ze(ue,ie),Re(X.__webglFramebuffer,P,ie,i.COLOR_ATTACHMENT0+N,ue,0),p(ie)&&E(ue)}t.unbindTexture()}else{let N=i.TEXTURE_2D;if((P.isWebGL3DRenderTarget||P.isWebGLArrayRenderTarget)&&(N=P.isWebGL3DRenderTarget?i.TEXTURE_3D:i.TEXTURE_2D_ARRAY),t.bindTexture(N,K.__webglTexture),Ze(N,_),_.mipmaps&&_.mipmaps.length>0)for(let V=0;V<_.mipmaps.length;V++)Re(X.__webglFramebuffer[V],P,_,i.COLOR_ATTACHMENT0,N,V);else Re(X.__webglFramebuffer,P,_,i.COLOR_ATTACHMENT0,N,0);p(_)&&E(N),t.unbindTexture()}P.depthBuffer&&it(P)}function rt(P){let _=P.textures;for(let X=0,K=_.length;X<K;X++){let ae=_[X];if(p(ae)){let be=C(P),Ee=n.get(ae).__webglTexture;t.bindTexture(be,Ee),E(be),t.unbindTexture()}}}let at=[],Dt=[];function Lt(P){if(P.samples>0){if(Tt(P)===!1){let _=P.textures,X=P.width,K=P.height,ae=i.COLOR_BUFFER_BIT,be=P.stencilBuffer?i.DEPTH_STENCIL_ATTACHMENT:i.DEPTH_ATTACHMENT,Ee=n.get(P),N=_.length>1;if(N)for(let ie=0;ie<_.length;ie++)t.bindFramebuffer(i.FRAMEBUFFER,Ee.__webglMultisampledFramebuffer),i.framebufferRenderbuffer(i.FRAMEBUFFER,i.COLOR_ATTACHMENT0+ie,i.RENDERBUFFER,null),t.bindFramebuffer(i.FRAMEBUFFER,Ee.__webglFramebuffer),i.framebufferTexture2D(i.DRAW_FRAMEBUFFER,i.COLOR_ATTACHMENT0+ie,i.TEXTURE_2D,null,0);t.bindFramebuffer(i.READ_FRAMEBUFFER,Ee.__webglMultisampledFramebuffer);let V=P.texture.mipmaps;V&&V.length>0?t.bindFramebuffer(i.DRAW_FRAMEBUFFER,Ee.__webglFramebuffer[0]):t.bindFramebuffer(i.DRAW_FRAMEBUFFER,Ee.__webglFramebuffer);for(let ie=0;ie<_.length;ie++){if(P.resolveDepthBuffer&&(P.depthBuffer&&(ae|=i.DEPTH_BUFFER_BIT),P.stencilBuffer&&P.resolveStencilBuffer&&(ae|=i.STENCIL_BUFFER_BIT)),N){i.framebufferRenderbuffer(i.READ_FRAMEBUFFER,i.COLOR_ATTACHMENT0,i.RENDERBUFFER,Ee.__webglColorRenderbuffer[ie]);let ge=n.get(_[ie]).__webglTexture;i.framebufferTexture2D(i.DRAW_FRAMEBUFFER,i.COLOR_ATTACHMENT0,i.TEXTURE_2D,ge,0)}i.blitFramebuffer(0,0,X,K,0,0,X,K,ae,i.NEAREST),l===!0&&(at.length=0,Dt.length=0,at.push(i.COLOR_ATTACHMENT0+ie),P.depthBuffer&&P.storeMultisampledDepthBuffer===!1&&(at.push(be),Dt.push(be),i.invalidateFramebuffer(i.DRAW_FRAMEBUFFER,Dt)),i.invalidateFramebuffer(i.READ_FRAMEBUFFER,at))}if(t.bindFramebuffer(i.READ_FRAMEBUFFER,null),t.bindFramebuffer(i.DRAW_FRAMEBUFFER,null),N)for(let ie=0;ie<_.length;ie++){t.bindFramebuffer(i.FRAMEBUFFER,Ee.__webglMultisampledFramebuffer),i.framebufferRenderbuffer(i.FRAMEBUFFER,i.COLOR_ATTACHMENT0+ie,i.RENDERBUFFER,Ee.__webglColorRenderbuffer[ie]);let ge=n.get(_[ie]).__webglTexture;t.bindFramebuffer(i.FRAMEBUFFER,Ee.__webglFramebuffer),i.framebufferTexture2D(i.DRAW_FRAMEBUFFER,i.COLOR_ATTACHMENT0+ie,i.TEXTURE_2D,ge,0)}t.bindFramebuffer(i.DRAW_FRAMEBUFFER,Ee.__webglMultisampledFramebuffer)}else if(P.depthBuffer&&P.storeMultisampledDepthBuffer===!1&&l){let _=P.stencilBuffer?i.DEPTH_STENCIL_ATTACHMENT:i.DEPTH_ATTACHMENT;i.invalidateFramebuffer(i.DRAW_FRAMEBUFFER,[_])}}}function _t(P){return Math.min(s.maxSamples,P.samples)}function Tt(P){let _=n.get(P);return P.samples>0&&e.has("WEBGL_multisampled_render_to_texture")===!0&&_.__useRenderToTexture!==!1}function z(P){let _=a.render.frame;h.get(P)!==_&&(h.set(P,_),P.update())}function Et(P,_){let X=P.colorSpace,K=P.format,ae=P.type;return P.isCompressedTexture===!0||P.isVideoTexture===!0||X!==ir&&X!==li&&(pt.getTransfer(X)===St?(K!==In||ae!==xn)&&je("WebGLTextures: sRGB encoded textures have to use RGBAFormat and UnsignedByteType."):nt("WebGLTextures: Unsupported texture color space:",X)),_}function lt(P){return typeof HTMLImageElement<"u"&&P instanceof HTMLImageElement?(c.width=P.naturalWidth||P.width,c.height=P.naturalHeight||P.height):typeof VideoFrame<"u"&&P instanceof VideoFrame?(c.width=P.displayWidth,c.height=P.displayHeight):(c.width=P.width,c.height=P.height),c}this.allocateTextureUnit=te,this.resetTextureUnits=Y,this.getTextureUnits=F,this.setTextureUnits=$,this.setTexture2D=Z,this.setTexture2DArray=Q,this.setTexture3D=ce,this.setTextureCube=se,this.rebindTextures=ot,this.setupRenderTarget=gt,this.updateRenderTargetMipmap=rt,this.updateMultisampleRenderTarget=Lt,this.setupDepthRenderbuffer=it,this.setupFrameBufferTexture=Re,this.useMultisampledRTT=Tt,this.isReversedDepthBuffer=function(){return t.buffers.depth.getReversed()}}function k0(i,e){function t(n,s=li){let r,a=pt.getTransfer(s);if(n===xn)return i.UNSIGNED_BYTE;if(n===go)return i.UNSIGNED_SHORT_4_4_4_4;if(n===_o)return i.UNSIGNED_SHORT_5_5_5_1;if(n===sc)return i.UNSIGNED_INT_5_9_9_9_REV;if(n===rc)return i.UNSIGNED_INT_10F_11F_11F_REV;if(n===nc)return i.BYTE;if(n===ic)return i.SHORT;if(n===Ps)return i.UNSIGNED_SHORT;if(n===mo)return i.INT;if(n===Vn)return i.UNSIGNED_INT;if(n===Pn)return i.FLOAT;if(n===tn)return i.HALF_FLOAT;if(n===ac)return i.ALPHA;if(n===oc)return i.RGB;if(n===In)return i.RGBA;if(n===Xn)return i.DEPTH_COMPONENT;if(n===Ai)return i.DEPTH_STENCIL;if(n===xo)return i.RED;if(n===vo)return i.RED_INTEGER;if(n===Ci)return i.RG;if(n===yo)return i.RG_INTEGER;if(n===bo)return i.RGBA_INTEGER;if(n===Or||n===Br||n===zr||n===Vr)if(a===St)if(r=e.get("WEBGL_compressed_texture_s3tc_srgb"),r!==null){if(n===Or)return r.COMPRESSED_SRGB_S3TC_DXT1_EXT;if(n===Br)return r.COMPRESSED_SRGB_ALPHA_S3TC_DXT1_EXT;if(n===zr)return r.COMPRESSED_SRGB_ALPHA_S3TC_DXT3_EXT;if(n===Vr)return r.COMPRESSED_SRGB_ALPHA_S3TC_DXT5_EXT}else return null;else if(r=e.get("WEBGL_compressed_texture_s3tc"),r!==null){if(n===Or)return r.COMPRESSED_RGB_S3TC_DXT1_EXT;if(n===Br)return r.COMPRESSED_RGBA_S3TC_DXT1_EXT;if(n===zr)return r.COMPRESSED_RGBA_S3TC_DXT3_EXT;if(n===Vr)return r.COMPRESSED_RGBA_S3TC_DXT5_EXT}else return null;if(n===Mo||n===So||n===To||n===Eo)if(r=e.get("WEBGL_compressed_texture_pvrtc"),r!==null){if(n===Mo)return r.COMPRESSED_RGB_PVRTC_4BPPV1_IMG;if(n===So)return r.COMPRESSED_RGB_PVRTC_2BPPV1_IMG;if(n===To)return r.COMPRESSED_RGBA_PVRTC_4BPPV1_IMG;if(n===Eo)return r.COMPRESSED_RGBA_PVRTC_2BPPV1_IMG}else return null;if(n===wo||n===Ao||n===Co||n===Ro||n===Po||n===Hr||n===Io)if(r=e.get("WEBGL_compressed_texture_etc"),r!==null){if(n===wo||n===Ao)return a===St?r.COMPRESSED_SRGB8_ETC2:r.COMPRESSED_RGB8_ETC2;if(n===Co)return a===St?r.COMPRESSED_SRGB8_ALPHA8_ETC2_EAC:r.COMPRESSED_RGBA8_ETC2_EAC;if(n===Ro)return r.COMPRESSED_R11_EAC;if(n===Po)return r.COMPRESSED_SIGNED_R11_EAC;if(n===Hr)return r.COMPRESSED_RG11_EAC;if(n===Io)return r.COMPRESSED_SIGNED_RG11_EAC}else return null;if(n===Lo||n===No||n===Do||n===Uo||n===Fo||n===ko||n===Oo||n===Bo||n===zo||n===Vo||n===Ho||n===Go||n===Wo||n===qo)if(r=e.get("WEBGL_compressed_texture_astc"),r!==null){if(n===Lo)return a===St?r.COMPRESSED_SRGB8_ALPHA8_ASTC_4x4_KHR:r.COMPRESSED_RGBA_ASTC_4x4_KHR;if(n===No)return a===St?r.COMPRESSED_SRGB8_ALPHA8_ASTC_5x4_KHR:r.COMPRESSED_RGBA_ASTC_5x4_KHR;if(n===Do)return a===St?r.COMPRESSED_SRGB8_ALPHA8_ASTC_5x5_KHR:r.COMPRESSED_RGBA_ASTC_5x5_KHR;if(n===Uo)return a===St?r.COMPRESSED_SRGB8_ALPHA8_ASTC_6x5_KHR:r.COMPRESSED_RGBA_ASTC_6x5_KHR;if(n===Fo)return a===St?r.COMPRESSED_SRGB8_ALPHA8_ASTC_6x6_KHR:r.COMPRESSED_RGBA_ASTC_6x6_KHR;if(n===ko)return a===St?r.COMPRESSED_SRGB8_ALPHA8_ASTC_8x5_KHR:r.COMPRESSED_RGBA_ASTC_8x5_KHR;if(n===Oo)return a===St?r.COMPRESSED_SRGB8_ALPHA8_ASTC_8x6_KHR:r.COMPRESSED_RGBA_ASTC_8x6_KHR;if(n===Bo)return a===St?r.COMPRESSED_SRGB8_ALPHA8_ASTC_8x8_KHR:r.COMPRESSED_RGBA_ASTC_8x8_KHR;if(n===zo)return a===St?r.COMPRESSED_SRGB8_ALPHA8_ASTC_10x5_KHR:r.COMPRESSED_RGBA_ASTC_10x5_KHR;if(n===Vo)return a===St?r.COMPRESSED_SRGB8_ALPHA8_ASTC_10x6_KHR:r.COMPRESSED_RGBA_ASTC_10x6_KHR;if(n===Ho)return a===St?r.COMPRESSED_SRGB8_ALPHA8_ASTC_10x8_KHR:r.COMPRESSED_RGBA_ASTC_10x8_KHR;if(n===Go)return a===St?r.COMPRESSED_SRGB8_ALPHA8_ASTC_10x10_KHR:r.COMPRESSED_RGBA_ASTC_10x10_KHR;if(n===Wo)return a===St?r.COMPRESSED_SRGB8_ALPHA8_ASTC_12x10_KHR:r.COMPRESSED_RGBA_ASTC_12x10_KHR;if(n===qo)return a===St?r.COMPRESSED_SRGB8_ALPHA8_ASTC_12x12_KHR:r.COMPRESSED_RGBA_ASTC_12x12_KHR}else return null;if(n===Xo||n===$o||n===Yo)if(r=e.get("EXT_texture_compression_bptc"),r!==null){if(n===Xo)return a===St?r.COMPRESSED_SRGB_ALPHA_BPTC_UNORM_EXT:r.COMPRESSED_RGBA_BPTC_UNORM_EXT;if(n===$o)return r.COMPRESSED_RGB_BPTC_SIGNED_FLOAT_EXT;if(n===Yo)return r.COMPRESSED_RGB_BPTC_UNSIGNED_FLOAT_EXT}else return null;if(n===Zo||n===jo||n===Gr||n===Jo)if(r=e.get("EXT_texture_compression_rgtc"),r!==null){if(n===Zo)return r.COMPRESSED_RED_RGTC1_EXT;if(n===jo)return r.COMPRESSED_SIGNED_RED_RGTC1_EXT;if(n===Gr)return r.COMPRESSED_RED_GREEN_RGTC2_EXT;if(n===Jo)return r.COMPRESSED_SIGNED_RED_GREEN_RGTC2_EXT}else return null;return n===Is?i.UNSIGNED_INT_24_8:i[n]!==void 0?i[n]:null}return{convert:t}}var O0=`
void main() {

	gl_Position = vec4( position, 1.0 );

}`,B0=`
uniform sampler2DArray depthColor;
uniform float depthWidth;
uniform float depthHeight;

void main() {

	vec2 coord = vec2( gl_FragCoord.x / depthWidth, gl_FragCoord.y / depthHeight );

	if ( coord.x >= 1.0 ) {

		gl_FragDepth = texture( depthColor, vec3( coord.x - 1.0, coord.y, 1 ) ).r;

	} else {

		gl_FragDepth = texture( depthColor, vec3( coord.x, coord.y, 0 ) ).r;

	}

}`,Pc=class{constructor(){this.texture=null,this.mesh=null,this.depthNear=0,this.depthFar=0}init(e,t){if(this.texture===null){let n=new mr(e.texture);(e.depthNear!==t.depthNear||e.depthFar!==t.depthFar)&&(this.depthNear=e.depthNear,this.depthFar=e.depthFar),this.texture=n}}getMesh(e){if(this.texture!==null&&this.mesh===null){let t=e.cameras[0].viewport,n=new kt({vertexShader:O0,fragmentShader:B0,uniforms:{depthColor:{value:this.texture},depthWidth:{value:t.z},depthHeight:{value:t.w}}});this.mesh=new bt(new yr(20,20),n)}return this.mesh}reset(){this.texture=null,this.mesh=null}getDepthTexture(){return this.texture}},Ic=class extends $n{constructor(e,t){super();let n=this,s=null,r=1,a=null,o="local-floor",l=1,c=null,h=null,f=null,u=null,d=null,g=null,b=typeof XRWebGLBinding<"u",m=new Pc,p={},E=t.getContextAttributes(),C=null,y=null,w=[],T=[],I=new De,x=null,A=null,D=new Jt;D.viewport=new Ut;let k=new Jt;k.viewport=new Ut;let G=[D,k],Y=new co,F=null,$=null;this.cameraAutoUpdate=!0,this.enabled=!1,this.isPresenting=!1,this.getController=function(ee){let ne=w[ee];return ne===void 0&&(ne=new ys,w[ee]=ne),ne.getTargetRaySpace()},this.getControllerGrip=function(ee){let ne=w[ee];return ne===void 0&&(ne=new ys,w[ee]=ne),ne.getGripSpace()},this.getHand=function(ee){let ne=w[ee];return ne===void 0&&(ne=new ys,w[ee]=ne),ne.getHandSpace()};function te(ee){let ne=T.indexOf(ee.inputSource);if(ne===-1)return;let xe=w[ne];xe!==void 0&&(xe.update(ee.inputSource,ee.frame,c||a),xe.dispatchEvent({type:ee.type,data:ee.inputSource}))}function re(){s.removeEventListener("select",te),s.removeEventListener("selectstart",te),s.removeEventListener("selectend",te),s.removeEventListener("squeeze",te),s.removeEventListener("squeezestart",te),s.removeEventListener("squeezeend",te),s.removeEventListener("end",re),s.removeEventListener("inputsourceschange",Z);for(let ee=0;ee<w.length;ee++){let ne=T[ee];ne!==null&&(T[ee]=null,w[ee].disconnect(ne))}F=null,$=null,m.reset();for(let ee in p)delete p[ee];if(e.setRenderTarget(C),d=null,u=null,f=null,s=null,y=null,Xe.stop(),n.isPresenting=!1,e.setPixelRatio(x),e.setSize(I.width,I.height,!1),A!==null){let ee=A.camera;ee.fov=A.fov,ee.zoom=A.zoom,ee.updateProjectionMatrix(),A=null}n.dispatchEvent({type:"sessionend"})}this.setFramebufferScaleFactor=function(ee){r=ee,n.isPresenting===!0&&je("WebXRManager: Cannot change framebuffer scale while presenting.")},this.setReferenceSpaceType=function(ee){o=ee,n.isPresenting===!0&&je("WebXRManager: Cannot change reference space type while presenting.")},this.getReferenceSpace=function(){return c||a},this.setReferenceSpace=function(ee){c=ee},this.getBaseLayer=function(){return u!==null?u:d},this.getBinding=function(){return f===null&&b&&(f=new XRWebGLBinding(s,t)),f},this.getFrame=function(){return g},this.getSession=function(){return s},this.setSession=async function(ee){if(s=ee,s!==null){if(C=e.getRenderTarget(),s.addEventListener("select",te),s.addEventListener("selectstart",te),s.addEventListener("selectend",te),s.addEventListener("squeeze",te),s.addEventListener("squeezestart",te),s.addEventListener("squeezeend",te),s.addEventListener("end",re),s.addEventListener("inputsourceschange",Z),E.xrCompatible!==!0&&await t.makeXRCompatible(),x=e.getPixelRatio(),e.getSize(I),b&&"createProjectionLayer"in XRWebGLBinding.prototype){let xe=null,Pe=null,Re=null;E.depth&&(Re=E.stencil?t.DEPTH24_STENCIL8:t.DEPTH_COMPONENT24,xe=E.stencil?Ai:Xn,Pe=E.stencil?Is:Vn);let Je={colorFormat:t.RGBA8,depthFormat:Re,scaleFactor:r};f=this.getBinding(),u=f.createProjectionLayer(Je),s.updateRenderState({layers:[u]}),e.setPixelRatio(1),e.setSize(u.textureWidth,u.textureHeight,!1),y=new Vt(u.textureWidth,u.textureHeight,{format:In,type:xn,depthTexture:new vi(u.textureWidth,u.textureHeight,Pe,void 0,void 0,void 0,void 0,void 0,void 0,xe),stencilBuffer:E.stencil,colorSpace:e.outputColorSpace,samples:E.antialias?4:0,resolveDepthBuffer:u.ignoreDepthValues===!1,resolveStencilBuffer:u.ignoreDepthValues===!1,storeMultisampledDepthBuffer:u.ignoreDepthValues===!1,storeMultisampledStencilBuffer:u.ignoreDepthValues===!1})}else{let xe={antialias:E.antialias,alpha:!0,depth:E.depth,stencil:E.stencil,framebufferScaleFactor:r};d=new XRWebGLLayer(s,t,xe),s.updateRenderState({baseLayer:d}),e.setPixelRatio(1),e.setSize(d.framebufferWidth,d.framebufferHeight,!1),y=new Vt(d.framebufferWidth,d.framebufferHeight,{format:In,type:xn,colorSpace:e.outputColorSpace,stencilBuffer:E.stencil,resolveDepthBuffer:d.ignoreDepthValues===!1,resolveStencilBuffer:d.ignoreDepthValues===!1,storeMultisampledDepthBuffer:d.ignoreDepthValues===!1,storeMultisampledStencilBuffer:d.ignoreDepthValues===!1})}y.isXRRenderTarget=!0,this.setFoveation(l),c=null,a=await s.requestReferenceSpace(o),Xe.setContext(s),Xe.start(),n.isPresenting=!0,n.dispatchEvent({type:"sessionstart"})}},this.getEnvironmentBlendMode=function(){if(s!==null)return s.environmentBlendMode},this.getDepthTexture=function(){return m.getDepthTexture()};function Z(ee){for(let ne=0;ne<ee.removed.length;ne++){let xe=ee.removed[ne],Pe=T.indexOf(xe);Pe>=0&&(T[Pe]=null,w[Pe].disconnect(xe))}for(let ne=0;ne<ee.added.length;ne++){let xe=ee.added[ne],Pe=T.indexOf(xe);if(Pe===-1){for(let Je=0;Je<w.length;Je++)if(Je>=T.length){T.push(xe),Pe=Je;break}else if(T[Je]===null){T[Je]=xe,Pe=Je;break}if(Pe===-1)break}let Re=w[Pe];Re&&Re.connect(xe)}}let Q=new U,ce=new U;function se(ee,ne,xe){Q.setFromMatrixPosition(ne.matrixWorld),ce.setFromMatrixPosition(xe.matrixWorld);let Pe=Q.distanceTo(ce),Re=ne.projectionMatrix.elements,Je=xe.projectionMatrix.elements,dt=Re[14]/(Re[10]-1),it=Re[14]/(Re[10]+1),ot=(Re[9]+1)/Re[5],gt=(Re[9]-1)/Re[5],rt=(Re[8]-1)/Re[0],at=(Je[8]+1)/Je[0],Dt=dt*rt,Lt=dt*at,_t=Pe/(-rt+at),Tt=_t*-rt;if(ne.matrixWorld.decompose(ee.position,ee.quaternion,ee.scale),ee.translateX(Tt),ee.translateZ(_t),ee.matrixWorld.compose(ee.position,ee.quaternion,ee.scale),ee.matrixWorldInverse.copy(ee.matrixWorld).invert(),Re[10]===-1)ee.projectionMatrix.copy(ne.projectionMatrix),ee.projectionMatrixInverse.copy(ne.projectionMatrixInverse);else{let z=dt+_t,Et=it+_t,lt=Dt-Tt,P=Lt+(Pe-Tt),_=ot*it/Et*z,X=gt*it/Et*z;ee.projectionMatrix.makePerspective(lt,P,_,X,z,Et),ee.projectionMatrixInverse.copy(ee.projectionMatrix).invert()}}function Ge(ee,ne){ne===null?ee.matrixWorld.copy(ee.matrix):ee.matrixWorld.multiplyMatrices(ne.matrixWorld,ee.matrix),ee.matrixWorldInverse.copy(ee.matrixWorld).invert()}this.updateCamera=function(ee){if(s===null)return;let ne=ee.near,xe=ee.far;m.texture!==null&&(m.depthNear>0&&(ne=m.depthNear),m.depthFar>0&&(xe=m.depthFar)),Y.near=k.near=D.near=ne,Y.far=k.far=D.far=xe,(F!==Y.near||$!==Y.far)&&(s.updateRenderState({depthNear:Y.near,depthFar:Y.far}),F=Y.near,$=Y.far),Y.layers.mask=ee.layers.mask|6,D.layers.mask=Y.layers.mask&-5,k.layers.mask=Y.layers.mask&-3;let Pe=ee.parent,Re=Y.cameras;Ge(Y,Pe);for(let Je=0;Je<Re.length;Je++)Ge(Re[Je],Pe);Re.length===2?se(Y,D,k):Y.projectionMatrix.copy(D.projectionMatrix),A===null&&ee.isPerspectiveCamera&&(A={camera:ee,fov:ee.fov,zoom:ee.zoom}),Ce(ee,Y,Pe)};function Ce(ee,ne,xe){xe===null?ee.matrix.copy(ne.matrixWorld):(ee.matrix.copy(xe.matrixWorld),ee.matrix.invert(),ee.matrix.multiply(ne.matrixWorld)),ee.matrix.decompose(ee.position,ee.quaternion,ee.scale),ee.updateMatrixWorld(!0),ee.projectionMatrix.copy(ne.projectionMatrix),ee.projectionMatrixInverse.copy(ne.projectionMatrixInverse),ee.isPerspectiveCamera&&(ee.fov=_s*2*Math.atan(1/ee.projectionMatrix.elements[5]),ee.zoom=1)}this.getCamera=function(){return Y},this.getFoveation=function(){if(!(u===null&&d===null))return l},this.setFoveation=function(ee){l=ee,u!==null&&(u.fixedFoveation=ee),d!==null&&d.fixedFoveation!==void 0&&(d.fixedFoveation=ee)},this.hasDepthSensing=function(){return m.texture!==null},this.getDepthSensingMesh=function(){return m.getMesh(Y)},this.getCameraTexture=function(ee){return p[ee]};let ut=null;function Ze(ee,ne){if(h=ne.getViewerPose(c||a),g=ne,h!==null){let xe=h.views;d!==null&&(e.setRenderTargetFramebuffer(y,d.framebuffer),e.setRenderTarget(y));let Pe=!1;xe.length!==Y.cameras.length&&(Y.cameras.length=0,Pe=!0);for(let it=0;it<xe.length;it++){let ot=xe[it],gt=null;if(d!==null)gt=d.getViewport(ot);else{let at=f.getViewSubImage(u,ot);gt=at.viewport,it===0&&(e.setRenderTargetTextures(y,at.colorTexture,at.depthStencilTexture),e.setRenderTarget(y))}let rt=G[it];rt===void 0&&(rt=new Jt,rt.layers.enable(it),rt.viewport=new Ut,G[it]=rt),rt.matrix.fromArray(ot.transform.matrix),rt.matrix.decompose(rt.position,rt.quaternion,rt.scale),rt.projectionMatrix.fromArray(ot.projectionMatrix),rt.projectionMatrixInverse.copy(rt.projectionMatrix).invert(),rt.viewport.set(gt.x,gt.y,gt.width,gt.height),it===0&&(Y.matrix.copy(rt.matrix),Y.matrix.decompose(Y.position,Y.quaternion,Y.scale)),Pe===!0&&Y.cameras.push(rt)}let Re=s.enabledFeatures;if(Re&&Re.includes("depth-sensing")&&s.depthUsage=="gpu-optimized"&&b){f=n.getBinding();let it=f.getDepthInformation(xe[0]);it&&it.isValid&&it.texture&&m.init(it,s.renderState)}if(Re&&Re.includes("camera-access")&&b){e.state.unbindTexture(),f=n.getBinding();for(let it=0;it<xe.length;it++){let ot=xe[it].camera;if(ot){let gt=p[ot];gt||(gt=new mr,p[ot]=gt);let rt=f.getCameraImage(ot);gt.sourceTexture=rt}}}}for(let xe=0;xe<w.length;xe++){let Pe=T[xe],Re=w[xe];Pe!==null&&Re!==void 0&&Re.update(Pe,ne,c||a)}ut&&ut(ee,ne),ne.detectedPlanes&&n.dispatchEvent({type:"planesdetected",data:ne}),g=null}let Xe=new Th;Xe.setAnimationLoop(Ze),this.setAnimationLoop=function(ee){ut=ee},this.dispose=function(){}}},z0=new xt,Ph=new st;Ph.set(-1,0,0,0,1,0,0,0,1);function V0(i,e){function t(m,p){m.matrixAutoUpdate===!0&&m.updateMatrix(),p.value.copy(m.matrix)}function n(m,p){p.color.getRGB(m.fogColor.value,fc(i)),p.isFog?(m.fogNear.value=p.near,m.fogFar.value=p.far):p.isFogExp2&&(m.fogDensity.value=p.density)}function s(m,p,E,C,y){p.isNodeMaterial?p.uniformsNeedUpdate=!1:p.isMeshBasicMaterial?r(m,p):p.isMeshLambertMaterial?(r(m,p),p.envMap&&(m.envMapIntensity.value=p.envMapIntensity)):p.isMeshToonMaterial?(r(m,p),f(m,p)):p.isMeshPhongMaterial?(r(m,p),h(m,p),p.envMap&&(m.envMapIntensity.value=p.envMapIntensity)):p.isMeshStandardMaterial?(r(m,p),u(m,p),p.isMeshPhysicalMaterial&&d(m,p,y)):p.isMeshMatcapMaterial?(r(m,p),g(m,p)):p.isMeshDepthMaterial?r(m,p):p.isMeshDistanceMaterial?(r(m,p),b(m,p)):p.isMeshNormalMaterial?r(m,p):p.isLineBasicMaterial?(a(m,p),p.isLineDashedMaterial&&o(m,p)):p.isPointsMaterial?l(m,p,E,C):p.isSpriteMaterial?c(m,p):p.isShadowMaterial?(m.color.value.copy(p.color),m.opacity.value=p.opacity):p.isShaderMaterial&&(p.uniformsNeedUpdate=!1)}function r(m,p){m.opacity.value=p.opacity,p.color&&m.diffuse.value.copy(p.color),p.emissive&&m.emissive.value.copy(p.emissive).multiplyScalar(p.emissiveIntensity),p.map&&(m.map.value=p.map,t(p.map,m.mapTransform)),p.alphaMap&&(m.alphaMap.value=p.alphaMap,t(p.alphaMap,m.alphaMapTransform)),p.bumpMap&&(m.bumpMap.value=p.bumpMap,t(p.bumpMap,m.bumpMapTransform),m.bumpScale.value=p.bumpScale,p.side===en&&(m.bumpScale.value*=-1)),p.normalMap&&(m.normalMap.value=p.normalMap,t(p.normalMap,m.normalMapTransform),m.normalScale.value.copy(p.normalScale),p.side===en&&m.normalScale.value.negate()),p.displacementMap&&(m.displacementMap.value=p.displacementMap,t(p.displacementMap,m.displacementMapTransform),m.displacementScale.value=p.displacementScale,m.displacementBias.value=p.displacementBias),p.emissiveMap&&(m.emissiveMap.value=p.emissiveMap,t(p.emissiveMap,m.emissiveMapTransform)),p.specularMap&&(m.specularMap.value=p.specularMap,t(p.specularMap,m.specularMapTransform)),p.alphaTest>0&&(m.alphaTest.value=p.alphaTest);let E=e.get(p),C=E.envMap,y=E.envMapRotation;C&&(m.envMap.value=C,m.envMapRotation.value.setFromMatrix4(z0.makeRotationFromEuler(y)).transpose(),C.isCubeTexture&&C.isRenderTargetTexture===!1&&m.envMapRotation.value.premultiply(Ph),m.reflectivity.value=p.reflectivity,m.ior.value=p.ior,m.refractionRatio.value=p.refractionRatio),p.lightMap&&(m.lightMap.value=p.lightMap,m.lightMapIntensity.value=p.lightMapIntensity,t(p.lightMap,m.lightMapTransform)),p.aoMap&&(m.aoMap.value=p.aoMap,m.aoMapIntensity.value=p.aoMapIntensity,t(p.aoMap,m.aoMapTransform))}function a(m,p){m.diffuse.value.copy(p.color),m.opacity.value=p.opacity,p.map&&(m.map.value=p.map,t(p.map,m.mapTransform))}function o(m,p){m.dashSize.value=p.dashSize,m.totalSize.value=p.dashSize+p.gapSize,m.scale.value=p.scale}function l(m,p,E,C){m.diffuse.value.copy(p.color),m.opacity.value=p.opacity,m.size.value=p.size*E,m.scale.value=C*.5,p.map&&(m.map.value=p.map,t(p.map,m.uvTransform)),p.alphaMap&&(m.alphaMap.value=p.alphaMap,t(p.alphaMap,m.alphaMapTransform)),p.alphaTest>0&&(m.alphaTest.value=p.alphaTest)}function c(m,p){m.diffuse.value.copy(p.color),m.opacity.value=p.opacity,m.rotation.value=p.rotation,p.map&&(m.map.value=p.map,t(p.map,m.mapTransform)),p.alphaMap&&(m.alphaMap.value=p.alphaMap,t(p.alphaMap,m.alphaMapTransform)),p.alphaTest>0&&(m.alphaTest.value=p.alphaTest)}function h(m,p){m.specular.value.copy(p.specular),m.shininess.value=Math.max(p.shininess,1e-4)}function f(m,p){p.gradientMap&&(m.gradientMap.value=p.gradientMap)}function u(m,p){m.metalness.value=p.metalness,p.metalnessMap&&(m.metalnessMap.value=p.metalnessMap,t(p.metalnessMap,m.metalnessMapTransform)),m.roughness.value=p.roughness,p.roughnessMap&&(m.roughnessMap.value=p.roughnessMap,t(p.roughnessMap,m.roughnessMapTransform)),p.envMap&&(m.envMapIntensity.value=p.envMapIntensity)}function d(m,p,E){m.ior.value=p.ior,p.sheen>0&&(m.sheenColor.value.copy(p.sheenColor).multiplyScalar(p.sheen),m.sheenRoughness.value=p.sheenRoughness,p.sheenColorMap&&(m.sheenColorMap.value=p.sheenColorMap,t(p.sheenColorMap,m.sheenColorMapTransform)),p.sheenRoughnessMap&&(m.sheenRoughnessMap.value=p.sheenRoughnessMap,t(p.sheenRoughnessMap,m.sheenRoughnessMapTransform))),p.clearcoat>0&&(m.clearcoat.value=p.clearcoat,m.clearcoatRoughness.value=p.clearcoatRoughness,p.clearcoatMap&&(m.clearcoatMap.value=p.clearcoatMap,t(p.clearcoatMap,m.clearcoatMapTransform)),p.clearcoatRoughnessMap&&(m.clearcoatRoughnessMap.value=p.clearcoatRoughnessMap,t(p.clearcoatRoughnessMap,m.clearcoatRoughnessMapTransform)),p.clearcoatNormalMap&&(m.clearcoatNormalMap.value=p.clearcoatNormalMap,t(p.clearcoatNormalMap,m.clearcoatNormalMapTransform),m.clearcoatNormalScale.value.copy(p.clearcoatNormalScale),p.side===en&&m.clearcoatNormalScale.value.negate())),p.dispersion>0&&(m.dispersion.value=p.dispersion),p.retroreflectivity>0&&(m.retroreflectivity.value=p.retroreflectivity),p.iridescence>0&&(m.iridescence.value=p.iridescence,m.iridescenceIOR.value=p.iridescenceIOR,m.iridescenceThicknessMinimum.value=p.iridescenceThicknessRange[0],m.iridescenceThicknessMaximum.value=p.iridescenceThicknessRange[1],p.iridescenceMap&&(m.iridescenceMap.value=p.iridescenceMap,t(p.iridescenceMap,m.iridescenceMapTransform)),p.iridescenceThicknessMap&&(m.iridescenceThicknessMap.value=p.iridescenceThicknessMap,t(p.iridescenceThicknessMap,m.iridescenceThicknessMapTransform))),p.transmission>0&&(m.transmission.value=p.transmission,m.transmissionSamplerMap.value=E.texture,m.transmissionSamplerSize.value.set(E.width,E.height),p.transmissionMap&&(m.transmissionMap.value=p.transmissionMap,t(p.transmissionMap,m.transmissionMapTransform)),m.thickness.value=p.thickness,p.thicknessMap&&(m.thicknessMap.value=p.thicknessMap,t(p.thicknessMap,m.thicknessMapTransform)),m.attenuationDistance.value=p.attenuationDistance,m.attenuationColor.value.copy(p.attenuationColor)),p.anisotropy>0&&(m.anisotropyVector.value.set(p.anisotropy*Math.cos(p.anisotropyRotation),p.anisotropy*Math.sin(p.anisotropyRotation)),p.anisotropyMap&&(m.anisotropyMap.value=p.anisotropyMap,t(p.anisotropyMap,m.anisotropyMapTransform))),m.specularIntensity.value=p.specularIntensity,m.specularColor.value.copy(p.specularColor),p.specularColorMap&&(m.specularColorMap.value=p.specularColorMap,t(p.specularColorMap,m.specularColorMapTransform)),p.specularIntensityMap&&(m.specularIntensityMap.value=p.specularIntensityMap,t(p.specularIntensityMap,m.specularIntensityMapTransform))}function g(m,p){p.matcap&&(m.matcap.value=p.matcap)}function b(m,p){let E=e.get(p).light;m.referencePosition.value.setFromMatrixPosition(E.matrixWorld),m.nearDistance.value=E.shadow.camera.near,m.farDistance.value=E.shadow.camera.far}return{refreshFogUniforms:n,refreshMaterialUniforms:s}}function H0(i,e,t,n){let s={},r={},a=[],o=i.getParameter(i.MAX_UNIFORM_BUFFER_BINDINGS);function l(y,w){let T=w.program;n.uniformBlockBinding(y,T)}function c(y,w){let T=s[y.id];T===void 0&&(m(y),T=h(y),s[y.id]=T,y.addEventListener("dispose",E));let I=w.program;n.updateUBOMapping(y,I);let x=e.render.frame;r[y.id]!==x&&(u(y),r[y.id]=x)}function h(y){let w=f();y.__bindingPointIndex=w;let T=i.createBuffer(),I=y.__size,x=y.usage;return i.bindBuffer(i.UNIFORM_BUFFER,T),i.bufferData(i.UNIFORM_BUFFER,I,x),i.bindBuffer(i.UNIFORM_BUFFER,null),i.bindBufferBase(i.UNIFORM_BUFFER,w,T),T}function f(){for(let y=0;y<o;y++)if(a.indexOf(y)===-1)return a.push(y),y;return nt("WebGLRenderer: Maximum number of simultaneously usable uniforms groups reached."),0}function u(y){let w=s[y.id],T=y.uniforms,I=y.__cache;i.bindBuffer(i.UNIFORM_BUFFER,w);for(let x=0,A=T.length;x<A;x++){let D=T[x];if(Array.isArray(D))for(let k=0,G=D.length;k<G;k++)d(D[k],x,k,I);else d(D,x,0,I)}i.bindBuffer(i.UNIFORM_BUFFER,null)}function d(y,w,T,I){if(b(y,w,T,I)===!0){let x=y.__offset,A=y.value;if(Array.isArray(A)){let D=0;for(let k=0;k<A.length;k++){let G=A[k],Y=p(G);g(G,y.__data,D),typeof G!="number"&&typeof G!="boolean"&&!G.isMatrix3&&!ArrayBuffer.isView(G)&&(D+=Y.storage/Float32Array.BYTES_PER_ELEMENT)}}else g(A,y.__data,0);i.bufferSubData(i.UNIFORM_BUFFER,x,y.__data)}}function g(y,w,T){typeof y=="number"||typeof y=="boolean"?w[0]=y:y.isMatrix3?(w[0]=y.elements[0],w[1]=y.elements[1],w[2]=y.elements[2],w[3]=0,w[4]=y.elements[3],w[5]=y.elements[4],w[6]=y.elements[5],w[7]=0,w[8]=y.elements[6],w[9]=y.elements[7],w[10]=y.elements[8],w[11]=0):ArrayBuffer.isView(y)?w.set(new y.constructor(y.buffer,y.byteOffset,w.length)):y.toArray(w,T)}function b(y,w,T,I){let x=y.value,A=w+"_"+T;if(I[A]===void 0)return typeof x=="number"||typeof x=="boolean"?I[A]=x:ArrayBuffer.isView(x)?I[A]=x.slice():I[A]=x.clone(),!0;{let D=I[A];if(typeof x=="number"||typeof x=="boolean"){if(D!==x)return I[A]=x,!0}else{if(ArrayBuffer.isView(x))return!0;if(D.equals(x)===!1)return D.copy(x),!0}}return!1}function m(y){let w=y.uniforms,T=0,I=16;for(let A=0,D=w.length;A<D;A++){let k=Array.isArray(w[A])?w[A]:[w[A]];for(let G=0,Y=k.length;G<Y;G++){let F=k[G],$=Array.isArray(F.value)?F.value:[F.value];for(let te=0,re=$.length;te<re;te++){let Z=$[te],Q=p(Z),ce=T%I,se=ce%Q.boundary,Ge=ce+se;T+=se,Ge!==0&&I-Ge<Q.storage&&(T+=I-Ge),F.__data=new Float32Array(Q.storage/Float32Array.BYTES_PER_ELEMENT),F.__offset=T,T+=Q.storage}}}let x=T%I;return x>0&&(T+=I-x),y.__size=T,y.__cache={},this}function p(y){let w={boundary:0,storage:0};return typeof y=="number"||typeof y=="boolean"?(w.boundary=4,w.storage=4):y.isVector2?(w.boundary=8,w.storage=8):y.isVector3||y.isColor?(w.boundary=16,w.storage=12):y.isVector4?(w.boundary=16,w.storage=16):y.isMatrix3?(w.boundary=48,w.storage=48):y.isMatrix4?(w.boundary=64,w.storage=64):y.isTexture?je("WebGLRenderer: Texture samplers can not be part of an uniforms group."):ArrayBuffer.isView(y)?(w.boundary=16,w.storage=y.byteLength):je("WebGLRenderer: Unsupported uniform value type.",y),w}function E(y){let w=y.target;w.removeEventListener("dispose",E);let T=a.indexOf(w.__bindingPointIndex);a.splice(T,1),i.deleteBuffer(s[w.id]),delete s[w.id],delete r[w.id]}function C(){for(let y in s)i.deleteBuffer(s[y]);a=[],s={},r={}}return{bind:l,update:c,dispose:C}}var G0=new Uint16Array([12469,15057,12620,14925,13266,14620,13807,14376,14323,13990,14545,13625,14713,13328,14840,12882,14931,12528,14996,12233,15039,11829,15066,11525,15080,11295,15085,10976,15082,10705,15073,10495,13880,14564,13898,14542,13977,14430,14158,14124,14393,13732,14556,13410,14702,12996,14814,12596,14891,12291,14937,11834,14957,11489,14958,11194,14943,10803,14921,10506,14893,10278,14858,9960,14484,14039,14487,14025,14499,13941,14524,13740,14574,13468,14654,13106,14743,12678,14818,12344,14867,11893,14889,11509,14893,11180,14881,10751,14852,10428,14812,10128,14765,9754,14712,9466,14764,13480,14764,13475,14766,13440,14766,13347,14769,13070,14786,12713,14816,12387,14844,11957,14860,11549,14868,11215,14855,10751,14825,10403,14782,10044,14729,9651,14666,9352,14599,9029,14967,12835,14966,12831,14963,12804,14954,12723,14936,12564,14917,12347,14900,11958,14886,11569,14878,11247,14859,10765,14828,10401,14784,10011,14727,9600,14660,9289,14586,8893,14508,8533,15111,12234,15110,12234,15104,12216,15092,12156,15067,12010,15028,11776,14981,11500,14942,11205,14902,10752,14861,10393,14812,9991,14752,9570,14682,9252,14603,8808,14519,8445,14431,8145,15209,11449,15208,11451,15202,11451,15190,11438,15163,11384,15117,11274,15055,10979,14994,10648,14932,10343,14871,9936,14803,9532,14729,9218,14645,8742,14556,8381,14461,8020,14365,7603,15273,10603,15272,10607,15267,10619,15256,10631,15231,10614,15182,10535,15118,10389,15042,10167,14963,9787,14883,9447,14800,9115,14710,8665,14615,8318,14514,7911,14411,7507,14279,7198,15314,9675,15313,9683,15309,9712,15298,9759,15277,9797,15229,9773,15166,9668,15084,9487,14995,9274,14898,8910,14800,8539,14697,8234,14590,7790,14479,7409,14367,7067,14178,6621,15337,8619,15337,8631,15333,8677,15325,8769,15305,8871,15264,8940,15202,8909,15119,8775,15022,8565,14916,8328,14804,8009,14688,7614,14569,7287,14448,6888,14321,6483,14088,6171,15350,7402,15350,7419,15347,7480,15340,7613,15322,7804,15287,7973,15229,8057,15148,8012,15046,7846,14933,7611,14810,7357,14682,7069,14552,6656,14421,6316,14251,5948,14007,5528,15356,5942,15356,5977,15353,6119,15348,6294,15332,6551,15302,6824,15249,7044,15171,7122,15070,7050,14949,6861,14818,6611,14679,6349,14538,6067,14398,5651,14189,5311,13935,4958,15359,4123,15359,4153,15356,4296,15353,4646,15338,5160,15311,5508,15263,5829,15188,6042,15088,6094,14966,6001,14826,5796,14678,5543,14527,5287,14377,4985,14133,4586,13869,4257,15360,1563,15360,1642,15358,2076,15354,2636,15341,3350,15317,4019,15273,4429,15203,4732,15105,4911,14981,4932,14836,4818,14679,4621,14517,4386,14359,4156,14083,3795,13808,3437,15360,122,15360,137,15358,285,15355,636,15344,1274,15322,2177,15281,2765,15215,3223,15120,3451,14995,3569,14846,3567,14681,3466,14511,3305,14344,3121,14037,2800,13753,2467,15360,0,15360,1,15359,21,15355,89,15346,253,15325,479,15287,796,15225,1148,15133,1492,15008,1749,14856,1882,14685,1886,14506,1783,14324,1608,13996,1398,13702,1183]),Kn=null;function W0(){return Kn===null&&(Kn=new ur(G0,16,16,Ci,tn),Kn.name="DFG_LUT",Kn.minFilter=Qt,Kn.magFilter=Qt,Kn.wrapS=qn,Kn.wrapT=qn,Kn.generateMipmaps=!1,Kn.needsUpdate=!0),Kn}var sl=class{constructor(e={}){let{canvas:t=ju(),context:n=null,depth:s=!0,stencil:r=!1,alpha:a=!1,antialias:o=!1,premultipliedAlpha:l=!0,preserveDrawingBuffer:c=!1,powerPreference:h="default",failIfMajorPerformanceCaveat:f=!1,reversedDepthBuffer:u=!1,outputBufferType:d=xn}=e;this.isWebGLRenderer=!0;let g;if(n!==null){if(typeof WebGLRenderingContext<"u"&&n instanceof WebGLRenderingContext)throw new Error("THREE.WebGLRenderer: WebGL 1 is not supported since r163.");g=n.getContextAttributes().alpha}else g=a;let b=d,m=new Set([bo,yo,vo]),p=new Set([xn,Vn,Ps,Is,go,_o]),E=new Uint32Array(4),C=new Int32Array(4),y=new U,w=null,T=null,I=[],x=[],A=null;this.domElement=t,this.debug={checkShaderErrors:!0,diagnostics:{keywords:!1},onShaderError:null},this.autoClear=!0,this.autoClearColor=!0,this.autoClearDepth=!0,this.autoClearStencil=!0,this.sortObjects=!0,this.clippingPlanes=[],this.localClippingEnabled=!1,this.toneMapping=zn,this.toneMappingExposure=1,this.transmissionResolutionScale=1;let D=this,k=!1,G=null,Y=null,F=null,$=null;this._outputColorSpace=cn;let te=0,re=0,Z=null,Q=-1,ce=null,se=new Ut,Ge=new Ut,Ce=null,ut=new Qe(0),Ze=0,Xe=t.width,ee=t.height,ne=1,xe=null,Pe=null,Re=new Ut(0,0,Xe,ee),Je=new Ut(0,0,Xe,ee),dt=!1,it=new bs,ot=!1,gt=!1,rt=new xt,at=new U,Dt=new Ut,Lt={background:null,fog:null,environment:null,overrideMaterial:null,isScene:!0},_t=!1;function Tt(){return Z===null?ne:1}let z=n;function Et(v,L){return t.getContext(v,L)}let lt,P,_,X,K,ae,be,Ee,N,V,ie,ge,ue,pe,_e,Se,Be,O,Me,J,ve,we,fe;try{let v={alpha:!0,depth:s,stencil:r,antialias:o,premultipliedAlpha:l,preserveDrawingBuffer:c,powerPreference:h,failIfMajorPerformanceCaveat:f};if("setAttribute"in t&&t.setAttribute("data-engine",`three.js r${"186"}`),t.addEventListener("webglcontextlost",Ct,!1),t.addEventListener("webglcontextrestored",Mt,!1),t.addEventListener("webglcontextcreationerror",nn,!1),z===null){let L="webgl2";if(z=Et(L,v),z===null)throw Et(L)?new Error("THREE.WebGLRenderer: Error creating WebGL context with your selected attributes."):new Error("THREE.WebGLRenderer: Error creating WebGL context.")}We()}catch(v){throw t.removeEventListener("webglcontextlost",Ct,!1),t.removeEventListener("webglcontextrestored",Mt,!1),t.removeEventListener("webglcontextcreationerror",nn,!1),nt("WebGLRenderer: "+v.message),v}function We(){lt=new Jm(z),lt.init(),ve=new k0(z,lt),P=new Vm(z,lt,e,ve),_=new U0(z,lt),P.reversedDepthBuffer&&u&&_.buffers.depth.setReversed(!0),Y=z.createFramebuffer(),F=z.createFramebuffer(),$=z.createFramebuffer(),X=new eg(z),K=new b0,ae=new F0(z,lt,_,K,P,ve,X),be=new jm(D),Ee=new tf(z),we=new Bm(z,Ee),N=new Km(z,Ee,X,we),V=new ng(z,N,Ee,we,X),O=new tg(z,P,ae),_e=new Hm(K),ie=new y0(D,be,lt,P,we,_e),ge=new V0(D,K),ue=new S0,pe=new R0(lt),Be=new Om(D,be,_,V,g,l),Se=new D0(D,V,P),fe=new H0(z,X,P,_),Me=new zm(z,lt,X),J=new Qm(z,lt,X),X.programs=ie.programs,D.capabilities=P,D.extensions=lt,D.properties=K,D.renderLists=ue,D.shadowMap=Se,D.state=_,D.info=X}b!==xn&&(A=new sg(b,t.width,t.height,o,s,r));let Ve=new Ic(D,z);this.xr=Ve,this.getContext=function(){return z},this.getContextAttributes=function(){return z.getContextAttributes()},this.forceContextLoss=function(){let v=lt.get("WEBGL_lose_context");v&&v.loseContext()},this.forceContextRestore=function(){let v=lt.get("WEBGL_lose_context");v&&v.restoreContext()},this.getPixelRatio=function(){return ne},this.setPixelRatio=function(v){v!==void 0&&(ne=v,this.setSize(Xe,ee,!1))},this.getSize=function(v){return v.set(Xe,ee)},this.setSize=function(v,L,B=!0){if(Ve.isPresenting){je("WebGLRenderer: Can't change size while VR device is presenting.");return}Xe=v,ee=L,t.width=Math.floor(v*ne),t.height=Math.floor(L*ne),B===!0&&(t.style.width=v+"px",t.style.height=L+"px"),A!==null&&A.setSize(t.width,t.height),this.setViewport(0,0,v,L)},this.getDrawingBufferSize=function(v){return v.set(Xe*ne,ee*ne).floor()},this.setDrawingBufferSize=function(v,L,B){Xe=v,ee=L,ne=B,t.width=Math.floor(v*B),t.height=Math.floor(L*B),this.setViewport(0,0,v,L)},this.setEffects=function(v){if(b===xn){nt("WebGLRenderer: setEffects() requires outputBufferType set to HalfFloatType or FloatType.");return}if(v){for(let L=0;L<v.length;L++)if(v[L].isOutputPass===!0){je("WebGLRenderer: OutputPass is not needed in setEffects(). Tone mapping and color space conversion are applied automatically.");break}}A.setEffects(v||[])},this.getCurrentViewport=function(v){return v.copy(se)},this.getViewport=function(v){return v.copy(Re)},this.setViewport=function(v,L,B,H){v.isVector4?Re.set(v.x,v.y,v.z,v.w):Re.set(v,L,B,H),_.viewport(se.copy(Re).multiplyScalar(ne).round())},this.getScissor=function(v){return v.copy(Je)},this.setScissor=function(v,L,B,H){v.isVector4?Je.set(v.x,v.y,v.z,v.w):Je.set(v,L,B,H),_.scissor(Ge.copy(Je).multiplyScalar(ne).round())},this.getScissorTest=function(){return dt},this.setScissorTest=function(v){_.setScissorTest(dt=v)},this.setOpaqueSort=function(v){xe=v},this.setTransparentSort=function(v){Pe=v},this.getClearColor=function(v){return v.copy(Be.getClearColor())},this.setClearColor=function(){Be.setClearColor(...arguments)},this.getClearAlpha=function(){return Be.getClearAlpha()},this.setClearAlpha=function(){Be.setClearAlpha(...arguments)},this.clear=function(v=!0,L=!0,B=!0){let H=0;if(v){let q=!1;if(Z!==null){let Te=Z.texture.format;q=m.has(Te)}if(q){let Te=Z.texture.type,Ie=p.has(Te),Ae=Be.getClearColor(),Oe=Be.getClearAlpha(),ze=Ae.r,tt=Ae.g,$e=Ae.b;Ie?(E[0]=ze,E[1]=tt,E[2]=$e,E[3]=Oe,z.clearBufferuiv(z.COLOR,0,E)):(C[0]=ze,C[1]=tt,C[2]=$e,C[3]=Oe,z.clearBufferiv(z.COLOR,0,C))}else H|=z.COLOR_BUFFER_BIT}L&&(H|=z.DEPTH_BUFFER_BIT,this.state.buffers.depth.setMask(!0)),B&&(H|=z.STENCIL_BUFFER_BIT,this.state.buffers.stencil.setMask(4294967295)),H!==0&&z.clear(H)},this.clearColor=function(){this.clear(!0,!1,!1)},this.clearDepth=function(){this.clear(!1,!0,!1)},this.clearStencil=function(){this.clear(!1,!1,!0)},this.setNodesHandler=function(v){v.setRenderer(this),G=v},this.dispose=function(){t.removeEventListener("webglcontextlost",Ct,!1),t.removeEventListener("webglcontextrestored",Mt,!1),t.removeEventListener("webglcontextcreationerror",nn,!1),Be.dispose(),ue.dispose(),pe.dispose(),K.dispose(),be.dispose(),V.dispose(),we.dispose(),fe.dispose(),ie.dispose(),Ve.dispose(),Ve.removeEventListener("sessionstart",Ji),Ve.removeEventListener("sessionend",Qr),dn.stop()};function Ct(v){v.preventDefault(),uc("WebGLRenderer: Context Lost."),k=!0}function Mt(){uc("WebGLRenderer: Context Restored."),k=!1;let v=X.autoReset,L=Se.enabled,B=Se.autoUpdate,H=Se.needsUpdate,q=Se.type;We(),X.autoReset=v,Se.enabled=L,Se.autoUpdate=B,Se.needsUpdate=H,Se.type=q}function nn(v){nt("WebGLRenderer: A WebGL context could not be created. Reason: ",v.statusMessage)}function sn(v){let L=v.target;L.removeEventListener("dispose",sn),Hs(L)}function Hs(v){Gs(v),K.remove(v)}function Gs(v){let L=K.get(v).programs;L!==void 0&&(L.forEach(function(B){ie.releaseProgram(B)}),v.isShaderMaterial&&ie.releaseShaderCache(v))}this.renderBufferDirect=function(v,L,B,H,q,Te){L===null&&(L=Lt);let Ie=q.isMesh&&q.matrixWorld.determinantAffine()<0,Ae=Ne(v,L,B,H,q);_.setMaterial(H,Ie);let Oe=B.index,ze=1;if(H.wireframe===!0){if(Oe=N.getWireframeAttribute(B),Oe===void 0)return;ze=2}let tt=B.drawRange,$e=B.attributes.position,Ue=tt.start*ze,ft=(tt.start+tt.count)*ze;Te!==null&&(Ue=Math.max(Ue,Te.start*ze),ft=Math.min(ft,(Te.start+Te.count)*ze)),Oe!==null?(Ue=Math.max(Ue,0),ft=Math.min(ft,Oe.count)):$e!=null&&(Ue=Math.max(Ue,0),ft=Math.min(ft,$e.count));let Ye=ft-Ue;if(Ye<0||Ye===1/0)return;we.setup(q,H,Ae,B,Oe);let Ke,wt=Me;if(Oe!==null&&(Ke=Ee.get(Oe),wt=J,wt.setIndex(Ke)),q.isMesh)H.wireframe===!0?(_.setLineWidth(H.wireframeLinewidth*Tt()),wt.setMode(z.LINES)):wt.setMode(z.TRIANGLES);else if(q.isLine){let Ot=H.linewidth;Ot===void 0&&(Ot=1),_.setLineWidth(Ot*Tt()),q.isLineSegments?wt.setMode(z.LINES):q.isLineLoop?wt.setMode(z.LINE_LOOP):wt.setMode(z.LINE_STRIP)}else q.isPoints?wt.setMode(z.POINTS):q.isSprite&&wt.setMode(z.TRIANGLES);if(q.isBatchedMesh)if(lt.get("WEBGL_multi_draw"))wt.renderMultiDraw(q._multiDrawStarts,q._multiDrawCounts,q._multiDrawCount);else{let Ot=q._multiDrawStarts,Fe=q._multiDrawCounts,Xt=q._multiDrawCount,vt=Oe?Ee.get(Oe).bytesPerElement:1,fn=K.get(H).currentProgram.getUniforms();for(let pn=0;pn<Xt;pn++)fn.setValue(z,"_gl_DrawID",pn),wt.render(Ot[pn]/vt,Fe[pn])}else if(q.isInstancedMesh)wt.renderInstances(Ue,Ye,q.count);else if(B.isInstancedBufferGeometry){let Ot=B._maxInstanceCount!==void 0?B._maxInstanceCount:1/0,Fe=Math.min(B.instanceCount,Ot);wt.renderInstances(Ue,Ye,Fe)}else wt.render(Ue,Ye)};function di(v,L,B,H){G!==null&&v.isNodeMaterial&&G.setObject(H,v),ot===!0&&_e.setState(v,B,!1),v.transparent===!0&&v.side===Jn&&v.forceSinglePass===!1?(v.side=en,v.needsUpdate=!0,oe(v,L,H),v.side=Ti,v.needsUpdate=!0,oe(v,L,H),v.side=Jn):oe(v,L,H)}this.compile=function(v,L,B=null){B===null&&(B=v),G!==null&&G.renderStart(v,L,B),T=pe.get(B),T.init(L),x.push(T),B.traverseVisible(function(q){q.isLight&&q.layers.test(L.layers)&&(T.pushLight(q),q.castShadow&&T.pushShadow(q))}),v!==B&&v.traverseVisible(function(q){q.isLight&&q.layers.test(L.layers)&&(T.pushLight(q),q.castShadow&&T.pushShadow(q))}),T.setupLights(),G!==null&&G.updateLights(T.state.lightsArray),gt=this.localClippingEnabled,ot=_e.init(this.clippingPlanes,gt),ot===!0&&_e.setGlobalState(this.clippingPlanes,L),G!==null&&Se.render(T.state.shadowsArray,B,L);let H=new Set;return v.traverse(function(q){if(!(q.isMesh||q.isPoints||q.isLine||q.isSprite))return;let Te=q.material;if(Te)if(Array.isArray(Te))for(let Ie=0;Ie<Te.length;Ie++){let Ae=Te[Ie];di(Ae,B,L,q),H.add(Ae)}else di(Te,B,L,q),H.add(Te)}),T=x.pop(),G!==null&&G.renderEnd(),H},this.compileAsync=function(v,L,B=null){let H=this.compile(v,L,B);return new Promise(q=>{function Te(){if(H.forEach(function(Ie){let Oe=K.get(Ie).currentProgram;(Oe===void 0||Oe.isReady())&&H.delete(Ie)}),H.size===0){q(v);return}setTimeout(Te,10)}lt.get("KHR_parallel_shader_compile")!==null?Te():setTimeout(Te,10)})};let Li=null;function Ws(v){Li&&Li(v)}function Ji(){dn.stop()}function Qr(){dn.start()}let dn=new Th;dn.setAnimationLoop(Ws),typeof self<"u"&&dn.setContext(self),this.setAnimationLoop=function(v){Li=v,Ve.setAnimationLoop(v),v===null?dn.stop():dn.start()},Ve.addEventListener("sessionstart",Ji),Ve.addEventListener("sessionend",Qr),this.render=function(v,L){if(L!==void 0&&L.isCamera!==!0){nt("WebGLRenderer.render: camera is not an instance of THREE.Camera.");return}if(k===!0)return;G!==null&&G.renderStart(v,L);let B=Ve.enabled===!0&&Ve.isPresenting===!0,H=A!==null&&(Z===null||B)&&A.begin(D,Z);if(v.matrixWorldAutoUpdate===!0&&v.updateMatrixWorld(),L.parent===null&&L.matrixWorldAutoUpdate===!0&&L.updateMatrixWorld(),Ve.enabled===!0&&Ve.isPresenting===!0&&(A===null||A.isCompositing()===!1)&&(Ve.cameraAutoUpdate===!0&&Ve.updateCamera(L),L=Ve.getCamera()),v.isScene===!0&&v.onBeforeRender(D,v,L,Z),T=pe.get(v,x.length),T.init(L),T.state.textureUnits=ae.getTextureUnits(),x.push(T),rt.multiplyMatrices(L.projectionMatrix,L.matrixWorldInverse),it.setFromProjectionMatrix(rt,kn,L.reversedDepth),gt=this.localClippingEnabled,ot=_e.init(this.clippingPlanes,gt),w=ue.get(v,I.length),w.init(),I.push(w),Ve.enabled===!0&&Ve.isPresenting===!0){let Ie=D.xr.getDepthSensingMesh();Ie!==null&&M(Ie,L,-1/0,D.sortObjects)}M(v,L,0,D.sortObjects),w.finish(),G!==null&&G.updateLights(T.state.lightsArray),D.sortObjects===!0&&w.sort(xe,Pe),_t=Ve.enabled===!1||Ve.isPresenting===!1||Ve.hasDepthSensing()===!1,_t&&Be.addToRenderList(w,v),this.info.render.frame++,this.info.autoReset===!0&&this.info.reset(),ot===!0&&_e.beginShadows();let q=T.state.shadowsArray;if(Se.render(q,v,L),ot===!0&&_e.endShadows(),(H&&A.hasRenderPass())===!1){let Ie=w.opaque,Ae=w.transmissive;if(T.setupLights(),L.isArrayCamera){let Oe=L.cameras;if(Ae.length>0)for(let ze=0,tt=Oe.length;ze<tt;ze++){let $e=Oe[ze];S(Ie,Ae,v,$e)}_t&&Be.render(v);for(let ze=0,tt=Oe.length;ze<tt;ze++){let $e=Oe[ze];R(w,v,$e,$e.viewport)}}else Ae.length>0&&S(Ie,Ae,v,L),_t&&Be.render(v),R(w,v,L)}Z!==null&&re===0&&(ae.updateMultisampleRenderTarget(Z),ae.updateRenderTargetMipmap(Z)),H&&A.end(D),v.isScene===!0&&v.onAfterRender(D,v,L),we.resetDefaultState(),Q=-1,ce=null,x.pop(),x.length>0?(T=x[x.length-1],ae.setTextureUnits(T.state.textureUnits),ot===!0&&_e.setGlobalState(D.clippingPlanes,T.state.camera)):T=null,I.pop(),I.length>0?w=I[I.length-1]:w=null,G!==null&&G.renderEnd()};function M(v,L,B,H){if(v.visible===!1)return;if(v.layers.test(L.layers)){if(v.isGroup)B=v.renderOrder;else if(v.isLOD)v.autoUpdate===!0&&v.update(L);else if(v.isLightProbeGrid)T.pushLightProbeGrid(v);else if(v.isLight)T.pushLight(v),v.castShadow&&T.pushShadow(v);else if(v.isSprite){if(!v.frustumCulled||v.intersectsFrustum(it)){H&&Dt.setFromMatrixPosition(v.matrixWorld).applyMatrix4(rt);let Ie=V.update(v),Ae=v.material;Ae.visible&&w.push(v,Ie,Ae,B,Dt.z,null,L)}}else if((v.isMesh||v.isLine||v.isPoints)&&(!v.frustumCulled||v.intersectsFrustum(it))){let Ie=V.update(v),Ae=v.material;if(H&&(v.boundingSphere!==void 0?(v.boundingSphere===null&&v.computeBoundingSphere(),Dt.copy(v.boundingSphere.center)):(Ie.boundingSphere===null&&Ie.computeBoundingSphere(),Dt.copy(Ie.boundingSphere.center)),Dt.applyMatrix4(v.matrixWorld).applyMatrix4(rt)),Array.isArray(Ae)){let Oe=Ie.groups;for(let ze=0,tt=Oe.length;ze<tt;ze++){let $e=Oe[ze],Ue=Ae[$e.materialIndex];Ue&&Ue.visible&&w.push(v,Ie,Ue,B,Dt.z,$e,L)}}else Ae.visible&&w.push(v,Ie,Ae,B,Dt.z,null,L)}}let Te=v.children;for(let Ie=0,Ae=Te.length;Ie<Ae;Ie++)M(Te[Ie],L,B,H)}function R(v,L,B,H){let{opaque:q,transmissive:Te,transparent:Ie}=v;T.setupLightsView(B),ot===!0&&_e.setGlobalState(D.clippingPlanes,B),H&&_.viewport(se.copy(H)),q.length>0&&W(q,L,B),Te.length>0&&W(Te,L,B),Ie.length>0&&W(Ie,L,B),_.buffers.depth.setTest(!0),_.buffers.depth.setMask(!0),_.buffers.color.setMask(!0),_.setPolygonOffset(!1)}function S(v,L,B,H){if((B.isScene===!0?B.overrideMaterial:null)!==null)return;if(T.state.transmissionRenderTarget[H.id]===void 0){let Ue=lt.has("EXT_color_buffer_half_float")||lt.has("EXT_color_buffer_float");T.state.transmissionRenderTarget[H.id]=new Vt(1,1,{generateMipmaps:!0,type:Ue?tn:xn,minFilter:wi,samples:Math.max(4,P.samples),stencilBuffer:r,resolveDepthBuffer:!1,resolveStencilBuffer:!1,storeMultisampledDepthBuffer:!1,storeMultisampledStencilBuffer:!1,colorSpace:pt.workingColorSpace})}let Te=T.state.transmissionRenderTarget[H.id],Ie=H.viewport||se;Te.setSize(Ie.z*D.transmissionResolutionScale,Ie.w*D.transmissionResolutionScale);let Ae=D.getRenderTarget(),Oe=D.getActiveCubeFace(),ze=D.getActiveMipmapLevel();D.setRenderTarget(Te),D.getClearColor(ut),Ze=D.getClearAlpha(),Ze<1&&D.setClearColor(16777215,.5),D.clear(),_t&&Be.render(B);let tt=D.toneMapping;D.toneMapping=zn;let $e=H.viewport;if(H.viewport!==void 0&&(H.viewport=void 0),T.setupLightsView(H),ot===!0&&_e.setGlobalState(D.clippingPlanes,H),W(v,B,H),ae.updateMultisampleRenderTarget(Te),ae.updateRenderTargetMipmap(Te),lt.has("WEBGL_multisampled_render_to_texture")===!1){let Ue=!1;for(let ft=0,Ye=L.length;ft<Ye;ft++){let Ke=L[ft],{object:wt,geometry:Ot,material:Fe,group:Xt}=Ke;if(Fe.side===Jn&&wt.layers.test(H.layers)){let vt=Fe.side;Fe.side=en,Fe.needsUpdate=!0,de(wt,B,H,Ot,Fe,Xt),Fe.side=vt,Fe.needsUpdate=!0,Ue=!0}}Ue===!0&&(ae.updateMultisampleRenderTarget(Te),ae.updateRenderTargetMipmap(Te))}D.setRenderTarget(Ae,Oe,ze),D.setClearColor(ut,Ze),$e!==void 0&&(H.viewport=$e),D.toneMapping=tt}function W(v,L,B){let H=L.isScene===!0?L.overrideMaterial:null;for(let q=0,Te=v.length;q<Te;q++){let Ie=v[q],{object:Ae,geometry:Oe,group:ze}=Ie,tt=Ie.material;tt.allowOverride===!0&&H!==null&&(tt=H),Ae.layers.test(B.layers)&&de(Ae,L,B,Oe,tt,ze)}}function de(v,L,B,H,q,Te){G!==null&&q.isNodeMaterial&&G.setObject(v,q),v.onBeforeRender(D,L,B,H,q,Te),v.modelViewMatrix.multiplyMatrices(B.matrixWorldInverse,v.matrixWorld),v.normalMatrix.getNormalMatrix(v.modelViewMatrix),q.onBeforeRender(D,L,B,H,v,Te),q.transparent===!0&&q.side===Jn&&q.forceSinglePass===!1?(q.side=en,q.needsUpdate=!0,D.renderBufferDirect(B,L,H,q,v,Te),q.side=Ti,q.needsUpdate=!0,D.renderBufferDirect(B,L,H,q,v,Te),q.side=Jn):D.renderBufferDirect(B,L,H,q,v,Te),v.onAfterRender(D,L,B,H,q,Te)}function oe(v,L,B){L.isScene!==!0&&(L=Lt);let H=K.get(v),q=T.state.lights,Te=T.state.shadowsArray,Ie=q.state.version,Ae=ie.getParameters(v,q.state,Te,L,B,T.state.lightProbeGridArray),Oe=ie.getProgramCacheKey(Ae),ze=H.programs;H.environment=v.isMeshStandardMaterial||v.isMeshLambertMaterial||v.isMeshPhongMaterial?L.environment:null,H.fog=L.fog;let tt=v.isMeshStandardMaterial||v.isMeshLambertMaterial&&!v.envMap||v.isMeshPhongMaterial&&!v.envMap;H.envMap=be.get(v.envMap||H.environment,tt),H.envMapRotation=H.environment!==null&&v.envMap===null?L.environmentRotation:v.envMapRotation,ze===void 0&&(v.addEventListener("dispose",sn),ze=new Map,H.programs=ze);let $e=ze.get(Oe);if($e!==void 0){if(H.currentProgram===$e&&H.lightsStateVersion===Ie)return he(v,Ae),$e}else Ae.uniforms=ie.getUniforms(v),G!==null&&v.isNodeMaterial&&G.build(v,B,Ae),v.onBeforeCompile(Ae,D),$e=ie.acquireProgram(Ae,Oe),ze.set(Oe,$e),H.uniforms=Ae.uniforms;let Ue=H.uniforms;return(!v.isShaderMaterial&&!v.isRawShaderMaterial||v.clipping===!0)&&(Ue.clippingPlanes=_e.uniform),he(v,Ae),H.needsLights=j(v),H.lightsStateVersion=Ie,H.needsLights&&(Ue.ambientLightColor.value=q.state.ambient,Ue.lightProbe.value=q.state.probe,Ue.sunLights.value=q.state.sun,Ue.sunLightShadows.value=q.state.sunShadow,Ue.directionalLights.value=q.state.directional,Ue.directionalLightShadows.value=q.state.directionalShadow,Ue.spotLights.value=q.state.spot,Ue.spotLightShadows.value=q.state.spotShadow,Ue.rectAreaLights.value=q.state.rectArea,Ue.ltc_1.value=q.state.rectAreaLTC1,Ue.ltc_2.value=q.state.rectAreaLTC2,Ue.pointLights.value=q.state.point,Ue.pointLightShadows.value=q.state.pointShadow,Ue.hemisphereLights.value=q.state.hemi,Ue.sunShadowMatrix.value=q.state.sunShadowMatrix,Ue.sunShadowCascade.value=q.state.sunShadowCascade,Ue.directionalShadowMatrix.value=q.state.directionalShadowMatrix,Ue.spotLightMatrix.value=q.state.spotLightMatrix,Ue.spotLightMap.value=q.state.spotLightMap,Ue.pointShadowMatrix.value=q.state.pointShadowMatrix),H.lightProbeGrid=T.state.lightProbeGridArray.length>0,H.currentProgram=$e,H.uniformsList=null,$e}function le(v){if(v.uniformsList===null){let L=v.currentProgram.getUniforms();v.uniformsList=Us.seqWithValue(L.seq,v.uniforms)}return v.uniformsList}function he(v,L){let B=K.get(v);B.outputColorSpace=L.outputColorSpace,B.batching=L.batching,B.batchingColor=L.batchingColor,B.instancing=L.instancing,B.instancingColor=L.instancingColor,B.instancingMorph=L.instancingMorph,B.skinning=L.skinning,B.morphTargets=L.morphTargets,B.morphNormals=L.morphNormals,B.morphColors=L.morphColors,B.morphTargetsCount=L.morphTargetsCount,B.numClippingPlanes=L.numClippingPlanes,B.numIntersection=L.numClipIntersection,B.vertexAlphas=L.vertexAlphas,B.vertexTangents=L.vertexTangents,B.toneMapping=L.toneMapping}function ke(v,L){if(v.length===0)return null;if(v.length===1)return v[0].texture!==null?v[0]:null;y.setFromMatrixPosition(L.matrixWorld);for(let B=0,H=v.length;B<H;B++){let q=v[B];if(q.texture!==null&&q.boundingBox.containsPoint(y))return q}return null}function Ne(v,L,B,H,q){L.isScene!==!0&&(L=Lt),ae.resetTextureUnits();let Te=L.fog,Ie=H.isMeshStandardMaterial||H.isMeshLambertMaterial||H.isMeshPhongMaterial?L.environment:null,Ae=Z===null?D.outputColorSpace:Z.isXRRenderTarget===!0?Z.texture.colorSpace:pt.workingColorSpace,Oe=H.isMeshStandardMaterial||H.isMeshLambertMaterial&&!H.envMap||H.isMeshPhongMaterial&&!H.envMap,ze=be.get(H.envMap||Ie,Oe),tt=H.vertexColors===!0&&!!B.attributes.color&&B.attributes.color.itemSize===4,$e=!!B.attributes.tangent&&(!!H.normalMap||H.anisotropy>0),Ue=!!B.morphAttributes.position,ft=!!B.morphAttributes.normal,Ye=!!B.morphAttributes.color,Ke=zn;H.toneMapped&&(Z===null||Z.isXRRenderTarget===!0)&&(Ke=D.toneMapping);let wt=B.morphAttributes.position||B.morphAttributes.normal||B.morphAttributes.color,Ot=wt!==void 0?wt.length:0,Fe=K.get(H),Xt=T.state.lights;if(ot===!0&&(gt===!0||v!==ce)){let At=v===ce&&H.id===Q;_e.setState(H,v,At)}let vt=!1;H.version===Fe.__version?(Fe.needsLights&&Fe.lightsStateVersion!==Xt.state.version||Fe.outputColorSpace!==Ae||q.isBatchedMesh&&Fe.batching===!1||!q.isBatchedMesh&&Fe.batching===!0||q.isBatchedMesh&&Fe.batchingColor===!0&&q._colorsTexture===null||q.isBatchedMesh&&Fe.batchingColor===!1&&q._colorsTexture!==null||q.isInstancedMesh&&Fe.instancing===!1||!q.isInstancedMesh&&Fe.instancing===!0||q.isSkinnedMesh&&Fe.skinning===!1||!q.isSkinnedMesh&&Fe.skinning===!0||q.isInstancedMesh&&Fe.instancingColor===!0&&q.instanceColor===null||q.isInstancedMesh&&Fe.instancingColor===!1&&q.instanceColor!==null||q.isInstancedMesh&&Fe.instancingMorph===!0&&q.morphTexture===null||q.isInstancedMesh&&Fe.instancingMorph===!1&&q.morphTexture!==null||Fe.envMap!==ze||H.fog===!0&&Fe.fog!==Te||Fe.numClippingPlanes!==void 0&&(Fe.numClippingPlanes!==_e.numPlanes||Fe.numIntersection!==_e.numIntersection)||Fe.vertexAlphas!==tt||Fe.vertexTangents!==$e||Fe.morphTargets!==Ue||Fe.morphNormals!==ft||Fe.morphColors!==Ye||Fe.toneMapping!==Ke||Fe.morphTargetsCount!==Ot||!!Fe.lightProbeGrid!=T.state.lightProbeGridArray.length>0)&&(vt=!0):(vt=!0,Fe.__version=H.version);let fn=Fe.currentProgram;vt===!0&&(fn=oe(H,L,q),G&&H.isNodeMaterial&&G.onUpdateProgram(H,fn,Fe));let pn=!1,Ln=!1,me=!1,He=fn.getUniforms(),It=Fe.uniforms;if(_.useProgram(fn.program)&&(pn=!0,Ln=!0,me=!0),H.id!==Q&&(Q=H.id,Ln=!0),Fe.needsLights){let At=ke(T.state.lightProbeGridArray,q);Fe.lightProbeGrid!==At&&(Fe.lightProbeGrid=At,Ln=!0)}if(pn||ce!==v){_.buffers.depth.getReversed()&&v.reversedDepth!==!0&&(v._reversedDepth=!0,v.updateProjectionMatrix()),He.setValue(z,"projectionMatrix",v.projectionMatrix),He.setValue(z,"viewMatrix",v.matrixWorldInverse);let Tn=He.map.cameraPosition;Tn!==void 0&&Tn.setValue(z,at.setFromMatrixPosition(v.matrixWorld)),P.logarithmicDepthBuffer&&He.setValue(z,"logDepthBufFC",2/(Math.log(v.far+1)/Math.LN2)),(H.isMeshPhongMaterial||H.isMeshToonMaterial||H.isMeshLambertMaterial||H.isMeshBasicMaterial||H.isMeshStandardMaterial||H.isShaderMaterial)&&He.setValue(z,"isOrthographic",v.isOrthographicCamera===!0),ce!==v&&(ce=v,Ln=!0,me=!0)}if(Fe.needsLights&&(Xt.state.sunShadowMap.length>0&&He.setValue(z,"sunShadowMap",Xt.state.sunShadowMap,ae),Xt.state.directionalShadowMap.length>0&&He.setValue(z,"directionalShadowMap",Xt.state.directionalShadowMap,ae),Xt.state.spotShadowMap.length>0&&He.setValue(z,"spotShadowMap",Xt.state.spotShadowMap,ae),Xt.state.pointShadowMap.length>0&&He.setValue(z,"pointShadowMap",Xt.state.pointShadowMap,ae)),q.isSkinnedMesh){He.setOptional(z,q,"bindMatrix"),He.setOptional(z,q,"bindMatrixInverse");let At=q.skeleton;At&&(At.boneTexture===null&&At.computeBoneTexture(),He.setValue(z,"boneTexture",At.boneTexture,ae))}q.isBatchedMesh&&(He.setOptional(z,q,"batchingTexture"),He.setValue(z,"batchingTexture",q._matricesTexture,ae),He.setOptional(z,q,"batchingIdTexture"),He.setValue(z,"batchingIdTexture",q._indirectTexture,ae),He.setOptional(z,q,"batchingColorTexture"),q._colorsTexture!==null&&He.setValue(z,"batchingColorTexture",q._colorsTexture,ae));let Hn=B.morphAttributes;if((Hn.position!==void 0||Hn.normal!==void 0||Hn.color!==void 0)&&O.update(q,B,fn),(Ln||Fe.receiveShadow!==q.receiveShadow)&&(Fe.receiveShadow=q.receiveShadow,He.setValue(z,"receiveShadow",q.receiveShadow)),(H.isMeshStandardMaterial||H.isMeshLambertMaterial||H.isMeshPhongMaterial)&&H.envMap===null&&L.environment!==null&&(It.envMapIntensity.value=L.environmentIntensity),It.dfgLUT!==void 0&&(It.dfgLUT.value=W0()),Ln){if(He.setValue(z,"toneMappingExposure",D.toneMappingExposure),Fe.needsLights&&qe(It,me),Te&&H.fog===!0&&ge.refreshFogUniforms(It,Te),ge.refreshMaterialUniforms(It,H,ne,ee,T.state.transmissionRenderTarget[v.id]),Fe.needsLights&&Fe.lightProbeGrid){let At=Fe.lightProbeGrid;It.probesSH.value=At.texture,It.probesMin.value.copy(At.boundingBox.min),It.probesMax.value.copy(At.boundingBox.max),It.probesResolution.value.copy(At.resolution)}Us.upload(z,le(Fe),It,ae)}if(H.isShaderMaterial&&H.uniformsNeedUpdate===!0&&(Us.upload(z,le(Fe),It,ae),H.uniformsNeedUpdate=!1),H.isSpriteMaterial&&He.setValue(z,"center",q.center),He.setValue(z,"modelViewMatrix",q.modelViewMatrix),He.setValue(z,"normalMatrix",q.normalMatrix),He.setValue(z,"modelMatrix",q.matrixWorld),H.uniformsGroups!==void 0){let At=H.uniformsGroups;for(let Tn=0,Gn=At.length;Tn<Gn;Tn++){let Fc=At[Tn];fe.update(Fc,fn),fe.bind(Fc,fn)}}return fn}function qe(v,L){v.ambientLightColor.needsUpdate=L,v.lightProbe.needsUpdate=L,v.sunLights.needsUpdate=L,v.sunLightShadows.needsUpdate=L,v.directionalLights.needsUpdate=L,v.directionalLightShadows.needsUpdate=L,v.pointLights.needsUpdate=L,v.pointLightShadows.needsUpdate=L,v.spotLights.needsUpdate=L,v.spotLightShadows.needsUpdate=L,v.rectAreaLights.needsUpdate=L,v.hemisphereLights.needsUpdate=L}function j(v){return v.isMeshLambertMaterial||v.isMeshToonMaterial||v.isMeshPhongMaterial||v.isMeshStandardMaterial||v.isShadowMaterial||v.isShaderMaterial&&v.lights===!0}this.getActiveCubeFace=function(){return te},this.getActiveMipmapLevel=function(){return re},this.getRenderTarget=function(){return Z},this.setRenderTargetTextures=function(v,L,B){let H=K.get(v);H.__autoAllocateDepthBuffer=v.resolveDepthBuffer===!1,H.__autoAllocateDepthBuffer===!1&&(H.__useRenderToTexture=!1),K.get(v.texture).__webglTexture=L,K.get(v.depthTexture).__webglTexture=H.__autoAllocateDepthBuffer?void 0:B,H.__hasExternalTextures=!0},this.setRenderTargetFramebuffer=function(v,L){let B=K.get(v);B.__webglFramebuffer=L,B.__useDefaultFramebuffer=L===void 0},this.setRenderTarget=function(v,L=0,B=0){Z=v,te=L,re=B;let H=null,q=!1,Te=!1;if(v){let Ae=K.get(v);if(Ae.__useDefaultFramebuffer!==void 0){_.bindFramebuffer(z.FRAMEBUFFER,Ae.__webglFramebuffer),se.copy(v.viewport),Ge.copy(v.scissor),Ce=v.scissorTest,_.viewport(se),_.scissor(Ge),_.setScissorTest(Ce),Q=-1;return}else if(Ae.__webglFramebuffer===void 0)ae.setupRenderTarget(v);else if(Ae.__hasExternalTextures)ae.rebindTextures(v,K.get(v.texture).__webglTexture,K.get(v.depthTexture).__webglTexture);else if(v.depthBuffer){let tt=v.depthTexture;if(Ae.__boundDepthTexture!==tt){if(tt!==null&&K.has(tt)&&(v.width!==tt.image.width||v.height!==tt.image.height))throw new Error("THREE.WebGLRenderer: Attached DepthTexture is initialized to the incorrect size.");ae.setupDepthRenderbuffer(v)}}let Oe=v.texture;(Oe.isData3DTexture||Oe.isDataArrayTexture||Oe.isCompressedArrayTexture)&&(Te=!0);let ze=K.get(v).__webglFramebuffer;v.isWebGLCubeRenderTarget?(Array.isArray(ze[L])?H=ze[L][B]:H=ze[L],q=!0):v.samples>0&&ae.useMultisampledRTT(v)===!1?H=K.get(v).__webglMultisampledFramebuffer:Array.isArray(ze)?H=ze[B]:H=ze,se.copy(v.viewport),Ge.copy(v.scissor),Ce=v.scissorTest}else se.copy(Re).multiplyScalar(ne).floor(),Ge.copy(Je).multiplyScalar(ne).floor(),Ce=dt;if(B!==0&&(H=Y),_.bindFramebuffer(z.FRAMEBUFFER,H)&&_.drawBuffers(v,H),_.viewport(se),_.scissor(Ge),_.setScissorTest(Ce),q){let Ae=K.get(v.texture);z.framebufferTexture2D(z.FRAMEBUFFER,z.COLOR_ATTACHMENT0,z.TEXTURE_CUBE_MAP_POSITIVE_X+L,Ae.__webglTexture,B)}else if(Te){let Ae=L;for(let Oe=0;Oe<v.textures.length;Oe++){let ze=K.get(v.textures[Oe]);z.framebufferTextureLayer(z.FRAMEBUFFER,z.COLOR_ATTACHMENT0+Oe,ze.__webglTexture,B,Ae)}}else if(v!==null&&B!==0){let Ae=K.get(v.texture);z.framebufferTexture2D(z.FRAMEBUFFER,z.COLOR_ATTACHMENT0,z.TEXTURE_2D,Ae.__webglTexture,B)}Q=-1};function et(v){let L=K.get(v);return(L.__readFormat!==v.format||L.__readType!==v.type)&&(L.__readFormat=v.format,L.__readType=v.type,L.__formatReadable=P.textureFormatReadable(v.format),L.__typeReadable=P.textureTypeReadable(v.type)),L}this.readRenderTargetPixels=function(v,L,B,H,q,Te,Ie,Ae=0){if(!(v&&v.isWebGLRenderTarget)){nt("WebGLRenderer.readRenderTargetPixels: renderTarget is not THREE.WebGLRenderTarget.");return}let Oe=K.get(v).__webglFramebuffer;if(v.isWebGLCubeRenderTarget&&Ie!==void 0&&(Oe=Oe[Ie]),Oe){_.bindFramebuffer(z.FRAMEBUFFER,Oe);try{let ze=v.textures[Ae],tt=ze.format,$e=ze.type;v.textures.length>1&&z.readBuffer(z.COLOR_ATTACHMENT0+Ae);let Ue=et(ze);if(Ue.__formatReadable===!1){nt("WebGLRenderer.readRenderTargetPixels: renderTarget is not in RGBA or implementation defined format.");return}if(Ue.__typeReadable===!1){nt("WebGLRenderer.readRenderTargetPixels: renderTarget is not in UnsignedByteType or implementation defined type.");return}L>=0&&L<=v.width-H&&B>=0&&B<=v.height-q&&z.readPixels(L,B,H,q,ve.convert(tt),ve.convert($e),Te)}finally{let ze=Z!==null?K.get(Z).__webglFramebuffer:null;_.bindFramebuffer(z.FRAMEBUFFER,ze)}}},this.readRenderTargetPixelsAsync=async function(v,L,B,H,q,Te,Ie,Ae=0){if(!(v&&v.isWebGLRenderTarget))throw new Error("THREE.WebGLRenderer.readRenderTargetPixels: renderTarget is not THREE.WebGLRenderTarget.");let Oe=K.get(v).__webglFramebuffer;if(v.isWebGLCubeRenderTarget&&Ie!==void 0&&(Oe=Oe[Ie]),Oe)if(L>=0&&L<=v.width-H&&B>=0&&B<=v.height-q){_.bindFramebuffer(z.FRAMEBUFFER,Oe);let ze=v.textures[Ae],tt=ze.format,$e=ze.type;v.textures.length>1&&z.readBuffer(z.COLOR_ATTACHMENT0+Ae);let Ue=et(ze);if(Ue.__formatReadable===!1)throw new Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: renderTarget is not in RGBA or implementation defined format.");if(Ue.__typeReadable===!1)throw new Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: renderTarget is not in UnsignedByteType or implementation defined type.");let ft=z.createBuffer();z.bindBuffer(z.PIXEL_PACK_BUFFER,ft),z.bufferData(z.PIXEL_PACK_BUFFER,Te.byteLength,z.STREAM_READ),z.readPixels(L,B,H,q,ve.convert(tt),ve.convert($e),0),z.bindBuffer(z.PIXEL_PACK_BUFFER,null);let Ye=Z!==null?K.get(Z).__webglFramebuffer:null;_.bindFramebuffer(z.FRAMEBUFFER,Ye);let Ke=z.fenceSync(z.SYNC_GPU_COMMANDS_COMPLETE,0);return z.flush(),await Ku(z,Ke,4),z.bindBuffer(z.PIXEL_PACK_BUFFER,ft),z.getBufferSubData(z.PIXEL_PACK_BUFFER,0,Te),z.bindBuffer(z.PIXEL_PACK_BUFFER,null),z.deleteBuffer(ft),z.deleteSync(Ke),Te}else throw new Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: requested read bounds are out of range.")},this.copyFramebufferToTexture=function(v,L=null,B=0){let H=Math.pow(2,-B),q=Math.floor(v.image.width*H),Te=Math.floor(v.image.height*H),Ie=L!==null?L.x:0,Ae=L!==null?L.y:0;ae.setTexture2D(v,0),z.copyTexSubImage2D(z.TEXTURE_2D,B,0,0,Ie,Ae,q,Te),_.unbindTexture()},this.copyTextureToTexture=function(v,L,B=null,H=null,q=0,Te=0){let Ie,Ae,Oe,ze,tt,$e,Ue,ft,Ye,Ke=v.isCompressedTexture?v.mipmaps[Te]:v.image;if(B!==null)Ie=B.max.x-B.min.x,Ae=B.max.y-B.min.y,Oe=B.isBox3?B.max.z-B.min.z:1,ze=B.min.x,tt=B.min.y,$e=B.isBox3?B.min.z:0;else{let It=Math.pow(2,-q);Ie=Math.floor(Ke.width*It),Ae=Math.floor(Ke.height*It),v.isDataArrayTexture?Oe=Ke.depth:v.isData3DTexture?Oe=Math.floor(Ke.depth*It):Oe=1,ze=0,tt=0,$e=0}H!==null?(Ue=H.x,ft=H.y,Ye=H.z):(Ue=0,ft=0,Ye=0);let wt=ve.convert(L.format),Ot=ve.convert(L.type),Fe;L.isData3DTexture?(ae.setTexture3D(L,0),Fe=z.TEXTURE_3D):L.isDataArrayTexture||L.isCompressedArrayTexture?(ae.setTexture2DArray(L,0),Fe=z.TEXTURE_2D_ARRAY):(ae.setTexture2D(L,0),Fe=z.TEXTURE_2D),_.activeTexture(z.TEXTURE0),_.pixelStorei(z.UNPACK_FLIP_Y_WEBGL,L.flipY),_.pixelStorei(z.UNPACK_PREMULTIPLY_ALPHA_WEBGL,L.premultiplyAlpha),_.pixelStorei(z.UNPACK_ALIGNMENT,L.unpackAlignment);let Xt=_.getParameter(z.UNPACK_ROW_LENGTH),vt=_.getParameter(z.UNPACK_IMAGE_HEIGHT),fn=_.getParameter(z.UNPACK_SKIP_PIXELS),pn=_.getParameter(z.UNPACK_SKIP_ROWS),Ln=_.getParameter(z.UNPACK_SKIP_IMAGES);_.pixelStorei(z.UNPACK_ROW_LENGTH,Ke.width),_.pixelStorei(z.UNPACK_IMAGE_HEIGHT,Ke.height),_.pixelStorei(z.UNPACK_SKIP_PIXELS,ze),_.pixelStorei(z.UNPACK_SKIP_ROWS,tt),_.pixelStorei(z.UNPACK_SKIP_IMAGES,$e);let me=v.isDataArrayTexture||v.isData3DTexture,He=L.isDataArrayTexture||L.isData3DTexture;if(v.isDepthTexture){let It=K.get(v),Hn=K.get(L),At=K.get(It.__renderTarget),Tn=K.get(Hn.__renderTarget);_.bindFramebuffer(z.READ_FRAMEBUFFER,At.__webglFramebuffer),_.bindFramebuffer(z.DRAW_FRAMEBUFFER,Tn.__webglFramebuffer);for(let Gn=0;Gn<Oe;Gn++)me&&(z.framebufferTextureLayer(z.READ_FRAMEBUFFER,z.COLOR_ATTACHMENT0,K.get(v).__webglTexture,q,$e+Gn),z.framebufferTextureLayer(z.DRAW_FRAMEBUFFER,z.COLOR_ATTACHMENT0,K.get(L).__webglTexture,Te,Ye+Gn)),z.blitFramebuffer(ze,tt,Ie,Ae,Ue,ft,Ie,Ae,z.DEPTH_BUFFER_BIT,z.NEAREST);_.bindFramebuffer(z.READ_FRAMEBUFFER,null),_.bindFramebuffer(z.DRAW_FRAMEBUFFER,null)}else if(q!==0||v.isRenderTargetTexture||K.has(v)){let It=K.get(v),Hn=K.get(L);_.bindFramebuffer(z.READ_FRAMEBUFFER,F),_.bindFramebuffer(z.DRAW_FRAMEBUFFER,$);for(let At=0;At<Oe;At++)me?z.framebufferTextureLayer(z.READ_FRAMEBUFFER,z.COLOR_ATTACHMENT0,It.__webglTexture,q,$e+At):z.framebufferTexture2D(z.READ_FRAMEBUFFER,z.COLOR_ATTACHMENT0,z.TEXTURE_2D,It.__webglTexture,q),He?z.framebufferTextureLayer(z.DRAW_FRAMEBUFFER,z.COLOR_ATTACHMENT0,Hn.__webglTexture,Te,Ye+At):z.framebufferTexture2D(z.DRAW_FRAMEBUFFER,z.COLOR_ATTACHMENT0,z.TEXTURE_2D,Hn.__webglTexture,Te),q!==0?z.blitFramebuffer(ze,tt,Ie,Ae,Ue,ft,Ie,Ae,z.COLOR_BUFFER_BIT,z.NEAREST):He?z.copyTexSubImage3D(Fe,Te,Ue,ft,Ye+At,ze,tt,Ie,Ae):z.copyTexSubImage2D(Fe,Te,Ue,ft,ze,tt,Ie,Ae);_.bindFramebuffer(z.READ_FRAMEBUFFER,null),_.bindFramebuffer(z.DRAW_FRAMEBUFFER,null)}else He?v.isDataTexture||v.isData3DTexture?z.texSubImage3D(Fe,Te,Ue,ft,Ye,Ie,Ae,Oe,wt,Ot,Ke.data):L.isCompressedArrayTexture?z.compressedTexSubImage3D(Fe,Te,Ue,ft,Ye,Ie,Ae,Oe,wt,Ke.data):z.texSubImage3D(Fe,Te,Ue,ft,Ye,Ie,Ae,Oe,wt,Ot,Ke):v.isDataTexture?z.texSubImage2D(z.TEXTURE_2D,Te,Ue,ft,Ie,Ae,wt,Ot,Ke.data):v.isCompressedTexture?z.compressedTexSubImage2D(z.TEXTURE_2D,Te,Ue,ft,Ke.width,Ke.height,wt,Ke.data):z.texSubImage2D(z.TEXTURE_2D,Te,Ue,ft,Ie,Ae,wt,Ot,Ke);_.pixelStorei(z.UNPACK_ROW_LENGTH,Xt),_.pixelStorei(z.UNPACK_IMAGE_HEIGHT,vt),_.pixelStorei(z.UNPACK_SKIP_PIXELS,fn),_.pixelStorei(z.UNPACK_SKIP_ROWS,pn),_.pixelStorei(z.UNPACK_SKIP_IMAGES,Ln),Te===0&&L.generateMipmaps&&z.generateMipmap(Fe),_.unbindTexture()},this.initRenderTarget=function(v){K.get(v).__webglFramebuffer===void 0&&ae.setupRenderTarget(v)},this.initTexture=function(v){v.isCubeTexture?ae.setTextureCube(v,0):v.isData3DTexture?ae.setTexture3D(v,0):v.isDataArrayTexture||v.isCompressedArrayTexture?ae.setTexture2DArray(v,0):ae.setTexture2D(v,0),_.unbindTexture()},this.resetState=function(){te=0,re=0,Z=null,_.reset(),we.reset()},typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("observe",{detail:this}))}get coordinateSystem(){return kn}get outputColorSpace(){return this._outputColorSpace}set outputColorSpace(e){this._outputColorSpace=e;let t=this.getContext();t.drawingBufferColorSpace=pt._getDrawingBufferColorSpace(e),t.unpackColorSpace=pt._getUnpackColorSpace()}};var Os={name:"CopyShader",uniforms:{tDiffuse:{value:null},opacity:{value:1}},vertexShader:`

		varying vec2 vUv;

		void main() {

			vUv = uv;
			gl_Position = projectionMatrix * modelViewMatrix * vec4( position, 1.0 );

		}`,fragmentShader:`

		uniform float opacity;

		uniform sampler2D tDiffuse;

		varying vec2 vUv;

		void main() {

			vec4 texel = texture2D( tDiffuse, vUv );
			gl_FragColor = opacity * texel;


		}`};var Sn=class{constructor(){this.isPass=!0,this.enabled=!0,this.needsSwap=!0,this.clear=!1,this.renderToScreen=!1}setSize(){}render(){console.error("THREE.Pass: .render() must be implemented in derived pass.")}dispose(){}},q0=new Si(-1,1,1,-1,0,1),Nc=class extends Rt{constructor(){super(),this.setAttribute("position",new yt([-1,3,0,-1,-1,0,3,-1,0],3)),this.setAttribute("uv",new yt([0,2,0,0,2,0],2))}},X0=new Nc,Ri=class{constructor(e){this._mesh=new bt(X0,e)}dispose(){this._mesh.geometry.dispose()}render(e){e.render(this._mesh,q0)}get material(){return this._mesh.material}set material(e){this._mesh.material=e}};var ol=class extends Sn{constructor(e,t="tDiffuse"){super(),this.textureID=t,this.uniforms=null,this.material=null,e instanceof kt?(this.uniforms=e.uniforms,this.material=e):e&&(this.uniforms=ci.clone(e.uniforms),this.material=new kt({name:e.name!==void 0?e.name:"unspecified",defines:Object.assign({},e.defines),uniforms:this.uniforms,vertexShader:e.vertexShader,fragmentShader:e.fragmentShader})),this._fsQuad=new Ri(this.material)}render(e,t,n){this.uniforms[this.textureID]&&(this.uniforms[this.textureID].value=n.texture),this._fsQuad.material=this.material,this.renderToScreen?(e.setRenderTarget(null),this._fsQuad.render(e)):(e.setRenderTarget(t),this.clear&&e.clear(e.autoClearColor,e.autoClearDepth,e.autoClearStencil),this._fsQuad.render(e))}dispose(){this.material.dispose(),this._fsQuad.dispose()}};var Yr=class extends Sn{constructor(e,t){super(),this.scene=e,this.camera=t,this.clear=!0,this.needsSwap=!1,this.inverse=!1}render(e,t,n){let s=e.getContext(),r=e.state;r.buffers.color.setMask(!1),r.buffers.depth.setMask(!1),r.buffers.color.setLocked(!0),r.buffers.depth.setLocked(!0);let a,o;this.inverse?(a=0,o=1):(a=1,o=0),r.buffers.stencil.setTest(!0),r.buffers.stencil.setOp(s.REPLACE,s.REPLACE,s.REPLACE),r.buffers.stencil.setFunc(s.ALWAYS,a,4294967295),r.buffers.stencil.setClear(o),r.buffers.stencil.setLocked(!0),e.setRenderTarget(n),this.clear&&e.clear(),e.render(this.scene,this.camera),e.setRenderTarget(t),this.clear&&e.clear(),e.render(this.scene,this.camera),r.buffers.color.setLocked(!1),r.buffers.depth.setLocked(!1),r.buffers.color.setMask(!0),r.buffers.depth.setMask(!0),r.buffers.stencil.setLocked(!1),r.buffers.stencil.setFunc(s.EQUAL,1,4294967295),r.buffers.stencil.setOp(s.KEEP,s.KEEP,s.KEEP),r.buffers.stencil.setLocked(!0)}},ll=class extends Sn{constructor(){super(),this.needsSwap=!1}render(e){e.state.buffers.stencil.setLocked(!1),e.state.buffers.stencil.setTest(!1)}};var cl=class{constructor(e,t){if(this.renderer=e,this._pixelRatio=e.getPixelRatio(),t===void 0){let n=e.getSize(new De);this._width=n.width,this._height=n.height,t=new Vt(this._width*this._pixelRatio,this._height*this._pixelRatio,{type:tn}),t.texture.name="EffectComposer.rt1"}else this._width=t.width,this._height=t.height;this.renderTarget1=t,this.renderTarget2=t.clone(),this.renderTarget2.texture.name="EffectComposer.rt2",this.writeBuffer=this.renderTarget1,this.readBuffer=this.renderTarget2,this.renderToScreen=!0,this.passes=[],this.copyPass=new ol(Os),this.copyPass.material.blending=Rn,this.timer=new Ar}swapBuffers(){let e=this.readBuffer;this.readBuffer=this.writeBuffer,this.writeBuffer=e}addPass(e){this.passes.push(e),e.setSize(this._width*this._pixelRatio,this._height*this._pixelRatio)}insertPass(e,t){this.passes.splice(t,0,e),e.setSize(this._width*this._pixelRatio,this._height*this._pixelRatio)}removePass(e){let t=this.passes.indexOf(e);t!==-1&&this.passes.splice(t,1)}isLastEnabledPass(e){for(let t=e+1;t<this.passes.length;t++)if(this.passes[t].enabled)return!1;return!0}render(e){this.timer.update(),e===void 0&&(e=this.timer.getDelta());let t=this.renderer.getRenderTarget(),n=!1;for(let s=0,r=this.passes.length;s<r;s++){let a=this.passes[s];if(a.enabled!==!1){if(a.renderToScreen=this.renderToScreen&&this.isLastEnabledPass(s),a.render(this.renderer,this.writeBuffer,this.readBuffer,e,n),a.needsSwap){if(n){let o=this.renderer.getContext(),l=this.renderer.state.buffers.stencil;l.setFunc(o.NOTEQUAL,1,4294967295),this.copyPass.render(this.renderer,this.writeBuffer,this.readBuffer,e),l.setFunc(o.EQUAL,1,4294967295)}this.swapBuffers()}Yr!==void 0&&(a instanceof Yr?n=!0:a instanceof ll&&(n=!1))}}this.renderer.setRenderTarget(t)}reset(e){if(e===void 0){let t=this.renderer.getSize(new De);this._pixelRatio=this.renderer.getPixelRatio(),this._width=t.width,this._height=t.height,e=this.renderTarget1.clone(),e.setSize(this._width*this._pixelRatio,this._height*this._pixelRatio)}this.renderTarget1.dispose(),this.renderTarget2.dispose(),this.renderTarget1=e,this.renderTarget2=e.clone(),this.writeBuffer=this.renderTarget1,this.readBuffer=this.renderTarget2}setSize(e,t){this._width=e,this._height=t;let n=this._width*this._pixelRatio,s=this._height*this._pixelRatio;this.renderTarget1.setSize(n,s),this.renderTarget2.setSize(n,s);for(let r=0;r<this.passes.length;r++)this.passes[r].setSize(n,s)}setPixelRatio(e){this._pixelRatio=e,this.setSize(this._width,this._height)}dispose(){this.renderTarget1.dispose(),this.renderTarget2.dispose(),this.copyPass.dispose()}};var ul=class extends Sn{constructor(e,t,n=null,s=null,r=null){super(),this.scene=e,this.camera=t,this.overrideMaterial=n,this.clearColor=s,this.clearAlpha=r,this.clear=!0,this.clearDepth=!1,this.needsSwap=!1,this.isRenderPass=!0,this._oldClearColor=new Qe}render(e,t,n){let s=e.autoClear;e.autoClear=!1;let r,a;this.overrideMaterial!==null&&(a=this.scene.overrideMaterial,this.scene.overrideMaterial=this.overrideMaterial),this.clearColor!==null&&(e.getClearColor(this._oldClearColor),e.setClearColor(this.clearColor,e.getClearAlpha())),this.clearAlpha!==null&&(r=e.getClearAlpha(),e.setClearAlpha(this.clearAlpha)),this.clearDepth==!0&&e.clearDepth(),e.setRenderTarget(this.renderToScreen?null:n),this.clear===!0&&e.clear(e.autoClearColor,e.autoClearDepth,e.autoClearStencil),e.render(this.scene,this.camera),this.clearColor!==null&&e.setClearColor(this._oldClearColor),this.clearAlpha!==null&&e.setClearAlpha(r),this.overrideMaterial!==null&&(this.scene.overrideMaterial=a),e.autoClear=s}};var Ih={name:"LuminosityHighPassShader",uniforms:{tDiffuse:{value:null},luminosityThreshold:{value:1},smoothWidth:{value:1},defaultColor:{value:new Qe(0)},defaultOpacity:{value:0}},vertexShader:`

		varying vec2 vUv;

		void main() {

			vUv = uv;

			gl_Position = projectionMatrix * modelViewMatrix * vec4( position, 1.0 );

		}`,fragmentShader:`

		uniform sampler2D tDiffuse;
		uniform vec3 defaultColor;
		uniform float defaultOpacity;
		uniform float luminosityThreshold;
		uniform float smoothWidth;

		varying vec2 vUv;

		void main() {

			vec4 texel = texture2D( tDiffuse, vUv );

			float v = luminance( texel.xyz );

			vec4 outputColor = vec4( defaultColor.rgb, defaultOpacity );

			float alpha = smoothstep( luminosityThreshold, luminosityThreshold + smoothWidth, v );

			gl_FragColor = mix( outputColor, texel, alpha );

		}`};var Bs=class i extends Sn{constructor(e,t=1,n,s){super(),this.strength=t,this.radius=n,this.threshold=s,this.resolution=e!==void 0?new De(e.x,e.y):new De(256,256),this.clearColor=new Qe(0,0,0),this.needsSwap=!1,this.renderTargetsHorizontal=[],this.renderTargetsVertical=[],this.nMips=5;let r=Math.round(this.resolution.x/2),a=Math.round(this.resolution.y/2);this.renderTargetBright=new Vt(r,a,{type:tn,depthBuffer:!1}),this.renderTargetBright.texture.name="UnrealBloomPass.bright",this.renderTargetBright.texture.generateMipmaps=!1;for(let h=0;h<this.nMips;h++){let f=new Vt(r,a,{type:tn,depthBuffer:!1});f.texture.name="UnrealBloomPass.h"+h,f.texture.generateMipmaps=!1,this.renderTargetsHorizontal.push(f);let u=new Vt(r,a,{type:tn,depthBuffer:!1});u.texture.name="UnrealBloomPass.v"+h,u.texture.generateMipmaps=!1,this.renderTargetsVertical.push(u),r=Math.round(r/2),a=Math.round(a/2)}let o=Ih;this.highPassUniforms=ci.clone(o.uniforms),this.highPassUniforms.luminosityThreshold.value=s,this.highPassUniforms.smoothWidth.value=.01,this.materialHighPassFilter=new kt({uniforms:this.highPassUniforms,vertexShader:o.vertexShader,fragmentShader:o.fragmentShader}),this.separableBlurMaterials=[];let l=[6,10,14,18,22];r=Math.round(this.resolution.x/2),a=Math.round(this.resolution.y/2);for(let h=0;h<this.nMips;h++)this.separableBlurMaterials.push(this._getSeparableBlurMaterial(l[h])),this.separableBlurMaterials[h].uniforms.invSize.value=new De(1/r,1/a),r=Math.round(r/2),a=Math.round(a/2);this.compositeMaterial=this._getCompositeMaterial(this.nMips),this.compositeMaterial.uniforms.blurTexture1.value=this.renderTargetsVertical[0].texture,this.compositeMaterial.uniforms.blurTexture2.value=this.renderTargetsVertical[1].texture,this.compositeMaterial.uniforms.blurTexture3.value=this.renderTargetsVertical[2].texture,this.compositeMaterial.uniforms.blurTexture4.value=this.renderTargetsVertical[3].texture,this.compositeMaterial.uniforms.blurTexture5.value=this.renderTargetsVertical[4].texture,this.compositeMaterial.uniforms.bloomStrength.value=t,this.compositeMaterial.uniforms.bloomRadius.value=.1;let c=[1,.8,.6,.4,.2];this.compositeMaterial.uniforms.bloomFactors.value=c,this.bloomTintColors=[new U(1,1,1),new U(1,1,1),new U(1,1,1),new U(1,1,1),new U(1,1,1)],this.compositeMaterial.uniforms.bloomTintColors.value=this.bloomTintColors,this.copyUniforms=ci.clone(Os.uniforms),this.blendMaterial=new kt({uniforms:this.copyUniforms,vertexShader:Os.vertexShader,fragmentShader:Os.fragmentShader,premultipliedAlpha:!0,blending:Gi,depthTest:!1,depthWrite:!1,transparent:!0}),this._oldClearColor=new Qe,this._oldClearAlpha=1,this._basic=new un,this._fsQuad=new Ri(null)}dispose(){for(let e=0;e<this.renderTargetsHorizontal.length;e++)this.renderTargetsHorizontal[e].dispose();for(let e=0;e<this.renderTargetsVertical.length;e++)this.renderTargetsVertical[e].dispose();this.renderTargetBright.dispose();for(let e=0;e<this.separableBlurMaterials.length;e++)this.separableBlurMaterials[e].dispose();this.compositeMaterial.dispose(),this.blendMaterial.dispose(),this._basic.dispose(),this._fsQuad.dispose()}setSize(e,t){let n=Math.round(e/2),s=Math.round(t/2);this.renderTargetBright.setSize(n,s);for(let r=0;r<this.nMips;r++)this.renderTargetsHorizontal[r].setSize(n,s),this.renderTargetsVertical[r].setSize(n,s),this.separableBlurMaterials[r].uniforms.invSize.value=new De(1/n,1/s),n=Math.round(n/2),s=Math.round(s/2)}render(e,t,n,s,r){e.getClearColor(this._oldClearColor),this._oldClearAlpha=e.getClearAlpha();let a=e.autoClear;e.autoClear=!1,e.setClearColor(this.clearColor,0),r&&e.state.buffers.stencil.setTest(!1),this.renderToScreen&&(this._fsQuad.material=this._basic,this._basic.map=n.texture,e.setRenderTarget(null),e.clear(),this._fsQuad.render(e)),this.highPassUniforms.tDiffuse.value=n.texture,this.highPassUniforms.luminosityThreshold.value=this.threshold,this._fsQuad.material=this.materialHighPassFilter,e.setRenderTarget(this.renderTargetBright),e.clear(),this._fsQuad.render(e);let o=this.renderTargetBright;for(let l=0;l<this.nMips;l++)this._fsQuad.material=this.separableBlurMaterials[l],this.separableBlurMaterials[l].uniforms.colorTexture.value=o.texture,this.separableBlurMaterials[l].uniforms.direction.value=i.BlurDirectionX,e.setRenderTarget(this.renderTargetsHorizontal[l]),e.clear(),this._fsQuad.render(e),this.separableBlurMaterials[l].uniforms.colorTexture.value=this.renderTargetsHorizontal[l].texture,this.separableBlurMaterials[l].uniforms.direction.value=i.BlurDirectionY,e.setRenderTarget(this.renderTargetsVertical[l]),e.clear(),this._fsQuad.render(e),o=this.renderTargetsVertical[l];this._fsQuad.material=this.compositeMaterial,this.compositeMaterial.uniforms.bloomStrength.value=this.strength,this.compositeMaterial.uniforms.bloomRadius.value=this.radius,this.compositeMaterial.uniforms.bloomTintColors.value=this.bloomTintColors,e.setRenderTarget(this.renderTargetsHorizontal[0]),e.clear(),this._fsQuad.render(e),this._fsQuad.material=this.blendMaterial,this.copyUniforms.tDiffuse.value=this.renderTargetsHorizontal[0].texture,r&&e.state.buffers.stencil.setTest(!0),this.renderToScreen?(e.setRenderTarget(null),this._fsQuad.render(e)):(e.setRenderTarget(n),this._fsQuad.render(e)),e.setClearColor(this._oldClearColor,this._oldClearAlpha),e.autoClear=a}_getSeparableBlurMaterial(e){let t=[],n=e/3;for(let a=0;a<e;a++)t.push(.39894*Math.exp(-.5*a*a/(n*n))/n);let s=[],r=[];for(let a=1;a<e;a+=2){let o=t[a],l=a+1<e?t[a+1]:0,c=o+l;s.push((a*o+(a+1)*l)/c),r.push(c)}return new kt({defines:{KERNEL_PAIRS:s.length},uniforms:{colorTexture:{value:null},invSize:{value:new De(.5,.5)},direction:{value:new De(.5,.5)},centerWeight:{value:t[0]},gaussianOffsets:{value:s},gaussianWeights:{value:r}},vertexShader:`

				varying vec2 vUv;

				void main() {

					vUv = uv;
					gl_Position = projectionMatrix * modelViewMatrix * vec4( position, 1.0 );

				}`,fragmentShader:`

				#include <common>

				varying vec2 vUv;

				uniform sampler2D colorTexture;
				uniform vec2 invSize;
				uniform vec2 direction;
				uniform float centerWeight;
				uniform float gaussianOffsets[KERNEL_PAIRS];
				uniform float gaussianWeights[KERNEL_PAIRS];

				void main() {

					vec3 diffuseSum = texture2D( colorTexture, vUv ).rgb * centerWeight;

					for ( int i = 0; i < KERNEL_PAIRS; i ++ ) {

						vec2 uvOffset = direction * invSize * gaussianOffsets[ i ];
						vec3 sample1 = texture2D( colorTexture, vUv + uvOffset ).rgb;
						vec3 sample2 = texture2D( colorTexture, vUv - uvOffset ).rgb;
						diffuseSum += ( sample1 + sample2 ) * gaussianWeights[ i ];

					}

					gl_FragColor = vec4( diffuseSum, 1.0 );

				}`})}_getCompositeMaterial(e){return new kt({defines:{NUM_MIPS:e},uniforms:{blurTexture1:{value:null},blurTexture2:{value:null},blurTexture3:{value:null},blurTexture4:{value:null},blurTexture5:{value:null},bloomStrength:{value:1},bloomFactors:{value:null},bloomTintColors:{value:null},bloomRadius:{value:0}},vertexShader:`

				varying vec2 vUv;

				void main() {

					vUv = uv;
					gl_Position = projectionMatrix * modelViewMatrix * vec4( position, 1.0 );

				}`,fragmentShader:`

				varying vec2 vUv;

				uniform sampler2D blurTexture1;
				uniform sampler2D blurTexture2;
				uniform sampler2D blurTexture3;
				uniform sampler2D blurTexture4;
				uniform sampler2D blurTexture5;
				uniform float bloomStrength;
				uniform float bloomRadius;
				uniform float bloomFactors[NUM_MIPS];
				uniform vec3 bloomTintColors[NUM_MIPS];

				float lerpBloomFactor( const in float factor ) {

					float mirrorFactor = 1.2 - factor;
					return mix( factor, mirrorFactor, bloomRadius );

				}

				void main() {

					// 3.0 for backwards compatibility with previous alpha-based intensity
					vec3 bloom = 3.0 * bloomStrength * (
						lerpBloomFactor( bloomFactors[ 0 ] ) * bloomTintColors[ 0 ] * texture2D( blurTexture1, vUv ).rgb +
						lerpBloomFactor( bloomFactors[ 1 ] ) * bloomTintColors[ 1 ] * texture2D( blurTexture2, vUv ).rgb +
						lerpBloomFactor( bloomFactors[ 2 ] ) * bloomTintColors[ 2 ] * texture2D( blurTexture3, vUv ).rgb +
						lerpBloomFactor( bloomFactors[ 3 ] ) * bloomTintColors[ 3 ] * texture2D( blurTexture4, vUv ).rgb +
						lerpBloomFactor( bloomFactors[ 4 ] ) * bloomTintColors[ 4 ] * texture2D( blurTexture5, vUv ).rgb
					);

					float bloomAlpha = max( bloom.r, max( bloom.g, bloom.b ) );
					gl_FragColor = vec4( bloom, bloomAlpha );

				}`})}};Bs.BlurDirectionX=new De(1,0);Bs.BlurDirectionY=new De(0,1);var Zr={name:"OutputShader",uniforms:{tDiffuse:{value:null},toneMappingExposure:{value:1}},vertexShader:`
		precision highp float;

		uniform mat4 modelViewMatrix;
		uniform mat4 projectionMatrix;

		attribute vec3 position;
		attribute vec2 uv;

		varying vec2 vUv;

		void main() {

			vUv = uv;
			gl_Position = projectionMatrix * modelViewMatrix * vec4( position, 1.0 );

		}`,fragmentShader:`

		precision highp float;

		uniform sampler2D tDiffuse;

		#include <tonemapping_pars_fragment>
		#include <colorspace_pars_fragment>

		varying vec2 vUv;

		void main() {

			gl_FragColor = texture2D( tDiffuse, vUv );

			// tone mapping

			#ifdef LINEAR_TONE_MAPPING

				gl_FragColor.rgb = LinearToneMapping( gl_FragColor.rgb );

			#elif defined( REINHARD_TONE_MAPPING )

				gl_FragColor.rgb = ReinhardToneMapping( gl_FragColor.rgb );

			#elif defined( CINEON_TONE_MAPPING )

				gl_FragColor.rgb = CineonToneMapping( gl_FragColor.rgb );

			#elif defined( ACES_FILMIC_TONE_MAPPING )

				gl_FragColor.rgb = ACESFilmicToneMapping( gl_FragColor.rgb );

			#elif defined( AGX_TONE_MAPPING )

				gl_FragColor.rgb = AgXToneMapping( gl_FragColor.rgb );

			#elif defined( NEUTRAL_TONE_MAPPING )

				gl_FragColor.rgb = NeutralToneMapping( gl_FragColor.rgb );

			#elif defined( CUSTOM_TONE_MAPPING )

				gl_FragColor.rgb = CustomToneMapping( gl_FragColor.rgb );

			#endif

			// color space

			#ifdef SRGB_TRANSFER

				gl_FragColor = sRGBTransferOETF( gl_FragColor );

			#endif

		}`};var hl=class extends Sn{constructor(){super(),this.isOutputPass=!0,this.uniforms=ci.clone(Zr.uniforms),this.material=new ws({name:Zr.name,uniforms:this.uniforms,vertexShader:Zr.vertexShader,fragmentShader:Zr.fragmentShader}),this._fsQuad=new Ri(this.material),this._outputColorSpace=null,this._toneMapping=null}render(e,t,n){this.uniforms.tDiffuse.value=n.texture,this.uniforms.toneMappingExposure.value=e.toneMappingExposure,(this._outputColorSpace!==e.outputColorSpace||this._toneMapping!==e.toneMapping)&&(this._outputColorSpace=e.outputColorSpace,this._toneMapping=e.toneMapping,this.material.defines={},pt.getTransfer(this._outputColorSpace)===St&&(this.material.defines.SRGB_TRANSFER=""),this._toneMapping===Pr?this.material.defines.LINEAR_TONE_MAPPING="":this._toneMapping===Ir?this.material.defines.REINHARD_TONE_MAPPING="":this._toneMapping===Lr?this.material.defines.CINEON_TONE_MAPPING="":this._toneMapping===qi?this.material.defines.ACES_FILMIC_TONE_MAPPING="":this._toneMapping===Dr?this.material.defines.AGX_TONE_MAPPING="":this._toneMapping===Ur?this.material.defines.NEUTRAL_TONE_MAPPING="":this._toneMapping===Nr&&(this.material.defines.CUSTOM_TONE_MAPPING=""),this.material.needsUpdate=!0),this.renderToScreen===!0?(e.setRenderTarget(null),this._fsQuad.render(e)):(e.setRenderTarget(t),this.clear&&e.clear(e.autoClearColor,e.autoClearDepth,e.autoClearStencil),this._fsQuad.render(e))}dispose(){this.material.dispose(),this._fsQuad.dispose()}};var dl=class extends Oi{constructor(){super(),this.name="RoomEnvironment",this.position.y=-3.5;let e=new Bn;e.deleteAttribute("uv");let t=new Zt({side:en}),n=new Zt,s=new oi(16777215,900,28,2);s.position.set(.418,16.199,.3),this.add(s);let r=new bt(e,t);r.position.set(-.757,13.219,.717),r.scale.set(31.713,28.305,28.591),this.add(r);let a=new gn(e,n,6),o=new Ht;o.position.set(-10.906,2.009,1.846),o.rotation.set(0,-.195,0),o.scale.set(2.328,7.905,4.651),o.updateMatrix(),a.setMatrixAt(0,o.matrix),o.position.set(-5.607,-.754,-.758),o.rotation.set(0,.994,0),o.scale.set(1.97,1.534,3.955),o.updateMatrix(),a.setMatrixAt(1,o.matrix),o.position.set(6.167,.857,7.803),o.rotation.set(0,.561,0),o.scale.set(3.927,6.285,3.687),o.updateMatrix(),a.setMatrixAt(2,o.matrix),o.position.set(-2.017,.018,6.124),o.rotation.set(0,.333,0),o.scale.set(2.002,4.566,2.064),o.updateMatrix(),a.setMatrixAt(3,o.matrix),o.position.set(2.291,-.756,-2.621),o.rotation.set(0,-.286,0),o.scale.set(1.546,1.552,1.496),o.updateMatrix(),a.setMatrixAt(4,o.matrix),o.position.set(-2.193,-.369,-5.547),o.rotation.set(0,.516,0),o.scale.set(3.875,3.487,2.986),o.updateMatrix(),a.setMatrixAt(5,o.matrix),this.add(a);let l=new bt(e,zs(50));l.position.set(-16.116,14.37,8.208),l.scale.set(.1,2.428,2.739),this.add(l);let c=new bt(e,zs(50));c.position.set(-16.109,18.021,-8.207),c.scale.set(.1,2.425,2.751),this.add(c);let h=new bt(e,zs(17));h.position.set(14.904,12.198,-1.832),h.scale.set(.15,4.265,6.331),this.add(h);let f=new bt(e,zs(43));f.position.set(-.462,8.89,14.52),f.scale.set(4.38,5.441,.088),this.add(f);let u=new bt(e,zs(20));u.position.set(3.235,11.486,-12.541),u.scale.set(2.5,2,.1),this.add(u);let d=new bt(e,zs(100));d.position.set(0,20,0),d.scale.set(1,.1,1),this.add(d)}dispose(){let e=new Set;this.traverse(t=>{t.isMesh&&(e.add(t.geometry),e.add(t.material))});for(let t of e)t.dispose()}};function zs(i){return new Mr({color:0,emissive:16777215,emissiveIntensity:i})}var Lh={idle:{energy:.34,speed:.16,cyan:8314111,amber:15180363},receiving:{energy:.72,speed:.55,cyan:9169407,amber:16757851},working:{energy:1,speed:.92,cyan:10154751,amber:16760162},tool:{energy:.92,speed:1.12,cyan:8388572,amber:16761183},delegating:{energy:.88,speed:.82,cyan:7536592,amber:16756815},waiting_result:{energy:.48,speed:.28,cyan:7985407,amber:14064458},waiting_user:{energy:.76,speed:.34,cyan:16748405,amber:16738383},speaking:{energy:.7,speed:.74,cyan:9238751,amber:16762218},complete:{energy:.56,speed:.32,cyan:9041343,amber:16762733},error:{energy:.74,speed:.2,cyan:16744556,amber:16736072},offline:{energy:.12,speed:.04,cyan:5858923,amber:6706244}},Nh=el.clamp;function Dh({low:i=!1}={}){let e=new zt;e.name="Reactive orchestration quantum core";let t=new Set,n=Z=>(t.add(Z),Z),s={transparent:!0,depthWrite:!1,blending:Gi},r=n(new Zt({color:16765065,emissive:16754237,emissiveIntensity:3.2,roughness:.28,metalness:.15,transparent:!0,opacity:.9})),a=new bt(n(new Es(.48,i?2:4)),r);a.name="Energy nucleus",e.add(a);let o=n(new un({color:10218239,wireframe:!0,opacity:.35,...s})),l=new bt(n(new Es(.76,i?2:3)),o);l.name="Nucleus field cage",e.add(l);let c=new zt;c.name="Concentric computation rings",e.add(c);let h=[],f=[],u=i?7:11;for(let Z=0;Z<u;Z++){let Q=1.05+Z*.19,ce=n(new un({color:Z%2?8710399:15773013,opacity:.16+Z%3*.035,...s}));h.push(ce);let se=new bt(n(new Cn(Q,.009+Z%3*.004,i?5:7,i?72:128)),ce);se.rotation.set(Z%3*Math.PI/3+.16,Z*2%5*Math.PI/5,Z%4*.19),se.userData.phase=Z*.71,c.add(se),f.push(se)}let d=new zt;d.name="Data orbit filaments",e.add(d);let g=[];for(let Z=0;Z<(i?7:12);Z++){let Q=[],ce=i?90:150,se=1.32+Z%5*.29,Ge=.56+Z%4*.11;for(let Xe=0;Xe<=ce;Xe++){let ee=Xe/ce*Math.PI*2;Q.push(new U(Math.cos(ee)*se,Math.sin(ee)*se*Ge,Math.sin(ee*2+Z)*.16))}let Ce=n(new Rt().setFromPoints(Q)),ut=n(new ai({color:Z%3?9169663:16758621,opacity:Z%3?.2:.28,...s}));g.push(ut);let Ze=new dr(Ce,ut);Ze.rotation.set(Z*.39,Z*.51,Z*.23),Ze.userData.phase=Z*.64,d.add(Ze)}let b=1369948382,m=()=>(b=1664525*b+1013904223>>>0,b/4294967296),p=(Z,Q,ce,se,Ge)=>{let Ce=new Float32Array(Z*3);for(let ee=0;ee<Z;ee++){let ne=m()*2-1,xe=m()*Math.PI*2,Pe=Q+(ce-Q)*Math.pow(m(),.62),Re=Math.sqrt(Math.max(0,1-ne*ne));Ce[ee*3]=Math.cos(xe)*Re*Pe,Ce[ee*3+1]=ne*Pe,Ce[ee*3+2]=Math.sin(xe)*Re*Pe}let ut=n(new Rt);ut.setAttribute("position",new Kt(Ce,3));let Ze=n(new Ms({color:se,size:Ge,sizeAttenuation:!0,opacity:.72,...s})),Xe=new fr(ut,Ze);return e.add(Xe),{points:Xe,material:Ze}},E=p(i?430:1050,.86,2.86,10219263,i?.025:.021),C=p(i?180:430,.72,2.5,16757842,i?.031:.027),y=n(new un({color:10940415,opacity:.12,...s})),w=new bt(n(new jn(.018,.055,7.5,10,1,!0)),y),T=w.clone();T.geometry=n(w.geometry.clone()),T.rotation.z=Math.PI/2,e.add(w,T);let I=n(new _n(.035,i?5:7,i?4:6)),x=n(new un({color:15268607,...s})),A=new gn(I,x,i?24:48),D=new xt,k=new U(1,1,1),G=new Gt;for(let Z=0;Z<A.count;Z++){let Q=Z/A.count*Math.PI*2,ce=1.52+Z%6*.23,se=Math.sin(Q*3)*.9;D.compose(new U(Math.cos(Q)*ce,se,Math.sin(Q)*ce),G,k),A.setMatrixAt(Z,D)}A.instanceMatrix.needsUpdate=!0,e.add(A);let Y=new oi(10153983,11,11,1.5);e.add(Y);let F=.28,$="offline",te={running:0,pending:0,blocked:0,userBlocked:0,workingAgents:0};function re({time:Z=0,delta:Q=1/60,state:ce=$,reduced:se=!1,activity:Ge=te}={}){$=Lh[ce]?ce:"offline",te={...te,...Ge};let Ce=Lh[$],ut=Nh((te.running||0)*.26+(te.workingAgents||0)*.16+Math.min(te.pending||0,6)*.035,0,.58),Ze=Nh(Ce.energy+ut,.08,1.28),Xe=se?1:1-Math.exp(-Math.max(Q,0)*4.2);F=el.lerp(F,Ze,Xe);let ee=$==="waiting_user"||$==="error"||(te.userBlocked||0)>0,ne=ee?16742500:Ce.cyan,xe=ee?16735816:Ce.amber,Pe=se?0:Ce.speed*(.72+F*.72),Re=se?1:1+Math.sin(Z*(1.8+Pe*3.2))*.055*F;a.scale.setScalar(Re*(.92+F*.11)),l.scale.setScalar(1+(se?0:Math.sin(Z*1.13)*.025*F)),r.emissive.setHex(xe),r.emissiveIntensity=.2+F*3.7,r.opacity=.32+F*.55,o.color.setHex(ne),o.opacity=.08+F*.34,c.rotation.y=se?0:Z*Pe*.19,c.rotation.x=se?.11:.11+Math.sin(Z*.17)*.08,f.forEach((Je,dt)=>{se||(Je.rotation.z+=Q*Pe*(.12+dt%5*.035)*(dt%2?1:-1)),Je.material.color.setHex(dt%2?ne:xe),Je.material.opacity=.05+F*(.11+dt%3*.025)}),d.rotation.z=se?0:-Z*Pe*.08,d.rotation.y=se?0:Z*Pe*.06,g.forEach((Je,dt)=>{Je.color.setHex(dt%3?ne:xe),Je.opacity=.045+F*(dt%3?.18:.25)}),E.points.rotation.y=se?0:Z*Pe*.09,E.points.rotation.z=se?0:Z*Pe*.035,C.points.rotation.y=se?0:-Z*Pe*.14,C.points.rotation.x=se?0:Z*Pe*.028,E.material.color.setHex(ne),E.material.opacity=.16+F*.68,C.material.color.setHex(xe),C.material.opacity=.1+F*.64,y.color.setHex(ne),y.opacity=$==="offline"?.02:.035+F*.14,w.scale.set(1,.75+F*.32,1),T.scale.set(.72+F*.34,1,1),x.color.setHex(ee?16752767:15137791),A.rotation.y=se?0:Z*Pe*.12,A.rotation.x=se?0:Math.sin(Z*.11)*.14,Y.color.setHex(ne),Y.intensity=.45+F*12.5}return{group:e,update:re,setActivity(Z){te={...te,...Z}},diagnostics(){return{type:"reactive-quantum-core",state:$,energy:F,rings:f.length,particles:E.points.geometry.attributes.position.count+C.points.geometry.attributes.position.count,nodes:A.count,activity:{...te}}},dispose(){for(let Z of t)Z.dispose?.()}}}var Dc=new U(0,1,0),jr=Math.PI*2;function Uh(i){let e=i|0||1;return()=>(e^=e<<13,e^=e>>>17,e^=e<<5,(e>>>0)/4294967296)}function Fh(){return{armor:new Zt({color:2698543,metalness:.88,roughness:.39}),edge:new Zt({color:7828841,metalness:.92,roughness:.3}),black:new Zt({color:527374,metalness:.6,roughness:.48}),bronze:new Zt({color:6048048,metalness:.91,roughness:.39}),cable:new Zt({color:1711906,metalness:.7,roughness:.44}),light:new Zt({color:16756811,emissive:16751153,emissiveIntensity:1.2,metalness:.35,roughness:.27}),lens:new Zt({color:16768921,emissive:16752947,emissiveIntensity:2.5,metalness:.3,roughness:.16})}}var fl=class{constructor(e){this.materials=e,this.buckets={},this.count=0,this.matrix=new xt,this.normalMatrix=new st,this.position=new U,this.normal=new U,this.rotation=new Gt}add(e,t,n=[0,0,0],s=[1,1,1],r=null){let a=t.index?t.toNonIndexed():t,o=this.buckets[e]||(this.buckets[e]={position:[],normal:[]});this.rotation.identity(),r instanceof Gt?this.rotation.copy(r):r&&this.rotation.setFromEuler(new wn(...r)),this.matrix.compose(new U(...n),this.rotation,new U(...s)),this.normalMatrix.getNormalMatrix(this.matrix);let l=a.getAttribute("position"),c=a.getAttribute("normal");for(let h=0;h<l.count;h++)this.position.fromBufferAttribute(l,h).applyMatrix4(this.matrix),this.normal.fromBufferAttribute(c,h).applyNormalMatrix(this.normalMatrix),o.position.push(this.position.x,this.position.y,this.position.z),o.normal.push(this.normal.x,this.normal.y,this.normal.z);this.count++,a!==t&&a.dispose(),t.dispose()}box(e,t,n,s=null){this.add(e,new Bn(1,1,1),t,n,s)}strut(e,t,n,s=.015,r=6,a=s){let o=new U(...t),l=new U(...n),c=l.clone().sub(o),h=c.length();h<1e-4||this.add(e,new jn(a,s,h,r),o.add(l).multiplyScalar(.5).toArray(),[1,1,1],new Gt().setFromUnitVectors(Dc,c.normalize()))}cable(e,t,n=.015,s=18){let r=new Ts(t.map(a=>new U(...a)));this.add(e,new br(r,s,n,5,!1))}finish(e){for(let[t,n]of Object.entries(this.buckets)){let s=new Rt;s.setAttribute("position",new yt(n.position,3)),s.setAttribute("normal",new yt(n.normal,3)),s.computeBoundingSphere();let r=new bt(s,this.materials[t]);r.name=`machine-batch-${t}`,e.add(r)}return Object.keys(this.buckets).length}};function Pi(i,e,t,n,s=.075){i.add("black",new jn(s*1.4,s*1.3,.105,12),[e,t,n-.025],[1,1,1],[Math.PI/2,0,0]),i.add("edge",new Cn(s*1.15,.015,5,16),[e,t,n+.028]),i.add("bronze",new Cn(s*.82,.007,4,14),[e,t,n+.039]),i.add("lens",new _n(s*.69,12,8),[e,t,n+.025],[1,1,.35]),i.add("black",new _n(s*.19,8,6),[e,t,n+.053],[1,1,.2])}function $0(i,e,t){i.add("black",new _n(.48,20,12),[0,0,0],[1,.9,.91]);let n=t?12:18;for(let s=0;s<n;s++){let r=s/n*jr,a=[];for(let c=0;c<7;c++){let h=-1.23+c*2.46/6;a.push([Math.cos(r)*Math.cos(h)*.53,Math.sin(h)*.5,Math.sin(r)*Math.cos(h)*.46])}for(let c=0;c<a.length-1;c++)i.strut(s%4===0?"bronze":"armor",a[c],a[c+1],.034,6),i.add("edge",new _n(.028,6,4),a[c]);let o=r+.1,l=[Math.cos(o)*.48,.15*Math.sin(r*2),Math.sin(o)*.43];i.box("armor",l,[.12,.19+e()*.13,.06],[0,-o+Math.PI/2,.12]),i.strut("edge",[Math.cos(r)*.32,.43,Math.sin(r)*.3],[Math.cos(r)*.18,.62+e()*.12,Math.sin(r)*.17],.012)}for(let s of[-.27,.02,.29]){let r=Math.sqrt(1-(s/.52)**2)*.51;i.add("edge",new Cn(r,.014,5,40),[0,s,0],[1,.85,1],[Math.PI/2,0,0])}i.box("armor",[0,.045,.43],[.37,.28,.14],[.05,0,0]),Pi(i,0,.07,.53,.092),Pi(i,-.16,-.025,.486,.048),Pi(i,.16,-.025,.486,.048),Pi(i,-.095,.205,.46,.035),Pi(i,.095,.205,.46,.035);for(let s=0;s<4;s++){let r=(s-1.5)*.095;i.box("black",[r,-.35,.26],[.068,.16,.11]),i.box("bronze",[r,-.44,.26],[.075,.025,.12]),i.box("light",[r,-.41,.321],[.031,.018,.008])}for(let s=0;s<95;s++){let r=e()*jr,a=(e()-.5)*.8,o=Math.sqrt(1-a*a/.25)*.51;i.box(s%8===0?"bronze":"edge",[Math.cos(r)*o,a,Math.sin(r)*o*.9],[.015,.027,.013],[e(),r,e()])}for(let s=0;s<5;s++){let r=(s-2)*.12,a=.68+e()*.35;i.strut("armor",[r,.38,-.05],[r*1.12,a,-.08],.022,6,.007),i.box("edge",[r,.54,-.05],[.035,.07,.04]),s%2===0&&i.add("light",new _n(.012,6,4),[r*1.12,a,-.08])}}function Y0(i,e,t){i.box("black",[0,0,0],[.63,.72,.56]);let n=t?34:56;for(let s=0;s<n;s++){let a=s%4*Math.PI/2,o=.065+e()*.12,l=.19+e()*.48,c=(e()-.5)*.63,h=.29+e()*.11,f=Math.sin(a)*h+Math.cos(a)*c,u=Math.cos(a)*h-Math.sin(a)*c,d=(e()-.5)*.36;i.box(s%5===0?"bronze":"armor",[f,d,u],[o,l,.11],[0,a,0]),i.box("edge",[f,d+l*.45,u],[o*1.09,.018,.13],[0,a,0]),i.box("black",[f,d-l*.25,u],[o*1.1,.03,.13],[0,a,0]);let g=new U(Math.sin(a),0,Math.cos(a));for(let b=0;b<3;b++)i.box(b%3===0?"light":"edge",[f+g.x*.061,d+b*.042,u+g.z*.061],[.012,.023,.008],[0,a,0])}for(let s=-1;s<=1;s+=2)for(let r=0;r<4;r++){let a=(r-1.5)*.16;i.box("armor",[s*.44,a,-.07],[.34,.038,.55],[0,0,s*.07]),i.strut("edge",[s*.29,a-.09,.15],[s*.6,a,.15],.009),i.box("bronze",[s*.59,a,-.08],[.015,.045,.56])}Pi(i,0,.04,.435,.063),Pi(i,-.14,.09,.41,.028),Pi(i,.14,.09,.41,.028);for(let s=0;s<9;s++){let r=(e()-.5)*.54,a=(e()-.5)*.45,o=.22+e()*.45;i.box("armor",[r,.35+o/2,a],[.043,o,.05]),i.strut("edge",[r,.35+o,a],[r,.54+o,a],.007,5,.002),i.box("bronze",[r,.46,a],[.067,.016,.075])}for(let s=0;s<12;s++){let r=(s%4-1.5)*.145,a=(Math.floor(s/4)-1)*.14,o=.14+e()*.22;i.strut("armor",[r,-.33,a],[r,-.33-o,a],.03,6,.014),i.add("bronze",new Cn(.025,.007,4,8),[r,-.36-o/2,a],[1,1,1],[Math.PI/2,0,0])}}function Z0(i,e,t,n,s){let r=n==="hermes"?s?7:10:6,a=s?11:17,o=r*a,l=new gn(new jn(1,1,1,6),e.cable,o),c=new gn(new Bn(1,1,1),e.armor,o),h=new gn(new _n(1,6,4),e.edge,o),f=new gn(new gr(1,1,5),e.bronze,r*2);for(let T of[l,c,h,f])T.instanceMatrix.setUsage(lc),T.frustumCulled=!1,T.name=`articulated-${T===l?"cables":T===c?"armor":T===h?"joints":"claws"}`,i.add(T);let u=Array.from({length:r},(T,I)=>({angle:I/r*jr+(n==="hermes"?0:.14),phase:t()*jr,reach:(n==="hermes"?1.12:.84)+t()*.35,depth:(t()-.5)*.9,curl:t()>.5?1:-1})),d=new xt,g=new Gt,b=new U,m=new U,p=new U,E=new U,C=new U;function y(T,I,x,A,D){let k=T.angle+Math.sin(x*.27+T.phase)*.065*A+T.curl*I*I*.75,G=.43+Math.sin(I*1.37)*T.reach,Y=Math.sin(x*.48+T.phase-I*3.9)*.085*A*I;return D.set(Math.cos(k)*G,Math.sin(k)*G*.61-I*I*.35+Y,-.1+Math.sin(I*Math.PI)*T.depth+Math.cos(x*.39+T.phase)*.07*A*I),D}function w(T,I){let x=0;for(let A=0;A<u.length;A++){let D=u[A];for(let k=0;k<a;k++,x++){let G=k/a;y(D,G,T,I,b),y(D,(k+1)/a,T,I,m),E.copy(m).sub(b);let Y=E.length();g.setFromUnitVectors(Dc,E.normalize()),p.copy(b).add(m).multiplyScalar(.5);let F=(1-G*.77)*.029;C.set(F,Y,F),d.compose(p,g,C),l.setMatrixAt(x,d),C.set(F*2.4,Y*.58,F*2.15),d.compose(p,g,C),c.setMatrixAt(x,d),C.setScalar(F*1.08),d.compose(b,g,C),h.setMatrixAt(x,d)}y(D,1,T,I,b);for(let k=0;k<2;k++)y(D,.96,T,I,m),E.copy(b).sub(m).normalize(),E.z+=k?.4:-.4,E.normalize(),p.copy(b).addScaledVector(E,.047),g.setFromUnitVectors(Dc,E),d.compose(p,g,C.set(.015,.12,.015)),f.setMatrixAt(A*2+k,d)}for(let A of[l,c,h,f])A.instanceMatrix.needsUpdate=!0}return w(0,0),{update:w,armCount:r,segments:a}}function kh({kind:i="hermes",seed:e=1,low:t=!1}={}){let n=new zt;n.name=`flying-${i}-machine`;let s=new zt;s.name="hovering-articulated-body",n.add(s);let r=Uh(e),a=Fh(),o=new fl(a);i==="codex"?Y0(o,r,t):$0(o,r,t);let l=o.finish(s),c=Z0(s,a,r,i,t),h=r()*jr,f=1,u="",d=0;return{group:n,update({time:g=0,state:b="idle",reduced:m=!1,delta:p=1/60}={}){let E=["offline","unavailable","unknown","disconnected"].includes(b),C=["working","tool","delegating","receiving","speaking"].includes(b),y=["error","blocked","waiting_user"].includes(b),w=E?.09:y?.75:C?1.4:.72;f=m?w:f+(w-f)*Math.min(1,p*4),a.lens.emissiveIntensity=f*2,a.light.emissiveIntensity=f*.62,b!==u&&(a.lens.emissive.setHex(y?16474676:16754235),a.light.emissive.setHex(y?15888690:16753719),u=b);let T=m||E?0:C?1:.46;s.position.y=Math.sin(g*.53+h)*.045*T,s.rotation.y=Math.sin(g*.24+h)*.1*T,s.rotation.z=Math.sin(g*.31+h)*.025*T,s.rotation.x=Math.sin(g*.29+h*.3)*.024*T,(!t||d++%2===0||m)&&c.update(m?0:g,T)},diagnostics(){return{kind:i,geometryOnly:!0,staticPieces:o.count,articulatedArms:c.armCount,segmentsPerArm:c.segments,drawCalls:l+4,nominalCoreDiameter:1.2,fullSpan:i==="hermes"?3.65:3.15}}}}function Oh({low:i=!1}={}){let e=new zt;e.name="machine-city-architecture";let t=Uh(691309),n=Fh();n.black.color.setHex(133133),n.armor.color.setHex(1188138),n.edge.color.setHex(2179408),n.bronze.color.setHex(2573133),n.cable.color.setHex(463899),n.light.color.setHex(2990020),n.light.emissive.setHex(1740216),n.light.emissiveIntensity=.42;let s=new fl(n),r=[],a=i?18:30;for(let l=0;l<a;l++){let c=l%2?1:-1,h=13+t()*18,f=c*(8.6+t()*17),u=-h,d=.45+t()*.9,g=8+t()*15,b=-7.5+g/2;r.push({x:f,z:u,width:d,height:g}),s.box("black",[f,b,u],[d,g,d*.92]);let m=i?2:3;for(let E=0;E<m;E++){let C=f+(E/Math.max(1,m-1)-.5)*d*1.12,y=d*(.58+t()*.18);s.box("armor",[C,b,u+y*.14],[d*.09,g*.94,y]),s.box("edge",[C,b,u+y*.67],[.018,g*.9,.018])}let p=Math.floor(g/1.18);for(let E=0;E<p;E++){let C=-7.25+E*1.18;s.box("armor",[f,C,u+d*.12],[d*1.13,.035,d*.92]),E%4===0&&s.box("edge",[f,C+.09,u+d*.53],[d*.92,.015,.02]);let y=i?1:2;for(let w=0;w<y;w++)t()<.68||s.box("light",[f+((w+.5)/y-.5)*d*.72,C+.18,u+d*.49],[.022+t()*.025,.045+t()*.06,.012])}}for(let l=0;l<(i?4:7);l++){let c=l%2?1:-1,h=c*(8.3+t()*2.2),f=c*(18+t()*8),u=-4.8+t()*12.5,d=-14-t()*10,g=Math.abs(f-h),b=(h+f)/2;s.box("black",[b,u,d],[g,.11,.36]),s.box("edge",[b,u+.34,d+.16],[g,.022,.022]);for(let m=0;m<Math.floor(g/2);m++){let p=Math.min(h,f)+m*2;s.strut("armor",[p,u-.24,d+.2],[p+c*.55,u+.34,d+.2],.014),m%3===0&&s.box("light",[p,u+.1,d+.25],[.025,.035,.01])}}for(let l of[-1,1])for(let c=0;c<(i?3:5);c++){let h=l*(9+t()*6),f=-14-t()*10,u=l*(.5+t()*.55);s.cable("cable",[[h,13,f],[h+u*.25,7,f+.35],[h+u*.65,1,f],[h+u,-7,f-.5]],.012+t()*.018,18)}let o=s.finish(e);return{group:e,update(){},diagnostics(){return{geometryOnly:!0,towers:r.length,staticPieces:s.count,drawCalls:o,centerClearance:8,depthRange:[-31,-13],visualMode:"quiet-server-room"}}}}var j0=["majak-hermes","majak-codex","quantlab-hermes","quantlab-codex"],Jr=(i,e,t)=>new U(i,e,t),J0={working:"working",blocked:"waiting_user",done:"complete",idle:"idle",unknown:"offline",offline:"offline"},Bh=new Set(["offline","unavailable","unknown","disconnected"]);function K0(i,e,t,n=12){let s=Math.min(e/2,t/2+n);return Math.max(s,Math.min(e-s,i))}function Q0(i,e,t,n,s){let r=Math.tan(e*Math.PI/360)*t*i,a=24/s*r*2,o=Math.max(0,r-1.4*n-.18-a);return Math.min(i<1?2.48:Math.min(5.35,i*2.58),o)}function zh(i,e){let t=new sl({canvas:i,antialias:!0,powerPreference:"high-performance"}),n=innerWidth<760||navigator.deviceMemory&&navigator.deviceMemory<=4,s=Math.min(devicePixelRatio,n?1:1.5);t.setPixelRatio(s),t.outputColorSpace=cn,t.toneMapping=qi,t.toneMappingExposure=1.2;let r=new Oi;r.background=new Qe(133393),r.fog=new or(463644,.041);let a=new Jt(35,1,.1,90);a.position.set(.35,.55,13.8),a.lookAt(0,.35,0);let o=new Fs(t),l=new dl,c=o.fromScene(l,.08).texture;r.environment=c,r.environmentIntensity=.72,l.dispose(),o.dispose(),r.add(new Tr(9423327,329997,.82));let h=new Hi(12115434,3.6);h.position.set(-5,7,8),r.add(h);let f=new Hi(4169662,1.35);f.position.set(5,1,6),r.add(f);let u=new Hi(5228520,4.4);u.position.set(4,6,-6),r.add(u);let d=new oi(14917708,7.5,13,2);d.position.set(-1,-3,3),r.add(d);let g=Dh({low:n}),b=new zt;b.position.set(0,.42,-.35),b.add(g.group),r.add(b);let m=Oh({low:n});r.add(m.group);let p=new Map;for(let[N,V]of j0.entries()){let ie=kh({kind:V.endsWith("hermes")?"hermes":"codex",seed:N+71,low:n});ie.group.userData.agentId=V,ie.base=Jr(0,0,0),ie.id=V,ie.status="offline",ie.group.traverse(ge=>{ge.userData.agentId=V}),r.add(ie.group),p.set(V,ie)}let E=new zt;E.name="swarm-task-nodes",r.add(E);let C=new zt;C.name="swarm-task-links",r.add(C);let y=new Map,w=[],T={running:7598815,pending:12163946,blocked:16747634,failed:16736082,done:7522710},I={running:0,blocked:1,failed:2,pending:3,done:4},x=null,A=()=>{};function D(N){E.remove(N.group),N.group.traverse(V=>{if(V.geometry?.dispose(),V.material)for(let ie of Array.isArray(V.material)?V.material:[V.material])ie.dispose()})}function k(N,V,ie,ge=0){let ue=new zt;ue.name=ge?"swarm-task-cluster":`swarm-task-${N}`;let pe=T[V]||10261639,_e=new bt(ge?new _r(.22,0):new vr(.16,0),new Zt({color:2435885,emissive:pe,emissiveIntensity:V==="running"?1.8:.75,metalness:.72,roughness:.28})),Se=new bt(new Cn(ge?.3:.23,.012,5,20),new un({color:pe,transparent:!0,opacity:.7}));Se.rotation.x=Math.PI/2,ue.add(_e,Se),ue.userData.taskId=ge?null:N,ue.userData.clusterCount=ge,ue.traverse(O=>{O.userData.taskId=ge?null:N});let Be={id:N,status:V,index:ie,clusterCount:ge,group:ue,body:_e,ring:Se,base:new U};return E.add(ue),Be}function G(){let N=[...y.values()],V=N.length;N.forEach((ie,ge)=>{let ue=ge<10?0:1,pe=ue?ge-10:ge,_e=ue?Math.max(1,V-10):Math.min(10,V),Se=-Math.PI*.92+pe/Math.max(1,_e-1)*Math.PI*1.84,Be=ue?3.55:2.65,O=ue?2.38:1.82;ie.base.set(Math.cos(Se)*Be,.42+Math.sin(Se)*O,ue?1.48:1.18),ie.group.position.copy(ie.base),ie.group.scale.setScalar(ie.clusterCount?.9:.72)})}function Y(){for(;w.length;){let N=w.pop();C.remove(N.line),N.line.geometry.dispose(),N.line.material.dispose()}}function F(){for(let N of w){let V=y.get(N.from),ie=y.get(N.to);if(!V||!ie){N.line.visible=!1;continue}N.line.visible=!0,N.line.geometry.setFromPoints([V.group.position,ie.group.position])}}function $(N){Y();let V=new Set;for(let ie of N){let ge=[];ie.parent_task_id&&ge.push([ie.parent_task_id,"parent"]);for(let ue of ie.dependencies||[])ge.push([ue,"dependency"]);for(let[ue,pe]of ge){if(!y.has(ue)||!y.has(ie.task_id))continue;let _e=`${ue}\0${ie.task_id}\0${pe}`;if(V.has(_e))continue;V.add(_e);let Se=new Rt,Be=new ai({color:pe==="dependency"?14981684:7598815,transparent:!0,opacity:pe==="dependency"?.26:.34}),O=new zi(Se,Be);O.name=`swarm-task-${pe}-edge`,O.renderOrder=-1,C.add(O),w.push({line:O,from:ue,to:ie.task_id,kind:pe})}}F()}function te(N){let V=[...Array.isArray(N)?N:[]].filter(_e=>_e&&_e.status!=="done").sort((_e,Se)=>(I[_e.status]??9)-(I[Se.status]??9)||(Se.updated_at||0)-(_e.updated_at||0)||String(_e.task_id).localeCompare(String(Se.task_id))),ie=20,ge=V.slice(0,ie),ue=new Map(ge.map((_e,Se)=>[_e.task_id,{row:_e,index:Se}])),pe=Math.max(0,V.length-ie);pe&&ue.set("__cluster__",{row:{task_id:"__cluster__",status:"pending"},index:ge.length,clusterCount:pe});for(let[_e,Se]of[...y])ue.has(_e)||(D(Se),y.delete(_e));for(let[_e,Se]of ue){let Be=y.get(_e);(!Be||Be.status!==Se.row.status||Be.clusterCount!==(Se.clusterCount||0))&&(Be&&D(Be),Be=k(_e,Se.row.status,Se.index,Se.clusterCount||0),y.set(_e,Be)),Be.index=Se.index,Be.status=Se.row.status}x&&!y.has(x)&&(x=null),G(),$(ge),xe=!0}let re=new Rt;re.setAttribute("position",new Kt(new Float32Array(195),3));let Z=new zi(re,new ai({color:9035184,transparent:!0,opacity:.32}));Z.visible=!1,r.add(Z);let Q=new gn(new _n(.028,6,4),new un({color:12582855}),12);Q.visible=!1,r.add(Q);let ce=new xt,se=Jr(1,1,1),Ge=new Gt,Ce=new cl(t);Ce.addPass(new ul(r,a));let ut=new Bs(new De(1,1),.38,.38,1.18);Ce.addPass(ut),Ce.addPass(new hl);let Ze="offline",Xe=matchMedia("(prefers-reduced-motion: reduce)").matches,ee=!0,ne=!1,xe=!0,Pe={enabled:!1,state:"idle",target:"majak-codex"},Re=null,Je=()=>{},dt=0,it=0,ot=0,gt=0,rt=0,at=!1,Dt=0,Lt=0,_t={running:0,pending:0,blocked:0,workingAgents:0,activeAgent:null},Tt=new Cr,z=new De,Et=new U,lt=N=>{let V=p.get(N);return V?.group.visible?V:null};function P(N){ne||(ne=!0,cancelAnimationFrame(gt),gt=0,e.hidden=!1,i.dispatchEvent(new CustomEvent("scene-unavailable",{bubbles:!0})),N&&console.error("Machine City renderer unavailable",N))}let _=()=>{if(!ne)try{let{width:N,height:V}=i.getBoundingClientRect();if(!N||!V)return;a.aspect=N/V,a.position.z=a.aspect<1?17.6:13.8,a.updateProjectionMatrix(),a.updateMatrixWorld(),t.setSize(N,V,!1),Ce.setSize(N,V);let ie=a.aspect<1?.48:.7,ge=a.getWorldDirection(Jr(0,0,0));[...p.values()].forEach((ue,pe)=>{let _e=pe%2===0?.5:1.05,Se=Q0(a.aspect,a.fov,Math.max(.1,a.position.z-_e-.25),ie,N),Be=a.position.x+(_e-a.position.z)/ge.z*ge.x;ue.base.set(Be+(pe<2?-Se:Se),pe%2===0?2.15:-1.1,_e),ue.group.scale.setScalar(ie),ue.group.position.copy(ue.base)}),G(),xe=!0}catch(N){P(N)}},X=new ResizeObserver(_);X.observe(i);function K(N){let V=i.getBoundingClientRect();return!V.width||!V.height?null:(z.set((N.clientX-V.left)/V.width*2-1,-(N.clientY-V.top)/V.height*2+1),Tt.setFromCamera(z,a),Tt.intersectObjects([...y.values()].map(ge=>ge.group),!0).find(ge=>!!ge.object.userData.taskId)?.object.userData.taskId||null)}i.addEventListener("pointermove",N=>{let V=i.getBoundingClientRect();Dt=(N.clientX-V.left)/V.width-.5,Lt=(N.clientY-V.top)/V.height-.5;let ie=K(N);i.dispatchEvent(new CustomEvent("swarm-task-hover",{bubbles:!0,detail:{taskId:ie,x:N.clientX-V.left,y:N.clientY-V.top}}))}),i.addEventListener("pointerleave",()=>{Dt=0,Lt=0,i.dispatchEvent(new CustomEvent("swarm-task-hover",{bubbles:!0,detail:{taskId:null,x:0,y:0}}))}),i.addEventListener("click",N=>{if(ne||!ee)return;let V=i.getBoundingClientRect();if(!V.width||!V.height)return;z.set((N.clientX-V.left)/V.width*2-1,-(N.clientY-V.top)/V.height*2+1),Tt.setFromCamera(z,a);let ie=[...p.values()].filter(ue=>ue.group.visible).map(ue=>ue.group).concat([...y.values()].map(ue=>ue.group)),ge=Tt.intersectObjects(ie,!0).find(ue=>{for(let pe=ue.object;pe;pe=pe.parent)if(!pe.visible)return!1;return!!(ue.object.userData.agentId||ue.object.userData.taskId)});if(ge){let ue=ge.object.userData.taskId,pe=ge.object.userData.agentId;ue?A(ue):pe&&Je(pe)}}),i.addEventListener("webglcontextlost",N=>{N.preventDefault(),P()}),i.addEventListener("webglcontextrestored",()=>{e.hidden=!1}),document.addEventListener("visibilitychange",()=>{ot=0,xe=!0});function ae(){r.updateMatrixWorld(),a.updateMatrixWorld();let N=i.getBoundingClientRect();if(!N.width||!N.height)return;for(let[ie,ge]of p){let ue=document.querySelector(`#film-view [data-agent="${ie}"]`);if(!ue||!ge.group.visible)continue;ge.group.getWorldPosition(Et),Et.y-=.78*ge.group.scale.x,Et.project(a);let pe=ue.offsetParent?.getBoundingClientRect()||N,_e=K0((Et.x*.5+.5)*N.width,N.width,ue.offsetWidth);ue.style.setProperty("--agent-x",`${N.left-pe.left+_e}px`),ue.style.setProperty("--agent-y",`${N.top-pe.top+(-Et.y*.5+.5)*N.height}px`)}let V=x?y.get(x):null;V?(V.group.getWorldPosition(Et),Et.project(a),i.dispatchEvent(new CustomEvent("swarm-task-focus-position",{bubbles:!0,detail:{taskId:V.id,x:(Et.x*.5+.5)*N.width,y:(-Et.y*.5+.5)*N.height}}))):i.dispatchEvent(new CustomEvent("swarm-task-focus-position",{bubbles:!0,detail:{taskId:null,x:0,y:0}}))}function be(N){if(gt=0,!ne){try{if(document.hidden||!ee||Xe&&!xe){gt=requestAnimationFrame(be);return}let V=ot?Math.min((N-ot)/1e3,.08):1/60;ot=N,Xe||(it+=V);let ie=Xe?0:it,ge=Xe||Bh.has(Ze);b.rotation.y=dt||(ge?0:ie*.028+Dt*.11),b.rotation.x=ge?0:-Lt*.07+Math.sin(ie*.17)*.025;let ue=[...p.values()].filter(J=>J.group.visible&&J.status==="working").length;g.update({time:ie,state:Ze,reduced:Xe,delta:V,activity:{..._t,workingAgents:ue}}),m.update({time:ie,reduced:Xe});let pe=0;for(let J of p.values()){let ve=pe*1.83,we=Pe.enabled?J.id===Pe.target?Ze:"idle":J0[J.status]||"offline";J.group.position.copy(J.base),!Xe&&!Bh.has(we)&&(J.group.position.x+=Math.sin(ie*.24+ve)*.18,J.group.position.y+=Math.sin(ie*.37+ve)*.15,J.group.position.z+=Math.cos(ie*.22+ve)*.25),J.group.rotation.y=J.base.x<0?.3:-.3,J.update({time:ie,state:we,reduced:Xe,delta:V}),pe++}let _e=0;for(let J of y.values()){let ve=_e*.73;J.group.position.copy(J.base),Xe?(J.ring.rotation.z=ve,J.group.rotation.y=0):(J.group.position.y+=Math.sin(ie*.42+ve)*.055,J.group.position.z+=Math.cos(ie*.31+ve)*.08,J.ring.rotation.z=ie*(J.status==="running"?.75:.18)+ve,J.group.rotation.y=ie*.08+ve*.2);let we=x===J.id,fe=J.clusterCount?.9:.72;J.group.scale.setScalar(we?fe*1.45:fe),J.body.material.emissiveIntensity=(J.status==="running"?1.8:.75)+(we?.9:0),_e++}F();let Se=_t.activeAgent?lt(_t.activeAgent):[...p.values()].find(J=>J.group.visible&&["working","blocked"].includes(J.status)),Be=Pe.enabled?lt(Pe.target):Se,O=Pe.enabled?Ze:Ze==="waiting_user"||(_t.userBlocked||0)>0||Be?.status==="blocked"?"waiting_user":"working",Me=!!(Be&&(Pe.enabled?["delegating","waiting_result","complete","tool"].includes(Ze):["working","waiting_user"].includes(O)));if(Z.visible=Me,Q.visible=Me&&O!=="waiting_user",Me){let J=Be.group.position,ve=new Vi(Jr(J.x<0?-1.55:1.55,.5,.6),Jr(J.x*.56,J.y-.42,2.05),J.clone()),we=ve.getPoints(64);re.setFromPoints(we);let fe=O==="waiting_user"?16742500:J.x<0?16758359:7598815;Z.material.color.setHex(fe),Q.material.color.setHex(fe),Z.material.opacity=O==="waiting_user"?.2:.43;for(let We=0;We<12;We++){let Ve=Xe?(We+1)/13:(ie*(.3+Math.min(_t.running||0,2)*.08)+We/12)%1;Pe.enabled&&Ze==="complete"&&(Ve=1-Ve),ce.compose(ve.getPoint(Ve),Ge,se),Q.setMatrixAt(We,ce)}Q.instanceMatrix.needsUpdate=!0}ae(),Ce.render(),xe=!1,!Xe&&V>.048?rt++:rt=Math.max(0,rt-1),rt>90&&!at&&(s=1,t.setPixelRatio(1),Ce.setPixelRatio(1),ut.enabled=!1,at=!0,_())}catch(V){P(V);return}ne||(gt=requestAnimationFrame(be))}}_(),ne||(gt=requestAnimationFrame(be));let Ee=document.querySelector("#inspect-model");return Ee?.addEventListener("click",()=>{dt=dt===0?.6:dt===.6?1.2:0,Ee.textContent=dt===0?"Prohl\xE9dnout j\xE1dro":dt===.6?"J\xE1dro ze t\u0159\xED \u010Dtvrtin":"J\xE1dro z boku",xe=!0}),{setState(N){Ze!==N&&(Ze=N,xe=!0)},setReduced(N){Xe=N,xe=!0,ot=0},setActive(N){ee=N,xe=!0,ot=0,N&&_()},setGaze(){},setActivity(N){_t={..._t,...N},g.setActivity(_t),xe=!0},setAgents(N){for(let V of p.values()){let ie=N.find(ge=>(ge.id||ge.agent)===V.id);V.status=ie?.status||"offline",V.group.visible=!!ie&&ie.visible!==!1}lt(Re)||(Re=null),lt(Pe.target)||(Pe.target=null),xe=!0},setTasks(N){te(N)},focusAgent(N){Re=lt(N)?N:null,xe=!0},focusTask(N){x=N&&y.has(N)?N:null,xe=!0},setDemo(N){Pe={...Pe,...N},lt(Pe.target)||(Pe.target=null),xe=!0},onSelect(N){Je=N},onTaskSelect(N){A=N},diagnostics(){return{geometry:"true-3d",state:Ze,reduced:Xe,active:ee,contextLost:ne,quality:at?"adaptive-low":n?"low":"high",core:g.diagnostics(),drones:[...p.values()].map(N=>({id:N.id,position:N.group.position.toArray(),...N.diagnostics()})),tasks:[...y.values()].map(N=>({id:N.id,status:N.status,clusterCount:N.clusterCount,position:N.group.position.toArray()})),taskEdges:w.map(N=>({from:N.from,to:N.to,kind:N.kind})),drawCalls:t.info.render.calls,triangles:t.info.render.triangles}},quality:n?"\xDAsporn\xE1":"Vysok\xE1",dispose(){cancelAnimationFrame(gt),X.disconnect(),r.traverse(N=>{if(N.geometry?.dispose(),N.material)for(let V of Array.isArray(N.material)?N.material:[N.material])V.dispose()}),c.dispose(),Ce.dispose(),t.dispose()}}}var Vs={idle:{label:"\u010Cek\xE1",copy:"Klidov\xFD re\u017Eim \xB7 \u017E\xE1dn\xE1 hl\xE1\u0161en\xE1 aktivn\xED pr\xE1ce",tone:"amber"},receiving:{label:"P\u0159ij\xEDm\xE1 zad\xE1n\xED",copy:"Demo p\u0159ijet\xED nov\xE9ho zad\xE1n\xED",tone:"amber"},working:{label:"Zpracov\xE1v\xE1 \xFAlohu",copy:"Demo zpracov\xE1n\xED \xFAlohy",tone:"amber"},tool:{label:"Pou\u017E\xEDv\xE1 n\xE1stroj",copy:"Demo n\xE1strojov\xE9 operace \xB7 \u017Eiv\xFD zdroj tuto ud\xE1lost neposkytuje",tone:"green"},delegating:{label:"Deleguje",copy:"Demo p\u0159ed\xE1n\xED \xFAkolu vybran\xE9mu agentovi",tone:"green"},waiting_result:{label:"\u010Cek\xE1 na v\xFDsledek",copy:"Demo \u010Dek\xE1n\xED \xB7 neprob\xEDh\xE1 intenzivn\xED pr\xE1ce",tone:"amber"},waiting_user:{label:"\u010Cek\xE1 na z\xE1sah",copy:"Agent je blokovan\xFD a pot\u0159ebuje kontrolu",tone:"red"},speaking:{label:"Mluv\xED",copy:"Stylizovan\xE1 animace odpov\u011Bdi \xB7 audio nen\xED p\u0159ipojeno",tone:"green"},complete:{label:"\xDAloha dokon\u010Dena",copy:"Agent ohl\xE1sil stav done",tone:"green"},error:{label:"Probl\xE9m syst\xE9mu",copy:"Jeden nebo v\xEDce datov\xFDch zdroj\u016F selhalo",tone:"red"},offline:{label:"Odpojeno",copy:"\u010Cerstv\xFD \u017Eiv\xFD stav nen\xED dostupn\xFD",tone:"muted"}},vn=["majak","quantlab"],Vh=new Set(["majak-hermes","majak-codex","quantlab-hermes","quantlab-codex"]),Hh={hermes:"Orchestrace, pam\u011B\u0165, n\xE1stroje a \u0159\xEDzen\xED pr\xE1ce",codex:"Implementace, testov\xE1n\xED a technick\xE1 revize"},Gh={idle:"\u010Cek\xE1",working:"Pracuje",blocked:"Blokov\xE1no",done:"Hotovo",unknown:"Nezn\xE1m\xE9",offline:"Odpojeno"},hn={pending:"\u010Cek\xE1",running:"B\u011B\u017E\xED",blocked:"Blokov\xE1no",done:"Hotovo",failed:"Selhalo"},Wh={pending:"pending",ready:"pending",running:"running",review:"running",blocked:"blocked",done:"done",failed:"failed",cancelled:"done"},qh="Bbambaaamm/Autonomous-Quant-Lab",Ft=new Intl.NumberFormat("cs-CZ"),Zi=new Intl.NumberFormat("cs-CZ",{notation:"compact",maximumFractionDigits:1}),ye=i=>String(i??"").replace(/[&<>"']/g,e=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[e]),Pt=i=>i==null?"Nedostupn\xE9":Ft.format(i),Ii=i=>i==null?"Nezn\xE1m\xE9":i===0?"0 USD":`${(i/1e6).toFixed(4)} USD`,ji=i=>i==null?"Nedostupn\xE9":i<1e3?`${Ft.format(Math.round(i))} ms`:`${(i/1e3).toFixed(2)} s`,ui=i=>Number.isFinite(i)?`${Math.max(0,Math.floor(Date.now()/1e3-i))} s`:"Nedostupn\xE9",hi=i=>Number.isFinite(i)?new Date(i*1e3).toLocaleString("cs-CZ",{day:"2-digit",month:"2-digit",hour:"2-digit",minute:"2-digit"}):"\u2014",jt=i=>Number.isFinite(i?.issue)?`#${i.issue}`:"bez issue",Kr=i=>i.endsWith("-hermes")?"hermes":"codex",Uc=i=>Gh[i]||Gh.unknown,e_=i=>({green:"#6adf9a",red:"#ff7159",muted:"#716d66",amber:"#e49a34"})[i],Xh=(i,e="provider")=>{let t=i.filter(r=>typeof r[e]=="string"&&Number.isFinite(r.last_used_at)).sort((r,a)=>a.last_used_at-r.last_used_at||r[e].localeCompare(a[e])),n=t[0]?.[e]||null,s=[...new Set(t.map(r=>r[e]))].filter(r=>r!==n);return{currentProvider:n,historicalProviders:s}};function $h(i){let e=M=>document.querySelector(M),t={film:e("#film-view"),work:e("#work-view"),faceState:e("#face-state"),faceTask:e("#face-task"),faceSignal:e("#face-signal"),header:e("#header-status"),liveDot:e("#live-dot"),snapshotAge:e("#snapshot-age"),agentCount:e("#agent-count"),queueCount:e("#queue-count"),requestCount:e("#request-count"),searchCount:e("#search-count"),searchLatency:e("#search-latency"),costTotal:e("#cost-total"),attention:e("#attention-action"),coordinatorCurrent:e("#coordinator-current"),coordinatorNext:e("#coordinator-next"),demo:e("#demo-panel"),demoStates:e("#demo-states"),detail:e("#agent-detail"),backdrop:e("#drawer-backdrop"),canvas:e("#machine-scene"),fallback:e("#webgl-fallback"),swarmKpis:e("#swarm-kpis"),kpiActive:e("#kpi-active"),kpiRunning:e("#kpi-running"),kpiWaiting:e("#kpi-waiting"),kpiBlocked:e("#kpi-blocked"),kpiQueue:e("#kpi-queue"),kpiSuccess:e("#kpi-success"),kpiRetries:e("#kpi-retries"),kpiAvgTask:e("#kpi-avg-task"),kpiTokens:e("#kpi-tokens"),kpiCost:e("#kpi-cost"),dagStatus:e("#taskgraph-status"),dagNodes:e("#taskgraph-nodes"),analyticsGrid:e("#swarm-analytics-grid")},n=null,s=!1,r="idle",a="work",o=null,l=null,c="all",h=matchMedia("(prefers-reduced-motion: reduce)").matches,f=null,u=!1,d=null,g="",b=null,m=!1,p="Na\u010D\xEDt\xE1m skute\u010Dn\xE1 data";function E(){u=!0,t.fallback.hidden=!1;try{f?.setActive(!1)}catch{}di("work")}try{f=i(t.canvas,t.fallback),u=!f}catch{u=!0,t.fallback.hidden=!1}t.canvas.addEventListener("webglcontextlost",M=>{M.preventDefault(),E()}),t.canvas.addEventListener("scene-unavailable",E),t.canvas.addEventListener("swarm-task-hover",M=>{let R=e("#task-hover-label"),S=M.detail||{},W=ee(S.taskId);if(!R||!W||a!=="film"){R&&(R.hidden=!0);return}R.textContent=`${jt(W)} \xB7 ${hn[W.status]||W.status} \xB7 ${W.issue_title||W.task_id}`,R.style.left=`${Math.max(12,S.x+14)}px`,R.style.top=`${Math.max(72,S.y+14)}px`,R.hidden=!1}),t.canvas.addEventListener("swarm-task-focus-position",M=>{let R=e("#task-selected-label"),S=M.detail||{},W=ee(S.taskId);if(!R||!W||a!=="film"||l!==W.task_id){R&&(R.hidden=!0);return}R.innerHTML=`<b>${ye(jt(W))}</b><span>${ye(hn[W.status]||W.status)}</span>`,R.style.left=`${Math.max(56,S.x)}px`,R.style.top=`${Math.max(110,S.y)}px`,R.hidden=!1});function C(M,...R){if(!(!f||u||typeof f[M]!="function"))try{return f[M](...R)}catch{E()}}function y(M,R){return n?.sources.find(S=>S.profile===M&&S.kind===R)}function w(){return vn.map(M=>y(M,"queue")).filter(Boolean)}function T(M=null){return(M?[y(M,"queue")].filter(Boolean):w()).flatMap(S=>S?.status==="available"?S.rows:[])}function I(M){return M?.repo==="Bbambaaamm/dotacni-majak"?"majak":"quantlab"}function x(M){return M==="majak-hermes"?"dotacni-majak-hermes":M}function A(M){return M==="dotacni-majak-hermes"?"majak-hermes":M}function D(){return y("quantlab","swarm")}function k(){let M=D();return M?.status==="available"&&M.rows.length===1?M.rows[0]:null}function G(){let M=k(),R=D();if(!M)return[];let S=/^\d+$/.test(M.issue)?Number(M.issue):null,W=R?.data_at??R?.observed_at??null;return M.tasks.map(de=>({task_id:de.task_id,status:Wh[de.state]||"blocked",raw_state:de.state,attempts:de.attempt,max_attempts:de.max_attempts,not_before:null,updated_at:W,agent:de.agent_id||null,kind:"herdr_swarm",blocker:de.blocker,pr_number:null,issue:S,issue_state:M.issue_state||"unknown",issue_title:`Herdr swarm \xB7 ${de.role}`,repo:M.repo,parent_task_id:de.parent_task_id,parent_agent_id:de.parent_agent_id,dependencies:de.dependencies,result_sha:de.result_sha,model:de.model,fallback_model:de.fallback_model,fencing_token:de.fencing_token,attempt_state:de.attempt_state,delivery_reconcile_count:de.delivery_reconcile_count}))}function Y(M){return M?.issue_state==="closed"||M?.issue_open===!1&&M?.scheduler_state==="closed"}function F(M){return!Y(M)||["running","pending"].includes(M.status)}function $(M=null){return T(M).filter(F)}function te(){return G().filter(F)}function re(){return k()?.agents||[]}function Z(){let M=k();return M?.runtime_status==="available"?M.runtime_agents:null}function Q(){let M=Z();return M&&M.filter(S=>["working","blocked"].includes(S.status)&&S.task_id).map(S=>S.task_id).map(ee).find(Boolean)||null}function ce(){return k()?.edges||[]}function se(){return k()?[...G(),...T("majak")]:T()}function Ge(){return y("quantlab","admission")}function Ce(){let M=Ge();return M?.status==="available"?M.rows:[]}function ut(){return Ce().filter(M=>M.event==="deny")}function Ze(){let M=y("quantlab","release");return M?.status==="available"&&M.rows.length===1?M.rows[0]:null}function Xe(){return $().filter(M=>["pending","running","blocked"].includes(M.status))}function ee(M){return se().find(R=>R.task_id===M)||T().find(R=>R.task_id===M)||null}let ne=new Set(["user_action_required","agent_interactive_input_required","github_write_auth_required"]);function xe(M=null){return $(M).filter(R=>R.status==="blocked"&&ne.has(R.blocker))}function Pe(M=null){return $(M).filter(R=>R.status==="blocked"&&!ne.has(R.blocker))}function Re(M=null){let R={running:0,blocked:1};return $().filter(S=>(!M||S.agent===M)&&Object.hasOwn(R,S.status)).sort((S,W)=>R[S.status]-R[W.status]||(W.updated_at||0)-(S.updated_at||0)||S.task_id.localeCompare(W.task_id))[0]}function Je(M=null){return $().filter(R=>(!M||R.agent===M)&&R.status==="pending").sort((R,S)=>(R.not_before??Number.MAX_SAFE_INTEGER)-(S.not_before??Number.MAX_SAFE_INTEGER)||R.task_id.localeCompare(S.task_id))[0]}function dt(M){return M?`${jt(M)} \xB7 ${M.task_id}`:"\u017D\xE1dn\xE1"}function it(M){return M?`${Pt(M.attempts)} / ${Pt(M.max_attempts)}`:"Nedostupn\xE9"}function ot(M){return Number.isFinite(M?.issue)?`https://github.com/${M.repo||qh}/issues/${M.issue}`:null}function gt(M){return Number.isFinite(M?.pr_number)?`https://github.com/${M.repo||qh}/pull/${M.pr_number}`:null}function rt(M,R){return M?`<a href="${ye(M)}" target="_blank" rel="noopener noreferrer">${ye(R)}</a>`:""}function at(){return vn.flatMap(M=>{let R=y(M,"herdr");return R?.status==="available"?R.rows.map(S=>({...S,profile:M})):[]})}function Dt(M){let R=at().filter(S=>S.profile===M);return R.length?R:["hermes","codex"].map(S=>({agent:`${M}-${S}`,profile:M,status:"offline",unavailable:!0}))}function Lt(M){let R=y(M,"router"),S=R?.status==="available",W=S?R.rows:[],de=S?W.reduce((B,H)=>B+H.requests,0):null,oe=B=>!S||W.some(H=>!Number.isFinite(H[B]))?null:W.reduce((H,q)=>H+q[B],0),le=B=>{if(!S)return{known:null,knownRequests:null,unknownRequests:null,coverage:null};let H=0,q=0,Te=0;for(let Ie of W)Number.isFinite(Ie[B])?(H+=Ie[B],q+=Ie.requests):Te+=Ie.requests;return{known:H,knownRequests:q,unknownRequests:Te,coverage:de===0?100:Math.round(q/de*100)}},he=le("input_tokens"),ke=le("output_tokens"),Ne=le("cost_microusd"),qe=S?W.filter(B=>Number.isFinite(B.input_tokens)&&Number.isFinite(B.output_tokens)):[],j=S?qe.reduce((B,H)=>B+H.requests,0):null,et=S?qe.reduce((B,H)=>B+H.input_tokens+H.output_tokens,0):null,v=S?W.filter(B=>!Number.isFinite(B.input_tokens)||!Number.isFinite(B.output_tokens)).reduce((B,H)=>B+H.requests,0):null,L=Xh(W);return{requests:de,input:oe("input_tokens"),output:oe("output_tokens"),cost:oe("cost_microusd"),inputKnown:he.known,outputKnown:ke.known,costKnown:Ne.known,inputKnownRequests:he.knownRequests,outputKnownRequests:ke.knownRequests,inputUnknownRequests:he.unknownRequests,outputUnknownRequests:ke.unknownRequests,tokenKnownRequests:j,tokenKnownTotal:et,tokenUnknownRequests:v,costKnownRequests:Ne.knownRequests,costUnknownRequests:Ne.unknownRequests,inputCoverage:he.coverage,outputCoverage:ke.coverage,costCoverage:Ne.coverage,fallbacks:oe("fallback_count"),models:[...new Set(W.map(B=>B.actual_model).filter(B=>typeof B=="string"))],providers:[...new Set(W.map(B=>B.provider).filter(B=>typeof B=="string"))],...L,rows:W,router:R}}function _t(M){let R=y(M,"search"),S=R?.status==="available",W=S?R.rows:[],de=qe=>!S||W.some(j=>!Number.isFinite(j[qe]))?null:W.reduce((j,et)=>j+et[qe],0),oe=S?de("searches"):null,le=S?de("duration_ms"):null,he=S?W.length?Math.max(...W.map(qe=>qe.max_duration_ms).filter(Number.isFinite)):0:null,ke=Object.fromEntries(["fast","deep","browser"].map(qe=>[qe,S?W.filter(j=>j.route_mode===qe).reduce((j,et)=>j+(Number.isFinite(et.searches)?et.searches:0),0):null])),Ne=Xh(W);return{searches:oe,successful:S?de("successful_searches"):null,duration:le,avgLatency:oe==null||le==null?null:oe===0?0:le/oe,maxLatency:he,fallbacks:S?de("fallback_count"):null,cost:S?de("cost_microusd"):null,results:S?de("result_count"):null,extracts:S?de("extract_count"):null,providers:[...new Set(W.map(qe=>qe.provider).filter(qe=>typeof qe=="string"))],fallbackProviders:[...new Set(W.map(qe=>qe.fallback_provider).filter(qe=>typeof qe=="string"))],...Ne,routes:ke,search:R}}function Tt(){let M=y("majak","codex");return{source:M,row:M?.status==="available"&&M.rows.length===1?M.rows[0]:null}}function z(){return vn.flatMap(M=>Lt(M).rows.map(R=>({...R,profile:M})))}function Et(){let M=new Map;for(let R of z()){let S=R.actual_model;M.has(S)||M.set(S,{model:S,requests:0,fallbacks:0,successes:0,durationMs:0,durationRequests:0,inputTokens:0,outputTokens:0,tokenKnownRequests:0,tokenUnknownRequests:0});let W=M.get(S);W.requests+=R.requests,W.fallbacks+=R.fallback_count,W.successes+=R.successful_requests,Number.isFinite(R.duration_ms)&&(W.durationMs+=R.duration_ms,W.durationRequests+=R.requests),Number.isFinite(R.input_tokens)&&Number.isFinite(R.output_tokens)?(W.inputTokens+=R.input_tokens,W.outputTokens+=R.output_tokens,W.tokenKnownRequests+=R.requests):W.tokenUnknownRequests+=R.requests}return[...M.values()].sort((R,S)=>S.requests-R.requests||R.model.localeCompare(S.model))}function lt(){let M=k()?[...te(),...$("majak")]:$(),R=Ye=>M.filter(Ke=>Ke.status===Ye).length,S=R("running"),W=R("pending"),de=R("failed"),oe=R("blocked"),le=R("done"),he=oe+de,ke=Z(),Ne=at().filter(Ye=>Ye.profile==="majak"&&Ye.status==="working").length,qe=k()?ke===null?null:ke.filter(Ye=>Ye.status==="working").length+Ne:at().filter(Ye=>Ye.status==="working").length,j=M.reduce((Ye,Ke)=>Ye+(Number.isSafeInteger(Ke.attempts)?Math.max(0,Ke.attempts):0),0),et=le+de,v=et?Math.round(le/et*100):null,L=vn.map(Lt),B=L.every(Ye=>Ye.router?.status==="available"),H=B?L.reduce((Ye,Ke)=>Ye+(Ke.tokenKnownTotal||0),0):null,q=B?L.reduce((Ye,Ke)=>Ye+(Ke.tokenKnownRequests||0),0):null,Te=B?L.reduce((Ye,Ke)=>Ye+(Ke.tokenUnknownRequests||0),0):null,Ie=B?L.reduce((Ye,Ke)=>Ye+(Ke.costKnown||0),0):null,Ae=B?L.reduce((Ye,Ke)=>Ye+(Ke.costKnownRequests||0),0):null,Oe=B?L.reduce((Ye,Ke)=>Ye+(Ke.costUnknownRequests||0),0):null,ze=Et(),tt=ze.reduce((Ye,Ke)=>Ye+Ke.durationMs,0),$e=ze.reduce((Ye,Ke)=>Ye+Ke.durationRequests,0),Ue=$e?tt/$e:null,ft=L.every(Ye=>Ye.fallbacks!=null)?L.reduce((Ye,Ke)=>Ye+Ke.fallbacks,0):null;return{queue:M,running:S,waiting:W,blocked:he,blockedOnly:oe,done:le,failed:de,activeAgents:qe,retries:j,success:v,activeQueue:S+W+oe,tokenTotal:H,tokenKnownRequests:q,tokenUnknownRequests:Te,cost:Ie,costKnownRequests:Ae,costUnknownRequests:Oe,requestLatency:Ue,fallbacks:ft,models:ze}}function P(){let M=e("#swarm-kpis");if(!M)return;if(!n){M.innerHTML='<div class="swarm-kpi"><span>Swarm</span><b>\u2014</b><small>telemetrie nedostupn\xE1</small></div>';return}let R=lt(),S=R.tokenTotal==null||!R.tokenKnownRequests?"\u2014":Zi.format(R.tokenTotal),W=R.cost==null||!R.costKnownRequests?"\u2014":Ii(R.cost),de=[["Active",R.activeAgents==null?"\u2014":R.activeAgents,R.activeAgents==null?"live runtime nedostupn\xFD":"\u017Eiv\xED pracuj\xEDc\xED agenti",R.activeAgents?"running":""],["Running",R.running,"durable b\u011B\u017E\xEDc\xED tasky",R.running?"running":""],["Waiting",R.waiting,"durable pending",R.waiting?"waiting":""],["Blocked / Failed",`${R.blockedOnly} / ${R.failed}`,"blocked nyn\xED / failed historie",R.blocked?"blocked":""],["Queue",R.activeQueue,"netermin\xE1ln\xED durable tasky",""],["Durable success",R.success==null?"\u2014":`${R.success} %`,`${R.done} done \xB7 ${R.failed} failed v historii`,""],["Retries",R.retries,"durable retry counter",R.retries?"waiting":""],["Avg task","\u2014","task duration se nem\u011B\u0159\xED",""],["Tokens",S,R.tokenKnownRequests==null?"router telemetry nedostupn\xE1":`${R.tokenKnownRequests} req known \xB7 ${R.tokenUnknownRequests||0} unknown`,""],["Cost known",W,R.costKnownRequests==null?"router telemetry nedostupn\xE1":`${R.costKnownRequests} req ocen\u011Bno \xB7 ${R.costUnknownRequests||0} unknown`,""]];M.innerHTML=de.map(([oe,le,he,ke])=>`<article class="swarm-kpi" data-state="${ke}"><span>${ye(oe)}</span><b>${ye(String(le))}</b><small>${ye(he)}</small></article>`).join("")}function _(M){return[{running:0,blocked:1,failed:2,pending:3,done:4}[M.status]??9,-(M.updated_at||0),M.task_id]}function X(){return[...se()].sort((M,R)=>{let S=_(M),W=_(R);return S[0]-W[0]||S[1]-W[1]||String(S[2]).localeCompare(String(W[2]))})}function K(M){return c==="all"?!0:c==="blocked"?M.status==="blocked"||M.status==="failed":M.status===c}function ae(M){let R=M.raw_state||hn[M.status]||M.status,S=M.attempt_state&&M.attempt_state!==R?`${R} \xB7 ${M.attempt_state}`:R;return`<button type="button" class="taskgraph-node" role="option" aria-selected="${String(l===M.task_id)}" data-task-id="${ye(M.task_id)}" data-status="${ye(M.status)}"><b>${ye(jt(M))} \xB7 ${ye(M.task_id)}</b><span>${ye(S)}</span><small>${ye(M.issue_title||M.kind)} \xB7 pokus ${ye(it(M))}</small></button>`}function be(M,R,S){if(!R.length)return"";let W=R.slice(0,S),de=R.length-W.length;return`<div class="taskgraph-lane" role="group" aria-label="${ye(M)}"><span class="taskgraph-lane-label">${ye(M)}</span><div class="taskgraph-lane-track">${W.map(ae).join("")}${de?`<div class="taskgraph-node taskgraph-cluster" data-status="pending"><b>+${de} uzl\u016F</b><span>LOD cluster</span><small>dal\u0161\xED sanitizovan\xE9 tasky</small></div>`:""}</div></div>`}function Ee(M,R){let S=M.filter(oe=>R.has(oe.from_task)&&R.has(oe.to_task));if(!S.length)return"";let W=S.slice(0,16),de=S.length-W.length;return`<div class="taskgraph-edge-strip" aria-label="Autoritativn\xED DAG hrany">${W.map(oe=>`<span class="taskgraph-edge" data-edge-kind="${ye(oe.kind)}"><b>${ye(oe.from_task)}</b><i>\u2192</i><b>${ye(oe.to_task)}</b><small>${ye(oe.kind)}</small></span>`).join("")}${de?`<span class="taskgraph-edge taskgraph-edge-overflow">+${de} hran</span>`:""}</div>`}function N(){let M=e("#taskgraph-nodes"),R=e("#taskgraph-status");if(!M||!R)return;let S=D(),W=w().filter(j=>j.status==="available"),de=k()?S:W.length?{status:"available",observed_at:Math.max(...W.map(j=>j.observed_at||0))}:null;if(!de||de.status!=="available"){R.textContent="Task telemetry nen\xED dostupn\xE1.",M.innerHTML='<div class="obs-empty">TaskGraph nelze zobrazit bez durable queue.</div>',C("setTasks",[]);return}let oe=X(),le=oe.filter(K);document.querySelectorAll("[data-task-filter]").forEach(j=>j.setAttribute("aria-pressed",String(j.dataset.taskFilter===c)));let he=c==="all"?"v\u0161echny stavy":c==="pending"?"\u010Dekaj\xEDc\xED":c==="blocked"?"blocked + failed":c,ke=ce();if(R.textContent=k()?`Autoritativn\xED Herdr DAG \xB7 ${ke.length} hran \xB7 filtr: ${he}.`:`Dependency telemetry nen\xED v aktu\xE1ln\xEDm kontraktu \xB7 hrany se nevym\xFD\u0161lej\xED \xB7 filtr: ${he}.`,!oe.length){M.innerHTML='<div class="obs-empty">Durable queue je pr\xE1zdn\xE1.</div>',C("setTasks",[]);return}if(!le.length){M.innerHTML='<div class="obs-empty">Pro zvolen\xFD filtr nejsou \u017E\xE1dn\xE9 tasky.</div>',C("setTasks",oe.filter(j=>j.status!=="done"));return}let Ne=k()?Ee(ke,new Set(le.map(j=>j.task_id))):"";if(c==="all"){let j=le.filter(v=>["running","blocked","failed"].includes(v.status)),et=le.filter(v=>!["running","blocked","failed"].includes(v.status));M.innerHTML=Ne+be("Aktivn\xED / probl\xE9mov\xE9",j,10)+be("\u010Cekaj\xEDc\xED / hotov\xE9",et,14)}else M.innerHTML=Ne+be(he,le,18);let qe=[...M.querySelectorAll("[data-task-id]")];qe.forEach((j,et)=>{j.addEventListener("click",()=>Hs(j.dataset.taskId)),j.addEventListener("keydown",v=>{if(!["ArrowRight","ArrowLeft","ArrowDown","ArrowUp","Home","End","Enter"," "].includes(v.key))return;if(v.key==="Enter"||v.key===" "){v.preventDefault(),Hs(j.dataset.taskId);return}v.preventDefault();let L=v.key==="ArrowDown"?2:v.key==="ArrowUp"?-2:v.key==="ArrowRight"?1:v.key==="ArrowLeft"?-1:0,B=v.key==="Home"?0:v.key==="End"?qe.length-1:Math.max(0,Math.min(qe.length-1,et+L));qe[B]?.focus()})}),C("setTasks",oe.filter(j=>j.status!=="done"))}function V(){let M=e("#swarm-analytics-grid");if(!M)return;if(!n){M.innerHTML='<article class="swarm-card"><header><h3>Swarm</h3></header><strong>\u2014</strong><p>\u017Div\xE1 telemetrie nen\xED dostupn\xE1.</p></article>';return}let R=lt(),S=R.queue.length||1,W=`<div class="swarm-mini">${["running","pending","blocked","failed","done"].map(ke=>{let Ne=R.queue.filter(qe=>qe.status===ke).length;return Ne?`<i class="${ke}" style="width:${(Ne/S*100).toFixed(1)}%" title="${ye(hn[ke]||ke)}: ${Ne}"></i>`:""}).join("")}</div>`,de=R.inputTokens==null||R.outputTokens==null?"\u2014":Zi.format(R.inputTokens+R.outputTokens),oe=R.cost==null?"\u2014":Ii(R.cost),le=R.models.slice(0,4),he=le.length?le.map(ke=>`${ye(ke.model)} ${Ft.format(ke.requests)}`).join(" \xB7 "):"Model telemetry nen\xED dostupn\xE1.";M.innerHTML=['<article class="swarm-card"><header><h3>Throughput</h3><span>tasks / time</span></header><strong>\u2014</strong><p>\u010Casov\xE1 \u0159ada dokon\u010Den\xFDch task\u016F nen\xED v autoritativn\xEDm kontraktu; hodnotu neodhadujeme.</p></article>',`<article class="swarm-card"><header><h3>Queue depth</h3><span>snapshot</span></header><strong>${Ft.format(R.activeQueue)}</strong>${W}<p>${R.running} running \xB7 ${R.waiting} waiting \xB7 ${R.blockedOnly} blocked \xB7 ${R.failed} failed \xB7 ${R.done} done</p></article>`,`<article class="swarm-card"><header><h3>Latency</h3><span>router request avg</span></header><strong>${ye(ji(R.requestLatency))}</strong><p>Task queue/review p50+p95 nejsou dostupn\xE9; zobrazen je pouze m\u011B\u0159en\xFD router request pr\u016Fm\u011Br.</p></article>`,`<article class="swarm-card"><header><h3>Tokens & cost</h3><span>known telemetry</span></header><strong>${ye(de)}</strong><p>${ye(oe)} known \xB7 ${R.costUnknownRequests||0} req unknown \xB7 ${R.tokenUnknownRequests||0} token fields unknown.</p></article>`,`<article class="swarm-card"><header><h3>Model mix</h3><span>requests</span></header><strong>${Ft.format(R.models.reduce((ke,Ne)=>ke+Ne.requests,0))}</strong><p>${he}</p></article>`,`<article class="swarm-card"><header><h3>Reliability</h3><span>snapshot</span></header><strong>${Ft.format(R.retries)}</strong><p>true retries \xB7 ${R.blockedOnly} blocked \xB7 ${R.failed} failed \xB7 ${Pt(R.fallbacks)} model fallback\u016F.</p></article>`].join("")}function ie(){P(),N(),V()}function ge(M){return Number.isFinite(M)?new Date(M*1e3).toLocaleString("cs-CZ",{day:"2-digit",month:"2-digit",hour:"2-digit",minute:"2-digit"}):"Nezn\xE1m\xFD"}function ue(M){if(!Number.isFinite(M))return"\u010Das resetu nen\xED dostupn\xFD";let R=Math.max(0,M-Date.now()/1e3),S=Math.ceil(R/3600);return S<48?`za ${S} h`:`za ${Math.ceil(S/24)} dn\xED`}function pe(M,R,{id:S,suffix:W="",maxValue:de=null}={}){if(!M.length)return'<div class="obs-empty">Zat\xEDm bez \u010Dasov\xE9 \u0159ady.</div>';let oe=680,le=178,he=42,ke=12,Ne=12,qe=26,j=M.map($e=>Number($e[R])).filter(Number.isFinite);if(!j.length)return'<div class="obs-empty">Zat\xEDm bez m\u011B\u0159en\xFDch hodnot.</div>';let et=Math.max(de??0,...j,1),v=$e=>M.length===1?(he+oe-ke)/2:he+$e/(M.length-1)*(oe-he-ke),L=$e=>Ne+(1-Math.max(0,$e)/et)*(le-Ne-qe),B=M.map(($e,Ue)=>[v(Ue),L(Number($e[R]))]),H=B.map(([$e,Ue],ft)=>`${ft?"L":"M"}${$e.toFixed(1)},${Ue.toFixed(1)}`).join(" "),q=`${H} L${v(M.length-1).toFixed(1)},${le-qe} L${v(0).toFixed(1)},${le-qe} Z`,Te=M[0].day||hi(M[0].at),Ie=M[Math.floor((M.length-1)/2)],Ae=Ie.day||hi(Ie.at),Oe=M[M.length-1],ze=Oe.day||hi(Oe.at),tt=ye(S||"obs");return`<svg class="obs-chart" viewBox="0 0 ${oe} ${le}" role="img">
      <defs><linearGradient id="${tt}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#70ddd0"/><stop offset="1" stop-color="#70ddd0" stop-opacity="0"/></linearGradient></defs>
      ${[0,.25,.5,.75,1].map($e=>`<line class="grid" x1="${he}" y1="${(Ne+$e*(le-Ne-qe)).toFixed(1)}" x2="${oe-ke}" y2="${(Ne+$e*(le-Ne-qe)).toFixed(1)}"/>`).join("")}
      <path class="area" style="fill:url(#${tt})" d="${q}"/><path class="line" d="${H}"/>
      ${B.slice(-12).map(([$e,Ue])=>`<circle class="point" cx="${$e.toFixed(1)}" cy="${Ue.toFixed(1)}" r="2.1"/>`).join("")}
      <text class="axis" x="2" y="${Ne+4}">${ye(Zi.format(et)+W)}</text><text class="axis" x="2" y="${le-qe+3}">0${ye(W)}</text>
      <text class="axis" x="${he}" y="${le-7}">${ye(Te)}</text><text class="axis" text-anchor="middle" x="${(oe/2).toFixed(1)}" y="${le-7}">${ye(Ae)}</text><text class="axis" text-anchor="end" x="${oe-ke}" y="${le-7}">${ye(ze)}</text>
    </svg>`}function _e(M,R,S,{percent:W=!1,alert:de=!1}={}){if(!M.length)return'<div class="obs-empty">\u017D\xE1dn\xE1 m\u011B\u0159en\xE1 data.</div>';let oe=Math.max(...M.map(R),W?100:1);return`<div class="obs-bars">${M.map(le=>{let he=R(le),ke=oe?Math.max(1,he/oe*100):0;return`<div class="obs-bar" data-alert="${de?String(de(le)):"false"}"><label title="${ye(le.model||le.label)}">${ye(le.model||le.label)}</label><div class="obs-bar-track"><i class="obs-bar-fill" style="--bar:${ke.toFixed(1)}%"></i></div><strong>${ye(S(he,le))}</strong></div>`}).join("")}</div>`}function Se(){if(s)return r;if(!n)return"offline";let M=k(),R=at();if(M){let de=te(),oe=de.filter(L=>L.status==="blocked"),le=Z(),he=R.filter(L=>L.profile==="majak"),ke=$("majak"),Ne=y("majak","herdr"),qe=n.sources.some(L=>L.profile==="majak");if(oe.some(L=>ne.has(L.blocker))||(le?.some(L=>L.status==="blocked")??!1)||he.some(L=>L.status==="blocked")||xe("quantlab").length||xe("majak").length)return"waiting_user";if(qe&&(!Ne||Ne.status!=="available"))return de.length||R.length?"error":"offline";if((le?.some(L=>L.status==="working")??!1)||re().length||de.some(L=>L.status==="running")||he.some(L=>L.status==="working")||ke.some(L=>L.status==="running"))return"working";if(oe.length||Pe("majak").length)return"waiting_result";let v=ke.some(L=>L.status!=="done");return de.length&&de.every(L=>L.raw_state==="done")&&!v?"complete":(he.some(L=>L.status==="idle"),"idle")}let S=R.filter(de=>Kr(de.agent)==="hermes"),W=$();return R.some(de=>de.status==="blocked")||xe().length?"waiting_user":n.sources.some(de=>de.kind==="herdr"&&de.status!=="available")?R.length?"error":"offline":S.some(de=>de.status==="working")||W.some(de=>de.status==="running")?"working":Pe().length?"waiting_result":S.some(de=>de.status==="idle")?"idle":S.length&&S.every(de=>de.status==="done")?"complete":"offline"}function Be(){return Vh.has(o)?o:"majak-codex"}function O(M){if(s)return`DEMO \xB7 ${Vs[M].copy}`;let R=k(),S=at(),W=Z(),de=R?[...(W||[]).filter(le=>le.status==="working").map(le=>le.agent_id),...S.filter(le=>le.profile==="majak"&&le.status==="working").map(le=>le.agent)]:S.filter(le=>le.status==="working").map(le=>le.agent),oe=R?te().find(le=>le.status==="running")||Q()||$("majak").find(le=>le.status==="running")||null:Re();if(M==="working"&&oe){let le=oe.repo==="Bbambaaamm/dotacni-majak"?"Maj\xE1k":oe.repo==="Bbambaaamm/herdr"?"Herdr":"QuantLab",he=oe.raw_state||oe.status,ke=oe.attempt_state&&oe.attempt_state!==he?` / ${oe.attempt_state}`:"",Ne=W?.some(j=>j.status==="working")??!1;if(R&&!Ne)return`${le} ${jt(oe)} \xB7 ${oe.task_id} \xB7 durable ${he}${ke} \xB7 \u017Eiv\xFD runtime nepotvrzen.`;let qe=ke?` \xB7 durable ${he}${ke}`:"";return`${le} ${jt(oe)} \xB7 ${oe.task_id} \xB7 live pr\xE1ce prob\xEDh\xE1${qe}.`}if(M==="working"||M==="idle"&&de.length)return`Pracuj\xED: ${de.join(", ")}. P\u0159esn\xFD \xFAkol zdroj neposkytuje.`;if(M==="waiting_user"){let le=[...new Set([...(W||[]).filter(Ne=>Ne.status==="blocked").map(Ne=>Ne.agent_id),...at().filter(Ne=>Ne.status==="blocked"&&(!R||Ne.profile==="majak")).map(Ne=>Ne.agent)])],he=R?[...te(),...xe()]:xe(),ke=[...new Map(he.map(Ne=>[Ne.task_id,Ne])).values()].filter(Ne=>Ne.status==="blocked"&&ne.has(Ne.blocker)).map(Ne=>`${jt(Ne)} ${Ne.task_id}`);return`Zkontrolujte: ${[...le,...ke].join(", ")||"blokovanou \xFAlohu"}.`}return M==="waiting_result"?`Technicky blokov\xE1no: ${(R?te():Pe()).filter(he=>he.status==="blocked"&&!ne.has(he.blocker)).map(he=>`${jt(he)} ${he.blocker||he.task_id}`).join(", ")||"intern\xED kontrola"}.`:M==="offline"?p:M==="error"?n.sources.filter(le=>le.status==="unavailable"&&le.reason!=="not_configured").map(le=>`${le.profile}/${le.kind}: ${le.reason}`).join(" \xB7 ")||"\u017Div\xFD stav jednoho projektu nen\xED dostupn\xFD.":Vs[M].copy}function Me(){let M=Se(),R=Vs[M],S=e_(R.tone),W=Re()||Q(),de=Je(W?.agent||null),oe=de?.task_id===W?.task_id?null:de;t.faceState.textContent=R.label,t.faceTask.textContent=O(M),t.coordinatorCurrent.textContent=s?`DEMO \xB7 ${Vs[M].label}`:dt(W),t.coordinatorNext.textContent=s?`DEMO \xB7 ${Be()}`:dt(oe),t.coordinatorCurrent.title=t.coordinatorCurrent.textContent,t.coordinatorNext.title=t.coordinatorNext.textContent,t.faceSignal.style.background=S,t.faceSignal.style.color=S,t.faceSignal.style.boxShadow=h?"none":`0 0 13px ${S}`,M!==d&&(C("setState",M),d=M);let le=k(),he=le?[...te(),...$("majak")]:$(),ke=at().filter(B=>B.status==="working"),Ne=ke.filter(B=>B.profile==="majak"),j=(le?Z():null)?.filter(B=>B.status==="working")||null,et=le?re():null;C("setActivity",{running:he.filter(B=>B.status==="running").length,pending:he.filter(B=>B.status==="pending").length,blocked:he.filter(B=>B.status==="blocked").length,userBlocked:xe().length,workingAgents:le?(j?j.length:et.length)+Ne.length:ke.length,activeAgent:le?j?.[0]?.agent_id||et[0]?.agent_id||Ne[0]?.agent||null:A(W?.agent)||ke[0]?.agent||null});let v=Be(),L=`${s}:${r}:${v}`;L!==g&&(C("setDemo",{enabled:s,state:r,target:v}),g=L),t.attention.hidden=s||!["waiting_user","error","offline"].includes(M),t.attention.textContent=M==="offline"?"Obnovit data":M==="waiting_user"?"Otev\u0159\xEDt blokovan\xE9ho agenta":"Zkontrolovat zdroje"}function J(M){let R=Kr(M.agent),S=s?"Uk\xE1zkov\xFD stroj \xB7 syntetick\xFD":M.unavailable?"Stav nen\xED dostupn\xFD":R==="hermes"?"Koordin\xE1tor":"V\xFDvojov\xFD agent",W=s?M.agent===Be()?r:"idle":M.status,de=s?`DEMO \xB7 ${Vs[W].label}`:Uc(W);return`<button class="agent-node" data-agent="${ye(M.agent)}" data-state="${ye(W)}" aria-label="${ye(`${M.agent}: ${de}`)}"><span class="agent-copy"><b>${ye(M.agent)}</b><small>${S}</small></span><span class="state-chip">${ye(de)}</span></button>`}function ve(){let M=[],R=0;for(let S of vn){let W=at().filter(j=>j.profile===S),de=["hermes","codex"].map(j=>W.find(et=>et.agent===`${S}-${j}`)||{agent:`${S}-${j}`,profile:S,status:"offline",unavailable:!0}),oe=W.filter(j=>!Vh.has(j.agent));R+=oe.length;let le=oe.length?`<button type="button" class="scene-overflow" data-overflow-profile="${S}">+${oe.length} dal\u0161\xEDch agent\u016F \u2014 pracovn\xED p\u0159ehled</button>`:"";e(`#${S}-agents`).innerHTML=de.map(J).join("")+le;let he=W.length?W:de,ke=T(S),Ne=xe(S).length,qe=Pe(S).length;e(`#${S}-project-state`).textContent=he.some(j=>j.status==="blocked")||Ne?"z\xE1sah":he.some(j=>j.status==="working")||ke.some(j=>j.status==="running")?"pracuje":qe?"\u010Dek\xE1":he.every(j=>j.unavailable)?"bez dat":"klid",M.push(...de.map(j=>({...j,id:j.agent,role:Kr(j.agent),visible:!e(`#${S}-agents`).hidden})))}t.film.querySelectorAll("[data-agent]").forEach(S=>S.addEventListener("click",()=>sn(S.dataset.agent))),t.film.querySelectorAll("[data-overflow-profile]").forEach(S=>S.addEventListener("click",()=>di("work"))),e("#data-caveat").textContent=R?`3D sc\xE9na zobrazuje \u010Dty\u0159i zn\xE1m\xE9 stroje. Dal\u0161\xEDch ${R} agent\u016F je v pracovn\xEDm p\u0159ehledu. Nezn\xE1m\xE9 metriky nejsou odhady.`:"Nezn\xE1m\xE9 hodnoty z\u016Fst\xE1vaj\xED nezn\xE1m\xE9.",C("setAgents",M),e("#link-layer").replaceChildren()}function we(){if(!n){t.snapshotAge.textContent="Nedostupn\xE9",t.agentCount.textContent="Nezn\xE1m\xE9",t.queueCount.textContent="Nedostupn\xE9",t.requestCount.textContent="Nedostupn\xE9",t.searchCount.textContent="Nedostupn\xE9",t.searchLatency.textContent="Nedostupn\xE9",t.costTotal.textContent="Nedostupn\xE9",e("#work-freshness").textContent=p;return}let M=vn.map(Lt),R=j=>M.every(et=>et[j]!=null)?M.reduce((et,v)=>et+v[j],0):null,S=vn.map(_t),W=j=>S.every(et=>et[j]!=null)?S.reduce((et,v)=>et+v[j],0):null,de=W("searches"),oe=W("duration");t.snapshotAge.textContent=ui(n.generated_at);let le=vn.every(j=>y(j,"herdr")?.status==="available");t.agentCount.textContent=le?String(at().length):`${at().length} ov\u011B\u0159eno \xB7 \u010D\xE1st nedostupn\xE1`;let he=[...new Set(n.sources.map(j=>j.profile))],ke=w(),Ne=he.length>0&&he.every(j=>y(j,"queue")?.status==="available");t.queueCount.textContent=Ne?String(Xe().length):"Nedostupn\xE9",t.requestCount.textContent=Pt(R("requests")),t.searchCount.textContent=Pt(de),t.searchLatency.textContent=ji(de==null||oe==null?null:de===0?0:oe/de);let qe=Tt().row;t.costTotal.textContent=qe?`${100-qe.used_percent} %`:"Nedostupn\xE9",t.costTotal.title=qe?`Reset ${ge(qe.resets_at)}`:"Codex usage snapshot nen\xED dostupn\xFD",e("#work-freshness").textContent=`\u017Div\xFD snapshot p\u0159ed ${ui(n.generated_at)}`}function fe(){let M=e("#observability-kpis"),R=e("#observability-grid");if(!n){M.innerHTML="",R.innerHTML='<article class="obs-panel full"><div class="obs-empty">\u017Div\xE1 telemetrie nen\xED dostupn\xE1.</div></article>';return}let S=Tt().row,W=S?.routing_status==="available",de=W?[{label:"FREE",value:S.routing_free},{label:"Sol",value:S.routing_sol},{label:"Astra",value:S.routing_astra}]:[],oe=vn.map(Lt),le=oe.every(me=>me.router?.status==="available"),he=le?oe.reduce((me,He)=>me+He.requests,0):null,ke=le?oe.reduce((me,He)=>me+He.costKnown,0):null,Ne=le?oe.reduce((me,He)=>me+(He.costKnownRequests||0),0):null,qe=le?oe.reduce((me,He)=>me+He.costUnknownRequests,0):null,j=lt(),et=j.activeAgents,v=j.activeQueue,L=S?100-S.used_percent:null,B=L==null?"warn":L<=5?"critical":L<=25?"warn":"ok",H=ke==null?"Nedostupn\xE9":Ne?qe?`${Ii(ke)} zn\xE1m\xE9 \xB7 ${Ft.format(qe)} req bez ceny`:Ii(ke):`0 req ocen\u011Bno \xB7 ${Ft.format(qe||0)} unknown`;M.innerHTML=[`<article class="obs-kpi" data-severity="${B}"><span>Codex allowance \xB7 zb\xFDv\xE1</span><b>${L==null?"\u2014":L+" %"}</b><div class="obs-gauge"><i style="--gauge:${S?S.used_percent:0}%"></i></div><small>${S?S.ordinary_usage_allowed?"B\u011B\u017En\xE9 pou\u017Eit\xED povoleno":"Limit vy\u010Derp\xE1n":"Zdroj nedostupn\xFD"}</small></article>`,`<article class="obs-kpi"><span>Dal\u0161\xED reset Codex</span><b>${S?ye(ge(S.resets_at)):"\u2014"}</b><small>${S?ye(ue(S.resets_at)):"\u010Cas resetu nen\xED dostupn\xFD"}</small></article>`,`<article class="obs-kpi"><span>Codex lifetime tokeny</span><b>${S?.lifetime_tokens==null?"\u2014":ye(Zi.format(S.lifetime_tokens))}</b><small>Peak/day: ${S?.peak_daily_tokens==null?"\u2014":ye(Zi.format(S.peak_daily_tokens))}</small></article>`,`<article class="obs-kpi"><span>Router po\u017Eadavky</span><b>${Pt(he)}</b><small>${le?`${Ft.format(oe.reduce((me,He)=>me+(He.fallbacks||0),0))} fallback\u016F${W?` \xB7 Astra eskalace ${Ft.format(S.routing_astra_escalations)}`:""}`:"\u010D\xE1st router\u016F nedostupn\xE1"}</small></article>`,`<article class="obs-kpi"><span>Variabiln\xED n\xE1klady</span><b>${ke==null||!Ne?"\u2014":ye(Ii(ke))}</b><small>${ye(H)}</small></article>`,`<article class="obs-kpi" data-severity="${v?"warn":"ok"}"><span>Aktivn\xED pr\xE1ce</span><b>${et==null?"\u2014":Ft.format(et)} agent \xB7 ${Ft.format(v)} fronta</b><small>${et==null?"Live runtime nedostupn\xFD \xB7 ":""}${v?"Durable fronta m\xE1 netermin\xE1ln\xED \xFAlohy":"Durable fronta bez aktivn\xEDch polo\u017Eek"}</small></article>`].join("");let q=Et(),Te=q.slice(0,8),Ie=q.filter(me=>me.requests>0).map(me=>({...me,rate:me.fallbacks/me.requests*100})).sort((me,He)=>He.rate-me.rate||He.requests-me.requests).slice(0,8),Ae=q.filter(me=>me.durationRequests>0).map(me=>({...me,avg:me.durationMs/me.durationRequests})).sort((me,He)=>He.avg-me.avg).slice(0,8),Oe=q.filter(me=>me.tokenKnownRequests>0).map(me=>({...me,tokens:me.inputTokens+me.outputTokens})).sort((me,He)=>He.tokens-me.tokens||He.requests-me.requests).slice(0,8),ze=oe.every(me=>me.requests!=null)?oe.reduce((me,He)=>me+He.requests,0):0,tt=(me,He)=>{let It=oe.reduce((Tn,Gn)=>Tn+(Gn[me]??0),0),Hn=oe.reduce((Tn,Gn)=>Tn+(Gn[He]??0),0),At=It+Hn;return At?Math.round(It/At*100):ze===0?100:0},$e=[["Input tokeny",tt("inputKnownRequests","inputUnknownRequests")],["Output tokeny",tt("outputKnownRequests","outputUnknownRequests")],["USD n\xE1klady",tt("costKnownRequests","costUnknownRequests")]],Ue=T(),ft=Object.fromEntries(Object.keys(hn).map(me=>[me,Ue.filter(He=>He.status===me).length])),Ye=Object.values(ft).reduce((me,He)=>me+He,0),Ke=Ge(),wt=Ce(),Ot=ut(),Fe=wt.filter(me=>me.event==="allow"),Xt=[...new Map(Ot.slice().reverse().map(me=>[me.reason,me])).values()].slice(0,6),vt=vn.map(_t),fn=["fast","deep","browser"].map(me=>({label:me.toUpperCase(),value:vt.every(He=>He.routes[me]!=null)?vt.reduce((He,It)=>He+It.routes[me],0):0})),pn=(S?.daily||[]).map(me=>({day:me.day.slice(5),tokens:me.tokens})),Ln=S?.limit_history||[];R.innerHTML=[`<article class="obs-panel wide"><header><div><h3>Codex tokeny po dnech</h3><span>45 posledn\xEDch m\u011B\u0159en\xFDch dn\xED</span></div><span>${pn.length?"peak "+ye(Zi.format(Math.max(...pn.map(me=>me.tokens)))):"bez dat"}</span></header>${pe(pn,"tokens",{id:"codexTokensArea"})}<p class="obs-note">Account-wide token activity z Codex app-serveru. Nen\xED p\u0159ev\xE1d\u011Bna na API cenu.</p></article>`,`<article class="obs-panel"><header><div><h3>Codex allowance</h3><span>\u010Dasov\xE1 \u0159ada vyu\u017Eit\xED</span></div><span>${S?S.used_percent+" % pou\u017Eito":"nedostupn\xE9"}</span></header>${pe(Ln,"used_percent",{id:"codexLimitArea",suffix:" %",maxValue:100})}<p class="obs-note">${Ln.length<2?"Historii jsme pr\xE1v\u011B za\u010Dali sb\xEDrat; graf se bude plnit automaticky.":"Snapshot ka\u017Ed\xFDch p\u0159ibli\u017En\u011B 5 minut."}${W?` \xB7 Router soft ${Ft.format(S.routing_soft_limit_pct)} % / hard ${Ft.format(S.routing_hard_limit_pct)} %.`:""}</p></article>`,`<article class="obs-panel"><header><div><h3>Cost-aware router</h3><span>FREE / Sol / Astra \xB7 task decisions</span></div><span>${W?ye(S.routing_policy_version):"nedostupn\xE9"}</span></header>${_e(de,me=>me.value,me=>Ft.format(me))}<div class="obs-legend"><span>Astra eskalace: ${W?Ft.format(S.routing_astra_escalations):"\u2014"}</span><span>Premium blokov\xE1no: ${W?Ft.format(S.routing_premium_denied):"\u2014"}</span></div><p class="obs-note">${W?`Posledn\xED route: ${ye(S.last_route_model||"\u2014")} \xB7 ${ye(S.last_route_reason||"\u2014")}`:"Routing telemetry nen\xED dostupn\xE1."}</p></article>`,`<article class="obs-panel"><header><div><h3>Model traffic</h3><span>po\u010Det skute\u010Dn\xFDch provider request\u016F</span></div><span>top 8</span></header>${_e(Te,me=>me.requests,me=>Ft.format(me))}</article>`,`<article class="obs-panel"><header><div><h3>Model tokeny</h3><span>skute\u010Dn\u011B zm\u011B\u0159en\xE9 router requesty</span></div><span>top 8</span></header>${_e(Oe,me=>me.tokens,me=>Zi.format(me))}<p class="obs-note">Per-model tokeny jsou autoritativn\xED pro Hermes router. Codex Sol/Astra zde nejsou odhadov\xE1ny; jejich account-wide tokeny z\u016Fst\xE1vaj\xED v samostatn\xE9m grafu.</p></article>`,`<article class="obs-panel"><header><div><h3>Fallback pressure</h3><span>fallbacky / po\u017Eadavky</span></div><span>vy\u0161\u0161\xED = hor\u0161\xED</span></header>${_e(Ie,me=>me.rate,me=>me.toFixed(1)+" %",{percent:!0,alert:me=>me.rate>=25})}</article>`,`<article class="obs-panel"><header><div><h3>Model latency</h3><span>pr\u016Fm\u011Br na request</span></div><span>jen zn\xE1m\xE1 latence</span></header>${_e(Ae,me=>me.avg,me=>ji(me))}</article>`,`<article class="obs-panel"><header><div><h3>Data coverage</h3><span>request-weighted completeness</span></div><span>fail-closed</span></header>${$e.map(([me,He])=>`<div class="coverage-row"><span>${ye(me)}</span><div class="coverage-track"><i style="width:${He}%"></i></div><strong>${He} %</strong></div>`).join("")}<p class="obs-note">100 % znamen\xE1, \u017Ee ka\u017Ed\xE9mu requestu odpov\xEDd\xE1 m\u011B\u0159en\xE1 hodnota. Chyb\u011Bj\xEDc\xED hodnoty nejsou dopo\u010D\xEDt\xE1ny.</p></article>`,`<article class="obs-panel"><header><div><h3>Durable queue</h3><span>stav pr\xE1ce QuantLab</span></div><span>${Ye} z\xE1znam\u016F</span></header>${Ye?`<div class="queue-strip">${Object.entries(ft).filter(([,me])=>me).map(([me,He])=>`<i class="${me}" style="width:${(He/Ye*100).toFixed(1)}%" title="${ye(hn[me])}: ${He}"></i>`).join("")}</div><div class="obs-legend">${Object.entries(ft).map(([me,He])=>`<span>${ye(hn[me])}: ${He}</span>`).join("")}</div>`:'<div class="obs-empty">Fronta je pr\xE1zdn\xE1.</div>'}</article>`,`<article class="obs-panel"><header><div><h3>Swarm admission</h3><span>ALLOW / DENY p\u0159ed spawnem</span></div><span>${Ke?.status==="available"?`${Fe.length} / ${Ot.length}`:"nedostupn\xE9"}</span></header>${Ke?.status==="available"?`<div class="obs-legend"><span>ALLOW: ${Fe.length}</span><span>DENY: ${Ot.length}</span></div>${Xt.length?`<div class="admission-reasons">${Xt.map(me=>`<span><b>${ye(me.reason)}</b> \xB7 ${ye(me.repo)} #${ye(me.issue)} \xB7 ${ye(ui(me.observed_at))}</span>`).join("")}</div>`:'<p class="obs-note">V aktu\xE1ln\xEDm bounded tail nejsou \u017E\xE1dn\xE9 denialy.</p>'}<p class="obs-note">Zobrazeny jsou pouze sanitizovan\xE9 reason codes a DAG scope. Prompt, detail toolu ani secrets se neexportuj\xED.</p>`:'<div class="obs-empty">Admission audit nen\xED v aktu\xE1ln\xEDm snapshotu dostupn\xFD.</div>'}</article>`,`<article class="obs-panel"><header><div><h3>Search route mix</h3><span>Fast / Deep / Browser</span></div><span>aktu\xE1ln\xED snapshot</span></header>${_e(fn,me=>me.value,me=>Ft.format(me))}</article>`,`<article class="obs-panel"><header><div><h3>Codex \xFA\u010Det</h3><span>read-only stav</span></div><span>data p\u0159ed ${Tt().source?ye(ui(Tt().source.observed_at)):"\u2014"}</span></header><div class="obs-legend"><span>Kredity: ${S?ye(S.credits_balance??"nezn\xE1m\xE9"):"\u2014"}</span><span>Reset kredity: ${S?Ft.format(S.reset_credits_available):"\u2014"}</span><span>Streak: ${S?.current_streak_days==null?"\u2014":Ft.format(S.current_streak_days)+" dn\xED"}</span><span>Max streak: ${S?.longest_streak_days==null?"\u2014":Ft.format(S.longest_streak_days)+" dn\xED"}</span></div><p class="obs-note">USD odhad se zobraz\xED jen pokud jej billing route skute\u010Dn\u011B poskytne. Subscription allowance se nep\u0159epo\u010D\xEDt\xE1v\xE1 na API cen\xEDk.</p></article>`].join("")}function We(){let M=w(),R=e("#queue-summary"),S=e("#queue-list");if(!M.some(le=>le.status==="available")){R.innerHTML="",S.innerHTML='<p class="queue-empty">Stav durable fronty nen\xED v aktu\xE1ln\xEDm snapshotu dostupn\xFD.</p>';return}let W=T(),de=Object.fromEntries(Object.keys(hn).map(le=>[le,W.filter(he=>he.status===le).length]));R.innerHTML=Object.entries(hn).map(([le,he])=>`<div class="queue-stat" data-status="${ye(le)}"><span>${ye(he)}</span><b>${Pt(de[le])}</b></div>`).join("");let oe=W.slice(0,12);S.innerHTML=oe.length?oe.map(le=>{let he=le.blocker||"\u2014",ke=le.status==="pending"?`od ${hi(le.not_before)}`:`zm\u011Bna ${hi(le.updated_at)}`,Ne=le.issue_title||le.kind;return`<article class="queue-task" data-status="${ye(le.status)}"><div class="queue-task-main"><b>${ye(jt(le))} \xB7 <code>${ye(le.task_id)}</code></b><small>${ye(Ne)} \xB7 ${ye(le.kind)} \xB7 ${ye(le.agent)}</small></div><span class="queue-status">${ye(hn[le.status]||le.status)}</span><span class="queue-attempt">Pokus ${ye(it(le))}</span><time>${ye(ke)}</time><span class="queue-blocker">${ye(he)}</span></article>`}).join(""):'<p class="queue-empty">Fronta je pr\xE1zdn\xE1.</p>',W.length>oe.length&&S.insertAdjacentHTML("beforeend",`<p class="queue-empty">+${W.length-oe.length} dal\u0161\xEDch z\xE1znam\u016F v sanitizovan\xE9m snapshotu.</p>`)}function Ve(){let M=e("#search-grid");M.innerHTML=vn.map(R=>{let S=_t(R);if(S.search?.status!=="available")return`<article class="search-card is-unavailable"><header><div><span>${ye(R.toUpperCase())}</span><b>Search telemetry</b></div><span class="search-health">Nedostupn\xE9</span></header><p>Zdroj Search Routeru nen\xED v aktu\xE1ln\xEDm snapshotu dostupn\xFD.</p></article>`;let W=S.searches===0?"\u2014":S.successful==null||S.searches==null?"Nedostupn\xE9":`${Math.round(S.successful/S.searches*100)} %`,de=S.currentProvider||"Zat\xEDm bez provozu",oe=S.historicalProviders.join(", ")||"\u2014",le=S.fallbackProviders.join(", ")||"\u2014";return`<article class="search-card"><header><div><span>${ye(R.toUpperCase())}</span><b>Search Router</b></div><span class="search-health">${Pt(S.searches)} hled\xE1n\xED</span></header><div class="search-metrics"><div><span>\xDAsp\u011B\u0161nost</span><b>${ye(W)}</b></div><div><span>Latence avg / max</span><b>${ye(`${ji(S.avgLatency)} / ${ji(S.maxLatency)}`)}</b></div><div><span>Fallbacky</span><b>${Pt(S.fallbacks)}</b></div><div><span>N\xE1klady</span><b>${ye(Ii(S.cost))}</b></div></div><div class="search-routes"><span>FAST <b>${Pt(S.routes.fast)}</b></span><span>DEEP <b>${Pt(S.routes.deep)}</b></span><span>BROWSER <b>${Pt(S.routes.browser)}</b></span></div><p><span>Aktu\xE1ln\xED provider (posledn\xED b\u011Bh):</span> ${ye(de)}</p><p><span>Historick\xE9 providery:</span> ${ye(oe)}</p><p><span>Pozorovan\xE9 fallback providery:</span> ${ye(le)}</p><p><span>V\xFDsledky / extrakce:</span> ${Pt(S.results)} / ${Pt(S.extracts)} \xB7 data p\u0159ed ${ye(ui(S.search.data_at))}</p></article>`}).join("")}function Ct(){e("#project-grid").innerHTML=vn.map(oe=>{let le=at().filter(j=>j.profile===oe),he=Lt(oe),ke=he.inputCoverage==null||he.outputCoverage==null?null:Math.min(he.inputCoverage,he.outputCoverage),Ne=he.inputKnown==null?"Nedostupn\xE9":`${Pt(he.inputKnown)} / ${Pt(he.outputKnown)}${ke<100?` \xB7 ${ke} % req`:""}`,qe=he.costKnown==null?"Nedostupn\xE9":`${Ii(he.costKnown)} zn\xE1m\xE9${he.costUnknownRequests?` + ${Ft.format(he.costUnknownRequests)} bez ceny`:""}`;return`<article class="work-project"><h2>${oe.toUpperCase()}</h2>${le.length?le.map(j=>`<button class="work-agent" data-agent="${ye(j.agent)}"><b>${ye(j.agent)}</b><span>${Uc(j.status)}</span><small>${Hh[Kr(j.agent)]}</small></button>`).join(""):"<p>\u017Div\xFD stav agent\u016F nen\xED dostupn\xFD.</p>"}<p class="work-models">Modely profilu: ${ye(he.models.join(", ")||"Nedostupn\xE9")}</p><p class="work-models">Aktu\xE1ln\xED provider (posledn\xED b\u011Bh): ${ye(he.currentProvider||"Nedostupn\xE9")}</p><p class="work-models">Historick\xE9 providery: ${ye(he.historicalProviders.join(", ")||"\u2014")}</p><div class="work-totals"><div><span>Po\u017Eadavky</span><b>${Pt(he.requests)}</b></div><div><span>Tokeny vstup/v\xFDstup</span><b>${ye(Ne)}</b></div><div><span>Zn\xE1m\xE9 n\xE1klady / fallbacky</span><b>${ye(qe)} \xB7 ${Pt(he.fallbacks)}</b></div></div></article>`}).join(""),e("#project-grid").querySelectorAll("[data-agent]").forEach(oe=>oe.addEventListener("click",()=>sn(oe.dataset.agent))),fe(),We(),Ve(),e("#source-grid").innerHTML=(n?.sources||[]).map(oe=>{let le=oe.kind==="codex"?"CODEX / \xDA\u010CET":`${oe.profile} / ${oe.kind}`;return`<article class="source-card" data-status="${ye(oe.status)}"><b>${ye(le)}</b><span>${ye(oe.status)} \xB7 ${ye(oe.reason)}</span><span>${oe.status==="available"?`${oe.rows.length} z\xE1znam\u016F`:"bez dat"}</span></article>`}).join("");let M=new Set(["user_action_required","auth_required","credentials_missing","permission_required"]),R=(n?.sources||[]).filter(oe=>oe.status==="unavailable"&&M.has(oe.reason)),S=at().filter(oe=>oe.status==="blocked"),W=xe(),de=e("#attention-summary");if(de.hidden=!!n&&!R.length&&!S.length&&!W.length,de.textContent=n?`Vy\u017Eaduje v\xE1\u0161 z\xE1sah: ${[...S.map(oe=>oe.agent),...W.map(oe=>`${jt(oe)} ${oe.task_id}`),...R.map(oe=>`${oe.profile}/${oe.kind} (${oe.reason})`)].join(", ")}`:p,!de.hidden){let oe=document.createElement("button");oe.type="button",oe.className="attention-action",oe.textContent=S.length?"Otev\u0159\xEDt blokovan\xE9ho agenta":W.length?"Otev\u0159\xEDt frontu":"Obnovit data",oe.addEventListener("click",()=>S.length?sn(S[0].agent):W.length?e("#queue-title").scrollIntoView({behavior:h?"auto":"smooth"}):dn(!0)),de.append(" ",oe)}}function Mt(){let M=ee(l),R=M?.kind==="herdr_swarm",S=M?.raw_state||(M?hn[M.status]||M.status:null),W=M?R?[M.parent_task_id?`parent ${M.parent_task_id}`:"root task",M.dependencies?.length?`depends on ${M.dependencies.join(", ")}`:"no dependencies"].join(" \xB7 "):"Nedostupn\xE9 v telemetry kontraktu \xB7 \u017E\xE1dn\xE1 hrana nebyla odvozena":null,de=M?R?`${M.model||"model nehl\xE1\u0161en"} \xB7 fallback ${M.fallback_model||"\u2014"}`:"Nedostupn\xE9 v telemetry kontraktu":null,oe=M?R?`result ${M.result_sha||"\u2014"} \xB7 branch/base nejsou v kontraktu`:"Nedostupn\xE9 v telemetry kontraktu":null;e("#detail-profile").textContent="SWARM TASK",e("#detail-title").textContent=M?`${jt(M)} \xB7 ${M.task_id}`:l||"Task",e("#detail-role").textContent="Durable task node \xB7 read only",e("#detail-status").textContent=M?`Stav: ${S}`:"Task u\u017E nen\xED v aktu\xE1ln\xEDm snapshotu",e("#detail-links").innerHTML=M?[rt(ot(M),`Otev\u0159\xEDt Issue ${jt(M)}`),rt(gt(M),M.pr_number?`Otev\u0159\xEDt PR #${M.pr_number}`:"")].filter(Boolean).join(""):"";let le=M?[["Task ID",M.task_id],["Issue / n\xE1zev",`${jt(M)} \xB7 ${M.issue_title||M.kind}`],["Stav / scheduler",`${S} \xB7 ${R?"authoritative swarm":M.scheduler_state||"nehl\xE1\u0161eno"}`],["Pokus / maximum",it(M)],["Agent",M.agent||"\u2014"],["Typ",M.kind],["PR",M.pr_number?`#${M.pr_number}`:"Nen\xED hl\xE1\u0161eno"],["Blocker",M.blocker||"\u2014"],["\u010Cas",M.status==="pending"?`nejd\u0159\xEDve ${hi(M.not_before)}`:`zm\u011Bna ${hi(M.updated_at)}`],["Dependency edges",W],["Model / fallback",de],["Fencing token",R?Pt(M.fencing_token):"Nedostupn\xE9 v telemetry kontraktu"],["Runtime / queue wait","Nedostupn\xE9 v telemetry kontraktu"],["Branch / base / result SHA",oe],["Test / reviewer","Nedostupn\xE9 v telemetry kontraktu"]]:[["Stav","Task u\u017E nen\xED v aktu\xE1ln\xEDm snapshotu"]];e("#detail-metrics").innerHTML=le.map(([ke,Ne])=>`<div><dt>${ye(ke)}</dt><dd>${ye(Ne)}</dd></div>`).join("");let he=M?[`Durable queue: ${jt(M)} \xB7 ${M.task_id} \xB7 ${S}`,`Scheduler: ${R?"authoritative swarm":M.scheduler_state||"nehl\xE1\u0161eno"} \xB7 pokus ${it(M)}`,M.blocker?`Blocker: ${M.blocker}`:"Bez hl\xE1\u0161en\xE9ho blockeru",R?`Autoritativn\xED DAG: ${W}.`:"Dependency telemetry nen\xED sou\u010D\xE1st\xED aktu\xE1ln\xEDho snapshotu; DAG hrany nejsou odhadov\xE1ny.","Prompt, intern\xED my\u0161lenky a raw log nejsou v dashboardu zobrazov\xE1ny."]:["Task nen\xED v aktu\xE1ln\xEDm snapshotu."];e("#detail-events").innerHTML=he.map(ke=>`<li>${ye(ke)}</li>`).join("")}function nn(){if(l){Mt();return}if(!o)return;let M=at().find(q=>q.agent===o),R=M?.profile||(o.startsWith("majak-")?"majak":"quantlab"),S=Lt(R),W=_t(R),de=y(R,"herdr"),oe=o.endsWith("-hermes"),le=x(o),he=oe?Re(le)||Je(le):null,ke=oe?he?`${jt(he)} \xB7 ${he.task_id} \xB7 ${hn[he.status]||he.status}`:"\u017D\xE1dn\xE1 \xFAloha v durable queue":"Nedostupn\xE9 v datov\xE9m kontraktu",Ne=he?.issue_title||"Nedostupn\xE9 v telemetry kontraktu",qe=he?`${hn[he.status]||he.status} \xB7 scheduler ${he.scheduler_state||"nehl\xE1\u0161eno"}`:"Nedostupn\xE9 v telemetry kontraktu",j=he?`${he.status==="pending"?"nejd\u0159\xEDve "+hi(he.not_before):"zm\u011Bna "+hi(he.updated_at)}`:"Nedostupn\xE9 v telemetry kontraktu",et=S.inputCoverage==null||S.outputCoverage==null?null:Math.min(S.inputCoverage,S.outputCoverage),v=S.inputKnown==null?"Nedostupn\xE9":`${Pt(S.inputKnown)} / ${Pt(S.outputKnown)}${et<100?` \xB7 coverage ${et} % req`:""}`,L=S.costKnown==null?"Nedostupn\xE9":`${Ii(S.costKnown)} zn\xE1m\xE9${S.costUnknownRequests?` + ${Ft.format(S.costUnknownRequests)} req bez ceny`:""}`;e("#detail-profile").textContent=R.toUpperCase(),e("#detail-title").textContent=o,e("#detail-role").textContent=Hh[Kr(o)],e("#detail-status").textContent=`\u017Div\xFD stav: ${M?Uc(M.status):"Odpojeno / nezn\xE1m\xE9"}`,e("#detail-links").innerHTML=[rt(ot(he),he?`Otev\u0159\xEDt Issue ${jt(he)}`:""),rt(gt(he),he?.pr_number?`Otev\u0159\xEDt PR #${he.pr_number}`:"")].filter(Boolean).join("");let B=[["Aktu\xE1ln\xED \xFAkol",ke],["Issue / n\xE1zev",he?`${jt(he)} \xB7 ${Ne}`:"Nedostupn\xE9 v telemetry kontraktu"],["Task stav",qe],["Pokus / maximum",it(he)],["\u010Cas fronty",j],["PR",he?.pr_number?`#${he.pr_number}`:"Nen\xED hl\xE1\u0161eno"],["Blocker",he?.blocker||"\u2014"],["Modely profilu",S.models.join(", ")||"Nedostupn\xE9 v aktu\xE1ln\xEDm snapshotu"],["Aktu\xE1ln\xED model provider / fallbacky",`${S.currentProvider||"Nedostupn\xE9"} \xB7 ${Pt(S.fallbacks)}`],["Historick\xE9 model providery",S.historicalProviders.join(", ")||"\u2014"],["Tokeny vstup / v\xFDstup",v],["Zn\xE1m\xE9 n\xE1klady profilu",L],["Aktu\xE1ln\xED search provider / fallbacky",`${W.currentProvider||"Nedostupn\xE9"} \xB7 ${Pt(W.fallbacks)}`],["Historick\xE9 search providery",W.historicalProviders.join(", ")||"\u2014"],["Search / avg latence",`${Pt(W.searches)} \xB7 ${ji(W.avgLatency)}`],["Runtime / queue wait","Nedostupn\xE9 v telemetry kontraktu"],["Branch / base / result SHA","Nedostupn\xE9 v telemetry kontraktu"],["Test / reviewer","Nedostupn\xE9 v telemetry kontraktu"]];e("#detail-metrics").innerHTML=B.map(([q,Te])=>`<div><dt>${ye(q)}</dt><dd>${ye(Te)}</dd></div>`).join("");let H=[];M&&H.push(`Herdr hl\xE1s\xED stav \u201E${M.status}\u201C \xB7 pozorov\xE1no p\u0159ed ${ui(de?.observed_at)}`),he&&H.push(`Durable queue: ${jt(he)} \xB7 ${he.task_id} \xB7 ${hn[he.status]||he.status} \xB7 pokus ${it(he)} \xB7 scheduler ${he.scheduler_state||"nehl\xE1\u0161eno"}`),he?.blocker&&H.push(`Blocker: ${he.blocker}`),S.router?.status==="available"&&H.push(`Router profilu: ${Pt(S.requests)} po\u017Eadavk\u016F \xB7 data p\u0159ed ${ui(S.router.data_at)}`),W.search?.status==="available"&&H.push(`Search Router: ${Pt(W.searches)} hled\xE1n\xED \xB7 ${ji(W.avgLatency)} pr\u016Fm\u011Br \xB7 ${Pt(W.fallbacks)} fallback\u016F \xB7 data p\u0159ed ${ui(W.search.data_at)}`),H.push("Runtime, branch/SHA, test a reviewer data se nezobrazuj\xED, dokud je autoritativn\xED telemetry kontrakt neposkytuje."),H.push("Zdroj neposkytuje prompt, historii n\xE1stroj\u016F, intern\xED my\u0161lenky ani surov\xE9 provozn\xED z\xE1znamy \xFAlohy."),s&&H.unshift("DEMO: pohyb 3D sc\xE9ny je syntetick\xFD. Tento detail st\xE1le zobrazuje skute\u010Dn\xFD snapshot."),e("#detail-events").innerHTML=H.map(q=>`<li>${ye(q)}</li>`).join("")}function sn(M){vn.flatMap(Dt).some(R=>R.agent===M)&&(b=document.activeElement,l=null,o=M,nn(),t.detail.hidden=!1,t.backdrop.hidden=!1,document.body.style.overflow="hidden",e("#detail-close").focus(),C("focusTask",null),C("focusAgent",M),s&&ve(),N(),Me())}function Hs(M){ee(M)&&(b=document.activeElement,o=null,l=M,Mt(),t.detail.hidden=!1,t.backdrop.hidden=!1,document.body.style.overflow="hidden",e("#detail-close").focus(),C("focusAgent",null),C("focusTask",M),N(),Me())}function Gs(){t.detail.hidden=!0,t.backdrop.hidden=!0,document.body.style.overflow="",C("focusAgent",null),C("focusTask",l||null),b?.isConnected?b.focus():l?document.querySelector(`[data-task-id="${CSS.escape(l)}"]`)?.focus():document.querySelector(`[data-agent="${CSS.escape(o||"")}"]`)?.focus()}function di(M){a=M,t.film.hidden=M!=="film",t.work.hidden=M!=="work",document.querySelectorAll("[data-view]").forEach(R=>{let S=R.dataset.view===M;R.classList.toggle("is-active",S),R.setAttribute("aria-pressed",String(S))}),C("setActive",M==="film"&&!document.hidden),u&&(t.fallback.hidden=!1)}function Li(){document.documentElement.dataset.motion=h?"reduced":"full";let M=e("#motion-toggle");M.setAttribute("aria-pressed",String(h)),M.textContent=h?"Povolit pohyb":"Omezit pohyb",C("setReduced",h),Me()}function Ws(){let M=Ze(),R=M?` \xB7 ${M.tag} @ ${M.commit.slice(0,12)}`:"";t.header.textContent=s?"DEMO \xB7 sc\xE9na syntetick\xE1, metriky skute\u010Dn\xE9":n?`\u017Div\xE1 data \xB7 ${ui(n.generated_at)}${R}`:p;let S=s?"#e49a34":n?"#6adf9a":"#ff7159";t.liveDot.style.background=S,t.liveDot.style.color=S}function Ji(){Ws(),ve(),we(),ie(),Ct(),Me(),t.detail.hidden||nn()}function Qr(M){if(!M||!Number.isFinite(M.generated_at)||!Array.isArray(M.sources))throw new Error("invalid");if(Date.now()/1e3-M.generated_at>90||M.generated_at>Date.now()/1e3+5)throw new Error("stale");for(let R of M.sources){if(!R||!vn.includes(R.profile)||typeof R.kind!="string"||!Array.isArray(R.rows))throw new Error("invalid");if(R.kind==="herdr"&&R.rows.some(S=>typeof S.agent!="string"||typeof S.status!="string"))throw new Error("invalid");if(["router","search"].includes(R.kind)&&R.rows.some(S=>typeof S.provider!="string"||!Number.isFinite(S.last_used_at)))throw new Error("invalid");if(R.kind==="queue"){let S=R.profile==="majak"?{repo:"Bbambaaamm/dotacni-majak",agent:"dotacni-majak-hermes"}:{repo:"Bbambaaamm/Autonomous-Quant-Lab",agent:"quantlab-hermes"};if(R.rows.some(W=>typeof W.task_id!="string"||W.repo!=null&&typeof W.repo!="string"||R.profile==="majak"&&W.repo!==S.repo||R.profile==="quantlab"&&W.repo!=null&&W.repo!==S.repo||W.issue!=null&&(!Number.isSafeInteger(W.issue)||W.issue<0)||W.issue_title!=null&&(typeof W.issue_title!="string"||W.issue_title.length>160)||typeof W.issue_open!="boolean"||W.scheduler_state!=null&&typeof W.scheduler_state!="string"||W.agent!==S.agent||typeof W.kind!="string"||!Object.hasOwn(hn,W.status)||!Number.isSafeInteger(W.attempts)||W.attempts<0||!Number.isSafeInteger(W.max_attempts)||W.max_attempts<0||W.not_before!=null&&!Number.isFinite(W.not_before)||!Number.isFinite(W.updated_at)||W.blocker!=null&&typeof W.blocker!="string"||W.pr_number!=null&&(!Number.isSafeInteger(W.pr_number)||W.pr_number<1)))throw new Error("invalid")}if(R.kind==="admission"){if(R.profile!=="quantlab")throw new Error("invalid");if(R.rows.some(S=>!["allow","deny"].includes(S.event)||S.reason!=null&&typeof S.reason!="string"||typeof S.role!="string"||typeof S.repo!="string"||typeof S.issue!="string"||!Number.isSafeInteger(S.node_count)||S.node_count<0||!Number.isSafeInteger(S.max_depth)||S.max_depth<0||!Number.isSafeInteger(S.max_fanout)||S.max_fanout<0||!Number.isSafeInteger(S.child_tools_count)||S.child_tools_count<0||S.agents_after!=null&&(!Number.isSafeInteger(S.agents_after)||S.agents_after<0)||!Number.isFinite(S.observed_at)||S.event==="deny"&&(S.reason==null||S.agents_after!=null)||S.event==="allow"&&(S.reason!=null||S.agents_after==null)))throw new Error("invalid")}if(R.kind==="swarm"){if(R.profile!=="quantlab"||R.status==="available"&&R.rows.length!==1)throw new Error("invalid");for(let S of R.rows){let W=S.runtime_status??"unavailable",de=S.runtime_agents??[];if(S.version!==1||typeof S.repo!="string"||typeof S.issue!="string"||S.issue_state!=null&&!["open","closed","unknown"].includes(S.issue_state)||typeof S.paper_only!="boolean"||!Array.isArray(S.policy_profiles)||!Array.isArray(S.agents)||!Array.isArray(S.tasks)||!Array.isArray(S.edges)||!["available","unavailable","not_applicable"].includes(W)||!Array.isArray(de)||W!=="available"&&de.length||S.repo==="Bbambaaamm/Autonomous-Quant-Lab"&&S.paper_only!==!0)throw new Error("invalid");let oe=new Set;for(let j of S.tasks){if(!j||typeof j.task_id!="string"||oe.has(j.task_id)||!Object.hasOwn(Wh,j.state)||typeof j.role!="string"||!Number.isSafeInteger(j.attempt)||j.attempt<0||!Number.isSafeInteger(j.max_attempts)||j.max_attempts<j.attempt||j.attempt_state!=null&&!["dispatching","accepted","working","delivery_uncertain","verifying","completed","done","blocked","failed","retry_scheduled"].includes(j.attempt_state)||j.delivery_reconcile_count!=null&&(!Number.isSafeInteger(j.delivery_reconcile_count)||j.delivery_reconcile_count<0)||!Number.isSafeInteger(j.fencing_token)||j.fencing_token<0||!Array.isArray(j.dependencies)||j.dependencies.some(et=>typeof et!="string")||j.parent_task_id!=null&&typeof j.parent_task_id!="string"||j.parent_agent_id!=null&&typeof j.parent_agent_id!="string"||j.agent_id!=null&&typeof j.agent_id!="string"||j.result_sha!=null&&(typeof j.result_sha!="string"||!/^[0-9a-f]{64}$/.test(j.result_sha)))throw new Error("invalid");oe.add(j.task_id)}let le=new Map(S.tasks.map(j=>[j.task_id,j])),he=new Set;for(let j of de){if(!j||typeof j.agent_id!="string"||he.has(j.agent_id)||!["idle","working","blocked","done","unknown"].includes(j.status)||j.task_id!=null&&!le.has(j.task_id))throw new Error("invalid");he.add(j.agent_id)}let ke=new Set,Ne=new Set;for(let j of S.agents){if(!j||typeof j.agent_id!="string"||ke.has(j.agent_id)||typeof j.task_id!="string"||Ne.has(j.task_id)||j.state!=="running"||j.parent_task_id!=null&&typeof j.parent_task_id!="string"||j.parent_agent_id!=null&&typeof j.parent_agent_id!="string"||!Number.isSafeInteger(j.fencing_token)||j.fencing_token<0)throw new Error("invalid");let et=le.get(j.task_id);if(!et||et.state!=="running"||et.agent_id!==j.agent_id||et.parent_task_id!==j.parent_task_id||et.parent_agent_id!==j.parent_agent_id||et.fencing_token!==j.fencing_token)throw new Error("invalid");ke.add(j.agent_id),Ne.add(j.task_id)}let qe=new Set(S.tasks.filter(j=>j.state==="running"&&j.agent_id!=null).map(j=>j.task_id));if(qe.size!==Ne.size||[...qe].some(j=>!Ne.has(j)))throw new Error("invalid");for(let j of S.edges)if(!j||!["parent","dependency"].includes(j.kind)||typeof j.from_task!="string"||typeof j.to_task!="string"||!oe.has(j.from_task)||!oe.has(j.to_task))throw new Error("invalid")}}if(R.kind==="release"){if(R.profile!=="quantlab"||R.status==="available"&&R.rows.length!==1)throw new Error("invalid");if(R.rows.some(S=>typeof S.tag!="string"||!/^v[A-Za-z0-9._-]{1,62}$/.test(S.tag)||typeof S.commit!="string"||!/^[0-9a-f]{40}$/.test(S.commit)||typeof S.config_sha256!="string"||!/^[0-9a-f]{64}$/.test(S.config_sha256)||!Number.isSafeInteger(S.deployed_at)||S.deployed_at<0))throw new Error("invalid")}if(R.kind==="codex"){if(R.profile!=="majak"||R.status==="available"&&R.rows.length!==1)throw new Error("invalid");if(R.rows.some(S=>!Number.isFinite(S.used_percent)||S.used_percent<0||S.used_percent>100||!Array.isArray(S.daily)||!Array.isArray(S.limit_history)||!["available","unavailable"].includes(S.routing_status)))throw new Error("invalid");for(let S of R.rows){if(S.routing_status!=="available")continue;let W=["routing_observed_at","routing_soft_limit_pct","routing_hard_limit_pct","routing_decisions","routing_free","routing_sol","routing_astra","routing_astra_escalations","routing_premium_denied"];if(typeof S.routing_policy_version!="string"||S.routing_policy_version.length>64||W.some(de=>!Number.isSafeInteger(S[de])||S[de]<0)||S.routing_soft_limit_pct>=S.routing_hard_limit_pct||S.routing_hard_limit_pct>100||S.routing_free+S.routing_sol+S.routing_astra>S.routing_decisions||S.routing_astra_escalations>S.routing_astra||S.last_route_at!=null&&!Number.isFinite(S.last_route_at)||S.last_route_tier!=null&&!["free","sol","astra"].includes(S.last_route_tier)||S.last_route_model!=null&&typeof S.last_route_model!="string"||S.last_route_reason!=null&&typeof S.last_route_reason!="string")throw new Error("invalid")}}}return M}async function dn(M=!1){if(m||!M&&document.hidden)return;m=!0;let R=new AbortController,S=setTimeout(()=>R.abort(),1e4);try{let W=await fetch("/agent-platform/api/v1/overview",{cache:"no-store",headers:{Accept:"application/json"},signal:R.signal});if(!W.ok)throw new Error(`HTTP ${W.status}`);n=Qr(await W.json()),p="\u010Cerstv\xFD \u017Eiv\xFD stav nen\xED dostupn\xFD",e("#server-fallback-details").removeAttribute("open")}catch(W){n=null,p=W.message==="stale"?"Snapshot je star\u0161\xED ne\u017E 90 s \xB7 obnovte data":"\u017Div\xE1 data nejsou dostupn\xE1 \xB7 ov\u011B\u0159te p\u0159ipojen\xED nebo p\u0159ihl\xE1\u0161en\xED"}finally{clearTimeout(S),m=!1,Ji()}}for(let[M,R]of Object.entries(Vs)){let S=document.createElement("button");S.type="button",S.dataset.demoState=M,S.textContent=R.label,S.addEventListener("click",()=>{r=M,t.demoStates.querySelectorAll("button").forEach(W=>{let de=W.dataset.demoState===M;W.classList.toggle("is-active",de),W.setAttribute("aria-pressed",String(de))}),ve(),Me()}),t.demoStates.append(S)}return document.querySelectorAll("[data-view]").forEach(M=>M.addEventListener("click",()=>di(M.dataset.view))),document.querySelectorAll("[data-task-filter]").forEach(M=>M.addEventListener("click",()=>{c=M.dataset.taskFilter||"all",N()})),e("#demo-toggle").addEventListener("click",M=>{s=!s,document.documentElement.dataset.mode=s?"demo":"live",M.currentTarget.setAttribute("aria-pressed",String(s)),M.currentTarget.textContent=s?"Ukon\u010Dit demo":"Demo re\u017Eim",t.demo.hidden=!s,s&&(r="idle",t.demoStates.querySelectorAll("button").forEach(R=>{let S=R.dataset.demoState==="idle";R.classList.toggle("is-active",S),R.setAttribute("aria-pressed",String(S))})),Ws(),ve(),Me(),t.detail.hidden||nn(),s||dn(!0)}),e("#demo-panel > div:first-child > span").textContent="Pouze animace jsou syntetick\xE9. Metriky a detaily z\u016Fst\xE1vaj\xED skute\u010Dn\xE9.",e("#motion-toggle").addEventListener("click",()=>{h=!h,Li()}),matchMedia("(prefers-reduced-motion: reduce)").addEventListener("change",M=>{h=M.matches,Li()}),e("#detail-close").addEventListener("click",Gs),t.backdrop.addEventListener("click",Gs),t.detail.setAttribute("role","dialog"),t.detail.setAttribute("aria-modal","true"),document.addEventListener("keydown",M=>{if(!t.detail.hidden&&(M.key==="Escape"&&Gs(),M.key==="Tab")){let R=[...t.detail.querySelectorAll('button:not([disabled]),a[href],[tabindex="0"]')],S=R[0],W=R[R.length-1];M.shiftKey&&document.activeElement===S?(M.preventDefault(),W?.focus()):!M.shiftKey&&document.activeElement===W&&(M.preventDefault(),S?.focus())}}),t.attention.addEventListener("click",()=>{if(!n){dn(!0);return}let M=at().find(R=>R.status==="blocked");M?sn(M.agent):di("work")}),document.querySelectorAll("[data-project-toggle]").forEach(M=>M.addEventListener("click",()=>{let R=M.closest(".project").querySelector(".agent-list"),S=M.getAttribute("aria-expanded")==="true";M.setAttribute("aria-expanded",String(!S)),R.hidden=S,ve()})),document.addEventListener("visibilitychange",()=>{C("setActive",!document.hidden&&a==="film"),document.hidden||dn(!0)}),C("onSelect",sn),C("onTaskSelect",Hs),Li(),di(u?"work":"film"),Ji(),dn(!0),setInterval(dn,3e4),setInterval(()=>{document.hidden||(n&&Date.now()/1e3-n.generated_at>90?(n=null,p="Snapshot je star\u0161\xED ne\u017E 90 s \xB7 obnovte data",Ji()):(we(),Ws(),t.detail.hidden||nn()))},1e3),Object.freeze({diagnostics:()=>({view:a,mode:s?"demo":"live",state:Se(),reduced:h,selectedAgent:o,selectedTask:l,sceneAvailable:!!f&&!u,freshSnapshot:!!n,agentCount:at().length,queueActive:Xe().length})})}$h(zh);document.documentElement.dataset.preview==="true"&&document.querySelector("#demo-toggle").click();})();
/*! Bundled license information:

three/build/three.core.js:
three/build/three.module.js:
  (**
   * @license
   * Copyright 2010-2026 Three.js Authors
   * SPDX-License-Identifier: MIT
   *)
*/
