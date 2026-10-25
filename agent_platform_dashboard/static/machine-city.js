(()=>{var ta=new Uint32Array(256),yl=ta.length;function rt(){let i=globalThis.crypto;if(!i||typeof i.getRandomValues!="function")throw new Error("secure_random_unavailable");return yl>=ta.length&&(i.getRandomValues(ta),yl=0),ta[yl++]/4294967296}var Su=0,nc=1,Tu=2;var Ar=1,Eu=2,As=3,yi=0,Zt=1,Wn=2,Mn=0,Cs=1,Bi=2,ic=3,sc=4,wu=5;var zi=100,Au=101,Cu=102,Ru=103,Iu=104,Pu=200,Lu=201,Nu=202,Du=203,rc=204,ac=205,Uu=206,Fu=207,ku=208,Ou=209,Bu=210,zu=211,Vu=212,Hu=213,Gu=214,Ca=0,Ra=1,Ia=2,fs=3,Pa=4,La=5,Na=6,Da=7,ho=0,Wu=1,$u=2,Dn=0,Cr=1,Rr=2,Ir=3,Vi=4,Pr=5,Lr=6,Nr=7;var oc=300,bi=301,Hi=302,fo=303,po=304,Dr=306,Ua=1e3,On=1001,Fa=1002,Gt=1003,qu=1004;var Ur=1005;var Yt=1006,mo=1007;var Mi=1008;var un=1009,lc=1010,cc=1011,Rs=1012,go=1013,Un=1014,Sn=1015,jt=1016,_o=1017,xo=1018,Is=1020,uc=35902,hc=35899,dc=1021,fc=1022,Tn=1023,Bn=1026,Si=1027,vo=1028,yo=1029,Ti=1030,bo=1031;var Mo=1033,Fr=33776,kr=33777,Or=33778,Br=33779,So=35840,To=35841,Eo=35842,wo=35843,Ao=36196,Co=37492,Ro=37496,Io=37488,Po=37489,zr=37490,Lo=37491,No=37808,Do=37809,Uo=37810,Fo=37811,ko=37812,Oo=37813,Bo=37814,zo=37815,Vo=37816,Ho=37817,Go=37818,Wo=37819,$o=37820,qo=37821,Xo=36492,Yo=36494,Zo=36495,jo=36283,Jo=36284,Vr=36285,Ko=36286;var er=2300,ka=2301,wa=2302,ql=2303,Xl=2400,Yl=2401,Zl=2402;var Xu=3200;var Hr=0,Yu=1,ti="",nn="srgb",tr="srgb-linear",nr="linear",yt="srgb";var Aa=7680;var Zu=519,ju=512,Ju=513,Ku=514,Qo=515,Qu=516,eh=517,el=518,th=519,nh=35044,pc=35048;var mc="300 es",Pn=2e3,ps=2001;function nd(i){for(let e=i.length-1;e>=0;--e)if(i[e]>=65535)return!0;return!1}function id(i){return ArrayBuffer.isView(i)&&!(i instanceof DataView)}function ir(i){return document.createElementNS("http://www.w3.org/1999/xhtml",i)}function ih(){let i=ir("canvas");return i.style.display="block",i}var Wc={},ms=null;function gc(...i){let e="THREE."+i.shift();ms?ms("log",e,...i):console.log(e,...i)}function sh(i){let e=i[0];if(typeof e=="string"&&e.startsWith("TSL:")){let t=i[1];t&&t.isStackTrace?i[0]+=" "+t.getLocation():i[1]='Stack trace not available. Enable "THREE.Node.captureStackTrace" to capture stack traces.'}return i}function $e(...i){i=sh(i);let e="THREE."+i.shift();if(ms)ms("warn",e,...i);else{let t=i[0];t&&t.isStackTrace?console.warn(t.getError(e)):console.warn(e,...i)}}function Xe(...i){i=sh(i);let e="THREE."+i.shift();if(ms)ms("error",e,...i);else{let t=i[0];t&&t.isStackTrace?console.error(t.getError(e)):console.error(e,...i)}}function Ni(...i){let e=i.join(" ");e in Wc||(Wc[e]=!0,$e(...i))}function rh(i,e,t){return new Promise(function(n,s){function r(){switch(i.clientWaitSync(e,i.SYNC_FLUSH_COMMANDS_BIT,0)){case i.WAIT_FAILED:s();break;case i.TIMEOUT_EXPIRED:setTimeout(r,t);break;default:n()}}setTimeout(r,t)})}var ah={[Ca]:Ra,[Ia]:Na,[Pa]:Da,[fs]:La,[Ra]:Ca,[Na]:Ia,[Da]:Pa,[La]:fs},zn=class{addEventListener(e,t){this._listeners===void 0&&(this._listeners={});let n=this._listeners;n[e]===void 0&&(n[e]=[]),n[e].indexOf(t)===-1&&n[e].push(t)}hasEventListener(e,t){let n=this._listeners;return n===void 0?!1:n[e]!==void 0&&n[e].indexOf(t)!==-1}removeEventListener(e,t){let n=this._listeners;if(n===void 0)return;let s=n[e];if(s!==void 0){let r=s.indexOf(t);r!==-1&&s.splice(r,1)}}dispatchEvent(e){let t=this._listeners;if(t===void 0)return;let n=t[e.type];if(n!==void 0){e.target=this;let s=n.slice(0);for(let r=0,a=s.length;r<a;r++)s[r].call(this,e);e.target=null}}},Jt=["00","01","02","03","04","05","06","07","08","09","0a","0b","0c","0d","0e","0f","10","11","12","13","14","15","16","17","18","19","1a","1b","1c","1d","1e","1f","20","21","22","23","24","25","26","27","28","29","2a","2b","2c","2d","2e","2f","30","31","32","33","34","35","36","37","38","39","3a","3b","3c","3d","3e","3f","40","41","42","43","44","45","46","47","48","49","4a","4b","4c","4d","4e","4f","50","51","52","53","54","55","56","57","58","59","5a","5b","5c","5d","5e","5f","60","61","62","63","64","65","66","67","68","69","6a","6b","6c","6d","6e","6f","70","71","72","73","74","75","76","77","78","79","7a","7b","7c","7d","7e","7f","80","81","82","83","84","85","86","87","88","89","8a","8b","8c","8d","8e","8f","90","91","92","93","94","95","96","97","98","99","9a","9b","9c","9d","9e","9f","a0","a1","a2","a3","a4","a5","a6","a7","a8","a9","aa","ab","ac","ad","ae","af","b0","b1","b2","b3","b4","b5","b6","b7","b8","b9","ba","bb","bc","bd","be","bf","c0","c1","c2","c3","c4","c5","c6","c7","c8","c9","ca","cb","cc","cd","ce","cf","d0","d1","d2","d3","d4","d5","d6","d7","d8","d9","da","db","dc","dd","de","df","e0","e1","e2","e3","e4","e5","e6","e7","e8","e9","ea","eb","ec","ed","ee","ef","f0","f1","f2","f3","f4","f5","f6","f7","f8","f9","fa","fb","fc","fd","fe","ff"],$c=1234567,js=Math.PI/180,gs=180/Math.PI;function Ps(){let i=rt()*4294967295|0,e=rt()*4294967295|0,t=rt()*4294967295|0,n=rt()*4294967295|0;return(Jt[i&255]+Jt[i>>8&255]+Jt[i>>16&255]+Jt[i>>24&255]+"-"+Jt[e&255]+Jt[e>>8&255]+"-"+Jt[e>>16&15|64]+Jt[e>>24&255]+"-"+Jt[t&63|128]+Jt[t>>8&255]+"-"+Jt[t>>16&255]+Jt[t>>24&255]+Jt[n&255]+Jt[n>>8&255]+Jt[n>>16&255]+Jt[n>>24&255]).toLowerCase()}function ot(i,e,t){return Math.max(e,Math.min(t,i))}function _c(i,e){return(i%e+e)%e}function sd(i,e,t,n,s){return n+(i-e)*(s-n)/(t-e)}function rd(i,e,t){return i!==e?(t-i)/(e-i):0}function Js(i,e,t){return(1-t)*i+t*e}function ad(i,e,t,n){return Js(i,e,1-Math.exp(-t*n))}function od(i,e=1){return e-Math.abs(_c(i,e*2)-e)}function ld(i,e,t){return i<=e?0:i>=t?1:(i=(i-e)/(t-e),i*i*(3-2*i))}function cd(i,e,t){return i<=e?0:i>=t?1:(i=(i-e)/(t-e),i*i*i*(i*(i*6-15)+10))}function ud(i,e){return i+Math.floor(rt()*(e-i+1))}function hd(i,e){return i+rt()*(e-i)}function dd(i){return i*(.5-rt())}function fd(i){i!==void 0&&($c=i);let e=$c+=1831565813;return e=Math.imul(e^e>>>15,e|1),e^=e+Math.imul(e^e>>>7,e|61),((e^e>>>14)>>>0)/4294967296}function pd(i){return i*js}function md(i){return i*gs}function gd(i){return i>0&&Number.isInteger(i)&&2**Math.round(Math.log2(i))===i}function _d(i){return Math.pow(2,Math.ceil(Math.log(i)/Math.LN2))}function xd(i){return Math.pow(2,Math.floor(Math.log(i)/Math.LN2))}function vd(i,e,t,n,s){let r=Math.cos,a=Math.sin,o=r(t/2),l=a(t/2),c=r((e+n)/2),h=a((e+n)/2),f=r((e-n)/2),u=a((e-n)/2),d=r((n-e)/2),_=a((n-e)/2);switch(s){case"XYX":i.set(o*h,l*f,l*u,o*c);break;case"YZY":i.set(l*u,o*h,l*f,o*c);break;case"ZXZ":i.set(l*f,l*u,o*h,o*c);break;case"XZX":i.set(o*h,l*_,l*d,o*c);break;case"YXY":i.set(l*d,o*h,l*_,o*c);break;case"ZYZ":i.set(l*_,l*d,o*h,o*c);break;default:$e("MathUtils: .setQuaternionFromProperEuler() encountered an unknown order: "+s)}}function hs(i,e){switch(e.constructor){case Float32Array:return i;case Uint32Array:return i/4294967295;case Uint16Array:return i/65535;case Uint8Array:case Uint8ClampedArray:return i/255;case Int32Array:return Math.max(i/2147483647,-1);case Int16Array:return Math.max(i/32767,-1);case Int8Array:return Math.max(i/127,-1);default:throw new Error("THREE.MathUtils: Invalid component type.")}}function tn(i,e){switch(e.constructor){case Float32Array:return i;case Uint32Array:return Math.round(i*4294967295);case Uint16Array:return Math.round(i*65535);case Uint8Array:case Uint8ClampedArray:return Math.round(i*255);case Int32Array:return Math.round(i*2147483647);case Int16Array:return Math.round(i*32767);case Int8Array:return Math.round(i*127);default:throw new Error("THREE.MathUtils: Invalid component type.")}}var tl={DEG2RAD:js,RAD2DEG:gs,generateUUID:Ps,clamp:ot,euclideanModulo:_c,mapLinear:sd,inverseLerp:rd,lerp:Js,damp:ad,pingpong:od,smoothstep:ld,smootherstep:cd,randInt:ud,randFloat:hd,randFloatSpread:dd,seededRandom:fd,degToRad:pd,radToDeg:md,isPowerOfTwo:gd,ceilPowerOfTwo:_d,floorPowerOfTwo:xd,setQuaternionFromProperEuler:vd,normalize:tn,denormalize:hs},De=class i{static{i.prototype.isVector2=!0}constructor(e=0,t=0){this.x=e,this.y=t}get width(){return this.x}set width(e){this.x=e}get height(){return this.y}set height(e){this.y=e}set(e,t){return this.x=e,this.y=t,this}setScalar(e){return this.x=e,this.y=e,this}setX(e){return this.x=e,this}setY(e){return this.y=e,this}setComponent(e,t){switch(e){case 0:this.x=t;break;case 1:this.y=t;break;default:throw new Error("THREE.Vector2: index is out of range: "+e)}return this}getComponent(e){switch(e){case 0:return this.x;case 1:return this.y;default:throw new Error("THREE.Vector2: index is out of range: "+e)}}clone(){return new this.constructor(this.x,this.y)}copy(e){return this.x=e.x,this.y=e.y,this}add(e){return this.x+=e.x,this.y+=e.y,this}addScalar(e){return this.x+=e,this.y+=e,this}addVectors(e,t){return this.x=e.x+t.x,this.y=e.y+t.y,this}addScaledVector(e,t){return this.x+=e.x*t,this.y+=e.y*t,this}sub(e){return this.x-=e.x,this.y-=e.y,this}subScalar(e){return this.x-=e,this.y-=e,this}subVectors(e,t){return this.x=e.x-t.x,this.y=e.y-t.y,this}multiply(e){return this.x*=e.x,this.y*=e.y,this}multiplyScalar(e){return this.x*=e,this.y*=e,this}divide(e){return this.x/=e.x,this.y/=e.y,this}divideScalar(e){return this.multiplyScalar(1/e)}applyMatrix3(e){let t=this.x,n=this.y,s=e.elements;return this.x=s[0]*t+s[3]*n+s[6],this.y=s[1]*t+s[4]*n+s[7],this}min(e){return this.x=Math.min(this.x,e.x),this.y=Math.min(this.y,e.y),this}max(e){return this.x=Math.max(this.x,e.x),this.y=Math.max(this.y,e.y),this}clamp(e,t){return this.x=ot(this.x,e.x,t.x),this.y=ot(this.y,e.y,t.y),this}clampScalar(e,t){return this.x=ot(this.x,e,t),this.y=ot(this.y,e,t),this}clampLength(e,t){let n=this.length();return this.divideScalar(n||1).multiplyScalar(ot(n,e,t))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this}negate(){return this.x=-this.x,this.y=-this.y,this}dot(e){return this.x*e.x+this.y*e.y}cross(e){return this.x*e.y-this.y*e.x}lengthSq(){return this.x*this.x+this.y*this.y}length(){return Math.sqrt(this.x*this.x+this.y*this.y)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)}normalize(){return this.divideScalar(this.length()||1)}angle(){return Math.atan2(-this.y,-this.x)+Math.PI}angleTo(e){let t=Math.sqrt(this.lengthSq()*e.lengthSq());if(t===0)return Math.PI/2;let n=this.dot(e)/t;return Math.acos(ot(n,-1,1))}distanceTo(e){return Math.sqrt(this.distanceToSquared(e))}distanceToSquared(e){let t=this.x-e.x,n=this.y-e.y;return t*t+n*n}manhattanDistanceTo(e){return Math.abs(this.x-e.x)+Math.abs(this.y-e.y)}setLength(e){return this.normalize().multiplyScalar(e)}lerp(e,t){return this.x+=(e.x-this.x)*t,this.y+=(e.y-this.y)*t,this}lerpVectors(e,t,n){return this.x=e.x+(t.x-e.x)*n,this.y=e.y+(t.y-e.y)*n,this}equals(e){return e.x===this.x&&e.y===this.y}fromArray(e,t=0){return this.x=e[t],this.y=e[t+1],this}toArray(e=[],t=0){return e[t]=this.x,e[t+1]=this.y,e}fromBufferAttribute(e,t){return this.x=e.getX(t),this.y=e.getY(t),this}rotateAround(e,t){let n=Math.cos(t),s=Math.sin(t),r=this.x-e.x,a=this.y-e.y;return this.x=r*n-a*s+e.x,this.y=r*s+a*n+e.y,this}random(){return this.x=rt(),this.y=rt(),this}*[Symbol.iterator](){yield this.x,yield this.y}},Ot=class{constructor(e=0,t=0,n=0,s=1){this.isQuaternion=!0,this._x=e,this._y=t,this._z=n,this._w=s}static slerpFlat(e,t,n,s,r,a,o){let l=n[s+0],c=n[s+1],h=n[s+2],f=n[s+3],u=r[a+0],d=r[a+1],_=r[a+2],S=r[a+3];if(f!==S||l!==u||c!==d||h!==_){let g=l*u+c*d+h*_+f*S;g<0&&(u=-u,d=-d,_=-_,S=-S,g=-g);let p=1-o;if(g<.9995){let w=Math.acos(g),I=Math.sin(w);p=Math.sin(p*w)/I,o=Math.sin(o*w)/I,l=l*p+u*o,c=c*p+d*o,h=h*p+_*o,f=f*p+S*o}else{l=l*p+u*o,c=c*p+d*o,h=h*p+_*o,f=f*p+S*o;let w=1/Math.sqrt(l*l+c*c+h*h+f*f);l*=w,c*=w,h*=w,f*=w}}e[t]=l,e[t+1]=c,e[t+2]=h,e[t+3]=f}static multiplyQuaternionsFlat(e,t,n,s,r,a){let o=n[s],l=n[s+1],c=n[s+2],h=n[s+3],f=r[a],u=r[a+1],d=r[a+2],_=r[a+3];return e[t]=o*_+h*f+l*d-c*u,e[t+1]=l*_+h*u+c*f-o*d,e[t+2]=c*_+h*d+o*u-l*f,e[t+3]=h*_-o*f-l*u-c*d,e}get x(){return this._x}set x(e){this._x=e,this._onChangeCallback()}get y(){return this._y}set y(e){this._y=e,this._onChangeCallback()}get z(){return this._z}set z(e){this._z=e,this._onChangeCallback()}get w(){return this._w}set w(e){this._w=e,this._onChangeCallback()}set(e,t,n,s){return this._x=e,this._y=t,this._z=n,this._w=s,this._onChangeCallback(),this}clone(){return new this.constructor(this._x,this._y,this._z,this._w)}copy(e){return this._x=e.x,this._y=e.y,this._z=e.z,this._w=e.w,this._onChangeCallback(),this}setFromEuler(e,t=!0){let n=e._x,s=e._y,r=e._z,a=e._order,o=Math.cos,l=Math.sin,c=o(n/2),h=o(s/2),f=o(r/2),u=l(n/2),d=l(s/2),_=l(r/2);switch(a){case"XYZ":this._x=u*h*f+c*d*_,this._y=c*d*f-u*h*_,this._z=c*h*_+u*d*f,this._w=c*h*f-u*d*_;break;case"YXZ":this._x=u*h*f+c*d*_,this._y=c*d*f-u*h*_,this._z=c*h*_-u*d*f,this._w=c*h*f+u*d*_;break;case"ZXY":this._x=u*h*f-c*d*_,this._y=c*d*f+u*h*_,this._z=c*h*_+u*d*f,this._w=c*h*f-u*d*_;break;case"ZYX":this._x=u*h*f-c*d*_,this._y=c*d*f+u*h*_,this._z=c*h*_-u*d*f,this._w=c*h*f+u*d*_;break;case"YZX":this._x=u*h*f+c*d*_,this._y=c*d*f+u*h*_,this._z=c*h*_-u*d*f,this._w=c*h*f-u*d*_;break;case"XZY":this._x=u*h*f-c*d*_,this._y=c*d*f-u*h*_,this._z=c*h*_+u*d*f,this._w=c*h*f+u*d*_;break;default:$e("Quaternion: .setFromEuler() encountered an unknown order: "+a)}return t===!0&&this._onChangeCallback(),this}setFromAxisAngle(e,t){let n=t/2,s=Math.sin(n);return this._x=e.x*s,this._y=e.y*s,this._z=e.z*s,this._w=Math.cos(n),this._onChangeCallback(),this}setFromRotationMatrix(e){let t=e.elements,n=t[0],s=t[4],r=t[8],a=t[1],o=t[5],l=t[9],c=t[2],h=t[6],f=t[10],u=n+o+f;if(u>0){let d=.5/Math.sqrt(u+1);this._w=.25/d,this._x=(h-l)*d,this._y=(r-c)*d,this._z=(a-s)*d}else if(n>o&&n>f){let d=2*Math.sqrt(1+n-o-f);this._w=(h-l)/d,this._x=.25*d,this._y=(s+a)/d,this._z=(r+c)/d}else if(o>f){let d=2*Math.sqrt(1+o-n-f);this._w=(r-c)/d,this._x=(s+a)/d,this._y=.25*d,this._z=(l+h)/d}else{let d=2*Math.sqrt(1+f-n-o);this._w=(a-s)/d,this._x=(r+c)/d,this._y=(l+h)/d,this._z=.25*d}return this._onChangeCallback(),this}setFromUnitVectors(e,t){let n=e.dot(t)+1;return n<1e-8?(n=0,Math.abs(e.x)>Math.abs(e.z)?(this._x=-e.y,this._y=e.x,this._z=0,this._w=n):(this._x=0,this._y=-e.z,this._z=e.y,this._w=n)):(this._x=e.y*t.z-e.z*t.y,this._y=e.z*t.x-e.x*t.z,this._z=e.x*t.y-e.y*t.x,this._w=n),this.normalize()}angleTo(e){return 2*Math.acos(Math.abs(ot(this.dot(e),-1,1)))}rotateTowards(e,t){let n=this.angleTo(e);if(n===0)return this;let s=Math.min(1,t/n);return this.slerp(e,s),this}identity(){return this.set(0,0,0,1)}invert(){return this.conjugate()}conjugate(){return this._x*=-1,this._y*=-1,this._z*=-1,this._onChangeCallback(),this}dot(e){return this._x*e._x+this._y*e._y+this._z*e._z+this._w*e._w}lengthSq(){return this._x*this._x+this._y*this._y+this._z*this._z+this._w*this._w}length(){return Math.sqrt(this._x*this._x+this._y*this._y+this._z*this._z+this._w*this._w)}normalize(){let e=this.length();return e===0?(this._x=0,this._y=0,this._z=0,this._w=1):(e=1/e,this._x=this._x*e,this._y=this._y*e,this._z=this._z*e,this._w=this._w*e),this._onChangeCallback(),this}multiply(e){return this.multiplyQuaternions(this,e)}premultiply(e){return this.multiplyQuaternions(e,this)}multiplyQuaternions(e,t){let n=e._x,s=e._y,r=e._z,a=e._w,o=t._x,l=t._y,c=t._z,h=t._w;return this._x=n*h+a*o+s*c-r*l,this._y=s*h+a*l+r*o-n*c,this._z=r*h+a*c+n*l-s*o,this._w=a*h-n*o-s*l-r*c,this._onChangeCallback(),this}slerp(e,t){let n=e._x,s=e._y,r=e._z,a=e._w,o=this.dot(e);o<0&&(n=-n,s=-s,r=-r,a=-a,o=-o);let l=1-t;if(o<.9995){let c=Math.acos(o),h=Math.sin(c);l=Math.sin(l*c)/h,t=Math.sin(t*c)/h,this._x=this._x*l+n*t,this._y=this._y*l+s*t,this._z=this._z*l+r*t,this._w=this._w*l+a*t,this._onChangeCallback()}else this._x=this._x*l+n*t,this._y=this._y*l+s*t,this._z=this._z*l+r*t,this._w=this._w*l+a*t,this.normalize();return this}slerpQuaternions(e,t,n){return this.copy(e).slerp(t,n)}random(){let e=2*Math.PI*rt(),t=2*Math.PI*rt(),n=rt(),s=Math.sqrt(1-n),r=Math.sqrt(n);return this.set(s*Math.sin(e),s*Math.cos(e),r*Math.sin(t),r*Math.cos(t))}equals(e){return e._x===this._x&&e._y===this._y&&e._z===this._z&&e._w===this._w}fromArray(e,t=0){return this._x=e[t],this._y=e[t+1],this._z=e[t+2],this._w=e[t+3],this._onChangeCallback(),this}toArray(e=[],t=0){return e[t]=this._x,e[t+1]=this._y,e[t+2]=this._z,e[t+3]=this._w,e}fromBufferAttribute(e,t){return this._x=e.getX(t),this._y=e.getY(t),this._z=e.getZ(t),this._w=e.getW(t),this._onChangeCallback(),this}toJSON(){return this.toArray()}_onChange(e){return this._onChangeCallback=e,this}_onChangeCallback(){}*[Symbol.iterator](){yield this._x,yield this._y,yield this._z,yield this._w}},B=class i{static{i.prototype.isVector3=!0}constructor(e=0,t=0,n=0){this.x=e,this.y=t,this.z=n}set(e,t,n){return n===void 0&&(n=this.z),this.x=e,this.y=t,this.z=n,this}setScalar(e){return this.x=e,this.y=e,this.z=e,this}setX(e){return this.x=e,this}setY(e){return this.y=e,this}setZ(e){return this.z=e,this}setComponent(e,t){switch(e){case 0:this.x=t;break;case 1:this.y=t;break;case 2:this.z=t;break;default:throw new Error("THREE.Vector3: index is out of range: "+e)}return this}getComponent(e){switch(e){case 0:return this.x;case 1:return this.y;case 2:return this.z;default:throw new Error("THREE.Vector3: index is out of range: "+e)}}clone(){return new this.constructor(this.x,this.y,this.z)}copy(e){return this.x=e.x,this.y=e.y,this.z=e.z,this}add(e){return this.x+=e.x,this.y+=e.y,this.z+=e.z,this}addScalar(e){return this.x+=e,this.y+=e,this.z+=e,this}addVectors(e,t){return this.x=e.x+t.x,this.y=e.y+t.y,this.z=e.z+t.z,this}addScaledVector(e,t){return this.x+=e.x*t,this.y+=e.y*t,this.z+=e.z*t,this}sub(e){return this.x-=e.x,this.y-=e.y,this.z-=e.z,this}subScalar(e){return this.x-=e,this.y-=e,this.z-=e,this}subVectors(e,t){return this.x=e.x-t.x,this.y=e.y-t.y,this.z=e.z-t.z,this}multiply(e){return this.x*=e.x,this.y*=e.y,this.z*=e.z,this}multiplyScalar(e){return this.x*=e,this.y*=e,this.z*=e,this}multiplyVectors(e,t){return this.x=e.x*t.x,this.y=e.y*t.y,this.z=e.z*t.z,this}applyEuler(e){return this.applyQuaternion(qc.setFromEuler(e))}applyAxisAngle(e,t){return this.applyQuaternion(qc.setFromAxisAngle(e,t))}applyMatrix3(e){let t=this.x,n=this.y,s=this.z,r=e.elements;return this.x=r[0]*t+r[3]*n+r[6]*s,this.y=r[1]*t+r[4]*n+r[7]*s,this.z=r[2]*t+r[5]*n+r[8]*s,this}applyNormalMatrix(e){return this.applyMatrix3(e).normalize()}applyMatrix4(e){let t=this.x,n=this.y,s=this.z,r=e.elements,a=1/(r[3]*t+r[7]*n+r[11]*s+r[15]);return this.x=(r[0]*t+r[4]*n+r[8]*s+r[12])*a,this.y=(r[1]*t+r[5]*n+r[9]*s+r[13])*a,this.z=(r[2]*t+r[6]*n+r[10]*s+r[14])*a,this}applyQuaternion(e){let t=this.x,n=this.y,s=this.z,r=e.x,a=e.y,o=e.z,l=e.w,c=2*(a*s-o*n),h=2*(o*t-r*s),f=2*(r*n-a*t);return this.x=t+l*c+a*f-o*h,this.y=n+l*h+o*c-r*f,this.z=s+l*f+r*h-a*c,this}project(e){return this.applyMatrix4(e.matrixWorldInverse).applyMatrix4(e.projectionMatrix)}unproject(e){return this.applyMatrix4(e.projectionMatrixInverse).applyMatrix4(e.matrixWorld)}transformDirection(e){let t=this.x,n=this.y,s=this.z,r=e.elements;return this.x=r[0]*t+r[4]*n+r[8]*s,this.y=r[1]*t+r[5]*n+r[9]*s,this.z=r[2]*t+r[6]*n+r[10]*s,this.normalize()}divide(e){return this.x/=e.x,this.y/=e.y,this.z/=e.z,this}divideScalar(e){return this.multiplyScalar(1/e)}min(e){return this.x=Math.min(this.x,e.x),this.y=Math.min(this.y,e.y),this.z=Math.min(this.z,e.z),this}max(e){return this.x=Math.max(this.x,e.x),this.y=Math.max(this.y,e.y),this.z=Math.max(this.z,e.z),this}clamp(e,t){return this.x=ot(this.x,e.x,t.x),this.y=ot(this.y,e.y,t.y),this.z=ot(this.z,e.z,t.z),this}clampScalar(e,t){return this.x=ot(this.x,e,t),this.y=ot(this.y,e,t),this.z=ot(this.z,e,t),this}clampLength(e,t){let n=this.length();return this.divideScalar(n||1).multiplyScalar(ot(n,e,t))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this.z=Math.floor(this.z),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this.z=Math.ceil(this.z),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this.z=Math.round(this.z),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this.z=Math.trunc(this.z),this}negate(){return this.x=-this.x,this.y=-this.y,this.z=-this.z,this}dot(e){return this.x*e.x+this.y*e.y+this.z*e.z}lengthSq(){return this.x*this.x+this.y*this.y+this.z*this.z}length(){return Math.sqrt(this.x*this.x+this.y*this.y+this.z*this.z)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)+Math.abs(this.z)}normalize(){return this.divideScalar(this.length()||1)}setLength(e){return this.normalize().multiplyScalar(e)}lerp(e,t){return this.x+=(e.x-this.x)*t,this.y+=(e.y-this.y)*t,this.z+=(e.z-this.z)*t,this}lerpVectors(e,t,n){return this.x=e.x+(t.x-e.x)*n,this.y=e.y+(t.y-e.y)*n,this.z=e.z+(t.z-e.z)*n,this}cross(e){return this.crossVectors(this,e)}crossVectors(e,t){let n=e.x,s=e.y,r=e.z,a=t.x,o=t.y,l=t.z;return this.x=s*l-r*o,this.y=r*a-n*l,this.z=n*o-s*a,this}projectOnVector(e){let t=e.lengthSq();if(t===0)return this.set(0,0,0);let n=e.dot(this)/t;return this.copy(e).multiplyScalar(n)}projectOnPlane(e){return bl.copy(this).projectOnVector(e),this.sub(bl)}reflect(e){return this.sub(bl.copy(e).multiplyScalar(2*this.dot(e)))}angleTo(e){let t=Math.sqrt(this.lengthSq()*e.lengthSq());if(t===0)return Math.PI/2;let n=this.dot(e)/t;return Math.acos(ot(n,-1,1))}distanceTo(e){return Math.sqrt(this.distanceToSquared(e))}distanceToSquared(e){let t=this.x-e.x,n=this.y-e.y,s=this.z-e.z;return t*t+n*n+s*s}manhattanDistanceTo(e){return Math.abs(this.x-e.x)+Math.abs(this.y-e.y)+Math.abs(this.z-e.z)}setFromSpherical(e){return this.setFromSphericalCoords(e.radius,e.phi,e.theta)}setFromSphericalCoords(e,t,n){let s=Math.sin(t)*e;return this.x=s*Math.sin(n),this.y=Math.cos(t)*e,this.z=s*Math.cos(n),this}setFromCylindrical(e){return this.setFromCylindricalCoords(e.radius,e.theta,e.y)}setFromCylindricalCoords(e,t,n){return this.x=e*Math.sin(t),this.y=n,this.z=e*Math.cos(t),this}setFromMatrixPosition(e){let t=e.elements;return this.x=t[12],this.y=t[13],this.z=t[14],this}setFromMatrixScale(e){let t=this.setFromMatrixColumn(e,0).length(),n=this.setFromMatrixColumn(e,1).length(),s=this.setFromMatrixColumn(e,2).length();return this.x=t,this.y=n,this.z=s,this}setFromMatrixColumn(e,t){return this.fromArray(e.elements,t*4)}setFromMatrix3Column(e,t){return this.fromArray(e.elements,t*3)}setFromEuler(e){return this.x=e._x,this.y=e._y,this.z=e._z,this}setFromColor(e){return this.x=e.r,this.y=e.g,this.z=e.b,this}equals(e){return e.x===this.x&&e.y===this.y&&e.z===this.z}fromArray(e,t=0){return this.x=e[t],this.y=e[t+1],this.z=e[t+2],this}toArray(e=[],t=0){return e[t]=this.x,e[t+1]=this.y,e[t+2]=this.z,e}fromBufferAttribute(e,t){return this.x=e.getX(t),this.y=e.getY(t),this.z=e.getZ(t),this}random(){return this.x=rt(),this.y=rt(),this.z=rt(),this}randomDirection(){let e=rt()*Math.PI*2,t=rt()*2-1,n=Math.sqrt(1-t*t);return this.x=n*Math.cos(e),this.y=t,this.z=n*Math.sin(e),this}*[Symbol.iterator](){yield this.x,yield this.y,yield this.z}},bl=new B,qc=new Ot,Ye=class i{static{i.prototype.isMatrix3=!0}constructor(e,t,n,s,r,a,o,l,c){this.elements=[1,0,0,0,1,0,0,0,1],e!==void 0&&this.set(e,t,n,s,r,a,o,l,c)}set(e,t,n,s,r,a,o,l,c){let h=this.elements;return h[0]=e,h[1]=s,h[2]=o,h[3]=t,h[4]=r,h[5]=l,h[6]=n,h[7]=a,h[8]=c,this}identity(){return this.set(1,0,0,0,1,0,0,0,1),this}copy(e){let t=this.elements,n=e.elements;return t[0]=n[0],t[1]=n[1],t[2]=n[2],t[3]=n[3],t[4]=n[4],t[5]=n[5],t[6]=n[6],t[7]=n[7],t[8]=n[8],this}extractBasis(e,t,n){return e.setFromMatrix3Column(this,0),t.setFromMatrix3Column(this,1),n.setFromMatrix3Column(this,2),this}setFromMatrix4(e){let t=e.elements;return this.set(t[0],t[4],t[8],t[1],t[5],t[9],t[2],t[6],t[10]),this}multiply(e){return this.multiplyMatrices(this,e)}premultiply(e){return this.multiplyMatrices(e,this)}multiplyMatrices(e,t){let n=e.elements,s=t.elements,r=this.elements,a=n[0],o=n[3],l=n[6],c=n[1],h=n[4],f=n[7],u=n[2],d=n[5],_=n[8],S=s[0],g=s[3],p=s[6],w=s[1],I=s[4],y=s[7],A=s[2],E=s[5],D=s[8];return r[0]=a*S+o*w+l*A,r[3]=a*g+o*I+l*E,r[6]=a*p+o*y+l*D,r[1]=c*S+h*w+f*A,r[4]=c*g+h*I+f*E,r[7]=c*p+h*y+f*D,r[2]=u*S+d*w+_*A,r[5]=u*g+d*I+_*E,r[8]=u*p+d*y+_*D,this}multiplyScalar(e){let t=this.elements;return t[0]*=e,t[3]*=e,t[6]*=e,t[1]*=e,t[4]*=e,t[7]*=e,t[2]*=e,t[5]*=e,t[8]*=e,this}determinant(){let e=this.elements,t=e[0],n=e[1],s=e[2],r=e[3],a=e[4],o=e[5],l=e[6],c=e[7],h=e[8];return t*a*h-t*o*c-n*r*h+n*o*l+s*r*c-s*a*l}invert(){let e=this.elements,t=e[0],n=e[1],s=e[2],r=e[3],a=e[4],o=e[5],l=e[6],c=e[7],h=e[8],f=h*a-o*c,u=o*l-h*r,d=c*r-a*l,_=t*f+n*u+s*d;if(_===0)return this.set(0,0,0,0,0,0,0,0,0);let S=1/_;return e[0]=f*S,e[1]=(s*c-h*n)*S,e[2]=(o*n-s*a)*S,e[3]=u*S,e[4]=(h*t-s*l)*S,e[5]=(s*r-o*t)*S,e[6]=d*S,e[7]=(n*l-c*t)*S,e[8]=(a*t-n*r)*S,this}transpose(){let e,t=this.elements;return e=t[1],t[1]=t[3],t[3]=e,e=t[2],t[2]=t[6],t[6]=e,e=t[5],t[5]=t[7],t[7]=e,this}getNormalMatrix(e){return this.setFromMatrix4(e).invert().transpose()}transposeIntoArray(e){let t=this.elements;return e[0]=t[0],e[1]=t[3],e[2]=t[6],e[3]=t[1],e[4]=t[4],e[5]=t[7],e[6]=t[2],e[7]=t[5],e[8]=t[8],this}setUvTransform(e,t,n,s,r,a,o){let l=Math.cos(r),c=Math.sin(r);return this.set(n*l,n*c,-n*(l*a+c*o)+a+e,-s*c,s*l,-s*(-c*a+l*o)+o+t,0,0,1),this}scale(e,t){return Ni("Matrix3: .scale() is deprecated. Use .makeScale() instead."),this.premultiply(Ml.makeScale(e,t)),this}rotate(e){return Ni("Matrix3: .rotate() is deprecated. Use .makeRotation() instead."),this.premultiply(Ml.makeRotation(-e)),this}translate(e,t){return Ni("Matrix3: .translate() is deprecated. Use .makeTranslation() instead."),this.premultiply(Ml.makeTranslation(e,t)),this}makeTranslation(e,t){return e.isVector2?this.set(1,0,e.x,0,1,e.y,0,0,1):this.set(1,0,e,0,1,t,0,0,1),this}makeRotation(e){let t=Math.cos(e),n=Math.sin(e);return this.set(t,-n,0,n,t,0,0,0,1),this}makeScale(e,t){return this.set(e,0,0,0,t,0,0,0,1),this}equals(e){let t=this.elements,n=e.elements;for(let s=0;s<9;s++)if(t[s]!==n[s])return!1;return!0}fromArray(e,t=0){for(let n=0;n<9;n++)this.elements[n]=e[n+t];return this}toArray(e=[],t=0){let n=this.elements;return e[t]=n[0],e[t+1]=n[1],e[t+2]=n[2],e[t+3]=n[3],e[t+4]=n[4],e[t+5]=n[5],e[t+6]=n[6],e[t+7]=n[7],e[t+8]=n[8],e}clone(){return new this.constructor().fromArray(this.elements)}},Ml=new Ye,Xc=new Ye().set(.4123908,.3575843,.1804808,.212639,.7151687,.0721923,.0193308,.1191948,.9505322),Yc=new Ye().set(3.2409699,-1.5373832,-.4986108,-.9692436,1.8759675,.0415551,.0556301,-.203977,1.0569715);function yd(){let i={enabled:!0,workingColorSpace:tr,spaces:{},convert:function(s,r,a){return this.enabled===!1||r===a||!r||!a||(this.spaces[r].transfer===yt&&(s.r=Kn(s.r),s.g=Kn(s.g),s.b=Kn(s.b)),this.spaces[r].primaries!==this.spaces[a].primaries&&(s.applyMatrix3(this.spaces[r].toXYZ),s.applyMatrix3(this.spaces[a].fromXYZ)),this.spaces[a].transfer===yt&&(s.r=ds(s.r),s.g=ds(s.g),s.b=ds(s.b))),s},workingToColorSpace:function(s,r){return this.convert(s,this.workingColorSpace,r)},colorSpaceToWorking:function(s,r){return this.convert(s,r,this.workingColorSpace)},getPrimaries:function(s){return this.spaces[s].primaries},getTransfer:function(s){return s===ti?nr:this.spaces[s].transfer},getToneMappingMode:function(s){return this.spaces[s].outputColorSpaceConfig.toneMappingMode||"standard"},getLuminanceCoefficients:function(s,r=this.workingColorSpace){return s.fromArray(this.spaces[r].luminanceCoefficients)},define:function(s){Object.assign(this.spaces,s)},_getMatrix:function(s,r,a){return s.copy(this.spaces[r].toXYZ).multiply(this.spaces[a].fromXYZ)},_getDrawingBufferColorSpace:function(s){return this.spaces[s].outputColorSpaceConfig.drawingBufferColorSpace},_getUnpackColorSpace:function(s=this.workingColorSpace){return this.spaces[s].workingColorSpaceConfig.unpackColorSpace},fromWorkingColorSpace:function(s,r){return Ni("ColorManagement: .fromWorkingColorSpace() has been renamed to .workingToColorSpace()."),i.workingToColorSpace(s,r)},toWorkingColorSpace:function(s,r){return Ni("ColorManagement: .toWorkingColorSpace() has been renamed to .colorSpaceToWorking()."),i.colorSpaceToWorking(s,r)}},e=[.64,.33,.3,.6,.15,.06],t=[.2126,.7152,.0722],n=[.3127,.329];return i.define({[tr]:{primaries:e,whitePoint:n,transfer:nr,toXYZ:Xc,fromXYZ:Yc,luminanceCoefficients:t,workingColorSpaceConfig:{unpackColorSpace:nn},outputColorSpaceConfig:{drawingBufferColorSpace:nn}},[nn]:{primaries:e,whitePoint:n,transfer:yt,toXYZ:Xc,fromXYZ:Yc,luminanceCoefficients:t,outputColorSpaceConfig:{drawingBufferColorSpace:nn}}}),i}var at=yd();function Kn(i){return i<.04045?i*.0773993808:Math.pow(i*.9478672986+.0521327014,2.4)}function ds(i){return i<.0031308?i*12.92:1.055*Math.pow(i,.41666)-.055}var Ji,Oa=class{static getDataURL(e,t="image/png"){if(/^data:/i.test(e.src)||typeof HTMLCanvasElement>"u")return e.src;let n;if(e instanceof HTMLCanvasElement)n=e;else{Ji===void 0&&(Ji=ir("canvas")),Ji.width=e.width,Ji.height=e.height;let s=Ji.getContext("2d");e instanceof ImageData?s.putImageData(e,0,0):s.drawImage(e,0,0,e.width,e.height),n=Ji}return n.toDataURL(t)}static sRGBToLinear(e){if(typeof HTMLImageElement<"u"&&e instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&e instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&e instanceof ImageBitmap){let t=ir("canvas");t.width=e.width,t.height=e.height;let n=t.getContext("2d");n.drawImage(e,0,0,e.width,e.height);let s=n.getImageData(0,0,e.width,e.height),r=s.data;for(let a=0;a<r.length;a++)r[a]=Kn(r[a]/255)*255;return n.putImageData(s,0,0),t}else if(e.data){let t=e.data.slice(0);for(let n=0;n<t.length;n++)t instanceof Uint8Array||t instanceof Uint8ClampedArray?t[n]=Math.floor(Kn(t[n]/255)*255):t[n]=Kn(t[n]);return{data:t,width:e.width,height:e.height}}else return $e("ImageUtils.sRGBToLinear(): Unsupported image type. No color space conversion applied."),e}},bd=0,_s=class{constructor(e=null){this.isTextureSource=!0,Object.defineProperty(this,"id",{value:bd++}),this.uuid=Ps(),this.data=e,this.dataReady=!0,this.version=0}getSize(e){let t=this.data;return typeof HTMLVideoElement<"u"&&t instanceof HTMLVideoElement?e.set(t.videoWidth,t.videoHeight,0):typeof VideoFrame<"u"&&t instanceof VideoFrame?e.set(t.displayWidth,t.displayHeight,0):t!==null?e.set(t.width,t.height,t.depth||0):e.set(0,0,0),e}set needsUpdate(e){e===!0&&this.version++}toJSON(e){let t=e===void 0||typeof e=="string";if(!t&&e.images[this.uuid]!==void 0)return e.images[this.uuid];let n={uuid:this.uuid,url:""},s=this.data;if(s!==null){let r;if(Array.isArray(s)){r=[];for(let a=0,o=s.length;a<o;a++)s[a].isDataTexture?r.push(Sl(s[a].image)):r.push(Sl(s[a]))}else r=Sl(s);n.url=r}return t||(e.images[this.uuid]=n),n}};function Sl(i){return typeof HTMLImageElement<"u"&&i instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&i instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&i instanceof ImageBitmap?Oa.getDataURL(i):i.data?{data:Array.from(i.data),width:i.width,height:i.height,type:i.data.constructor.name}:($e("Texture: Unable to serialize Texture."),{})}var Md=0,Tl=new B,on=class i extends zn{constructor(e=i.DEFAULT_IMAGE,t=i.DEFAULT_MAPPING,n=On,s=On,r=Yt,a=Mi,o=Tn,l=un,c=i.DEFAULT_ANISOTROPY,h=ti){super(),this.isTexture=!0,Object.defineProperty(this,"id",{value:Md++}),this.uuid=Ps(),this.name="",this.source=new _s(e),this.mipmaps=[],this.mapping=t,this.channel=0,this.wrapS=n,this.wrapT=s,this.magFilter=r,this.minFilter=a,this.anisotropy=c,this.format=o,this.internalFormat=null,this.type=l,this.offset=new De(0,0),this.repeat=new De(1,1),this.center=new De(0,0),this.rotation=0,this.matrixAutoUpdate=!0,this.matrix=new Ye,this.generateMipmaps=!0,this.premultiplyAlpha=!1,this.flipY=!0,this.unpackAlignment=4,this.colorSpace=h,this.userData={},this.updateRanges=[],this.version=0,this.onUpdate=null,this.renderTarget=null,this.isRenderTargetTexture=!1,this.isArrayTexture=!!(e&&e.depth&&e.depth>1),this.pmremVersion=0,this.normalized=!1}get width(){return this.source.getSize(Tl).x}get height(){return this.source.getSize(Tl).y}get depth(){return this.source.getSize(Tl).z}get image(){return this.source.data}set image(e){this.source.data=e}updateMatrix(){this.matrix.setUvTransform(this.offset.x,this.offset.y,this.repeat.x,this.repeat.y,this.rotation,this.center.x,this.center.y)}addUpdateRange(e,t){this.updateRanges.push({start:e,count:t})}clearUpdateRanges(){this.updateRanges.length=0}clone(){return new this.constructor().copy(this)}copy(e){return this.name=e.name,this.source=e.source,this.mipmaps=e.mipmaps.slice(0),this.mapping=e.mapping,this.channel=e.channel,this.wrapS=e.wrapS,this.wrapT=e.wrapT,this.magFilter=e.magFilter,this.minFilter=e.minFilter,this.anisotropy=e.anisotropy,this.format=e.format,this.internalFormat=e.internalFormat,this.type=e.type,this.normalized=e.normalized,this.offset.copy(e.offset),this.repeat.copy(e.repeat),this.center.copy(e.center),this.rotation=e.rotation,this.matrixAutoUpdate=e.matrixAutoUpdate,this.matrix.copy(e.matrix),this.generateMipmaps=e.generateMipmaps,this.premultiplyAlpha=e.premultiplyAlpha,this.flipY=e.flipY,this.unpackAlignment=e.unpackAlignment,this.colorSpace=e.colorSpace,this.renderTarget=e.renderTarget,this.isRenderTargetTexture=e.isRenderTargetTexture,this.isArrayTexture=e.isArrayTexture,this.userData=JSON.parse(JSON.stringify(e.userData)),this.needsUpdate=!0,this}setValues(e){for(let t in e){let n=e[t];if(n===void 0){$e(`Texture.setValues(): parameter '${t}' has value of undefined.`);continue}let s=this[t];if(s===void 0){$e(`Texture.setValues(): property '${t}' does not exist.`);continue}s&&n&&s.isVector2&&n.isVector2||s&&n&&s.isVector3&&n.isVector3||s&&n&&s.isMatrix3&&n.isMatrix3?s.copy(n):this[t]=n}}toJSON(e){let t=e===void 0||typeof e=="string";if(!t&&e.textures[this.uuid]!==void 0)return e.textures[this.uuid];let n={metadata:{version:4.7,type:"Texture",generator:"Texture.toJSON"},uuid:this.uuid,name:this.name,image:this.source.toJSON(e).uuid,mapping:this.mapping,channel:this.channel,repeat:[this.repeat.x,this.repeat.y],offset:[this.offset.x,this.offset.y],center:[this.center.x,this.center.y],rotation:this.rotation,wrap:[this.wrapS,this.wrapT],format:this.format,internalFormat:this.internalFormat,type:this.type,normalized:this.normalized,colorSpace:this.colorSpace,minFilter:this.minFilter,magFilter:this.magFilter,anisotropy:this.anisotropy,flipY:this.flipY,generateMipmaps:this.generateMipmaps,premultiplyAlpha:this.premultiplyAlpha,unpackAlignment:this.unpackAlignment};return Object.keys(this.userData).length>0&&(n.userData=this.userData),t||(e.textures[this.uuid]=n),n}dispose(){this.dispatchEvent({type:"dispose"})}transformUv(e){if(this.mapping!==oc)return e;if(e.applyMatrix3(this.matrix),e.x<0||e.x>1)switch(this.wrapS){case Ua:e.x=e.x-Math.floor(e.x);break;case On:e.x=e.x<0?0:1;break;case Fa:Math.abs(Math.floor(e.x)%2)===1?e.x=Math.ceil(e.x)-e.x:e.x=e.x-Math.floor(e.x);break}if(e.y<0||e.y>1)switch(this.wrapT){case Ua:e.y=e.y-Math.floor(e.y);break;case On:e.y=e.y<0?0:1;break;case Fa:Math.abs(Math.floor(e.y)%2)===1?e.y=Math.ceil(e.y)-e.y:e.y=e.y-Math.floor(e.y);break}return this.flipY&&(e.y=1-e.y),e}set needsUpdate(e){e===!0&&(this.version++,this.source.needsUpdate=!0)}set needsPMREMUpdate(e){e===!0&&this.pmremVersion++}};on.DEFAULT_IMAGE=null;on.DEFAULT_MAPPING=oc;on.DEFAULT_ANISOTROPY=1;var It=class i{static{i.prototype.isVector4=!0}constructor(e=0,t=0,n=0,s=1){this.x=e,this.y=t,this.z=n,this.w=s}get width(){return this.z}set width(e){this.z=e}get height(){return this.w}set height(e){this.w=e}set(e,t,n,s){return this.x=e,this.y=t,this.z=n,this.w=s,this}setScalar(e){return this.x=e,this.y=e,this.z=e,this.w=e,this}setX(e){return this.x=e,this}setY(e){return this.y=e,this}setZ(e){return this.z=e,this}setW(e){return this.w=e,this}setComponent(e,t){switch(e){case 0:this.x=t;break;case 1:this.y=t;break;case 2:this.z=t;break;case 3:this.w=t;break;default:throw new Error("THREE.Vector4: index is out of range: "+e)}return this}getComponent(e){switch(e){case 0:return this.x;case 1:return this.y;case 2:return this.z;case 3:return this.w;default:throw new Error("THREE.Vector4: index is out of range: "+e)}}clone(){return new this.constructor(this.x,this.y,this.z,this.w)}copy(e){return this.x=e.x,this.y=e.y,this.z=e.z,this.w=e.w!==void 0?e.w:1,this}add(e){return this.x+=e.x,this.y+=e.y,this.z+=e.z,this.w+=e.w,this}addScalar(e){return this.x+=e,this.y+=e,this.z+=e,this.w+=e,this}addVectors(e,t){return this.x=e.x+t.x,this.y=e.y+t.y,this.z=e.z+t.z,this.w=e.w+t.w,this}addScaledVector(e,t){return this.x+=e.x*t,this.y+=e.y*t,this.z+=e.z*t,this.w+=e.w*t,this}sub(e){return this.x-=e.x,this.y-=e.y,this.z-=e.z,this.w-=e.w,this}subScalar(e){return this.x-=e,this.y-=e,this.z-=e,this.w-=e,this}subVectors(e,t){return this.x=e.x-t.x,this.y=e.y-t.y,this.z=e.z-t.z,this.w=e.w-t.w,this}multiply(e){return this.x*=e.x,this.y*=e.y,this.z*=e.z,this.w*=e.w,this}multiplyScalar(e){return this.x*=e,this.y*=e,this.z*=e,this.w*=e,this}applyMatrix4(e){let t=this.x,n=this.y,s=this.z,r=this.w,a=e.elements;return this.x=a[0]*t+a[4]*n+a[8]*s+a[12]*r,this.y=a[1]*t+a[5]*n+a[9]*s+a[13]*r,this.z=a[2]*t+a[6]*n+a[10]*s+a[14]*r,this.w=a[3]*t+a[7]*n+a[11]*s+a[15]*r,this}divide(e){return this.x/=e.x,this.y/=e.y,this.z/=e.z,this.w/=e.w,this}divideScalar(e){return this.multiplyScalar(1/e)}setAxisAngleFromQuaternion(e){this.w=2*Math.acos(e.w);let t=Math.sqrt(1-e.w*e.w);return t<1e-4?(this.x=1,this.y=0,this.z=0):(this.x=e.x/t,this.y=e.y/t,this.z=e.z/t),this}setAxisAngleFromRotationMatrix(e){let t,n,s,r,l=e.elements,c=l[0],h=l[4],f=l[8],u=l[1],d=l[5],_=l[9],S=l[2],g=l[6],p=l[10];if(Math.abs(h-u)<.01&&Math.abs(f-S)<.01&&Math.abs(_-g)<.01){if(Math.abs(h+u)<.1&&Math.abs(f+S)<.1&&Math.abs(_+g)<.1&&Math.abs(c+d+p-3)<.1)return this.set(1,0,0,0),this;t=Math.PI;let I=(c+1)/2,y=(d+1)/2,A=(p+1)/2,E=(h+u)/4,D=(f+S)/4,v=(_+g)/4;return I>y&&I>A?I<.01?(n=0,s=.707106781,r=.707106781):(n=Math.sqrt(I),s=E/n,r=D/n):y>A?y<.01?(n=.707106781,s=0,r=.707106781):(s=Math.sqrt(y),n=E/s,r=v/s):A<.01?(n=.707106781,s=.707106781,r=0):(r=Math.sqrt(A),n=D/r,s=v/r),this.set(n,s,r,t),this}let w=Math.sqrt((g-_)*(g-_)+(f-S)*(f-S)+(u-h)*(u-h));return Math.abs(w)<.001&&(w=1),this.x=(g-_)/w,this.y=(f-S)/w,this.z=(u-h)/w,this.w=Math.acos((c+d+p-1)/2),this}setFromMatrixPosition(e){let t=e.elements;return this.x=t[12],this.y=t[13],this.z=t[14],this.w=t[15],this}min(e){return this.x=Math.min(this.x,e.x),this.y=Math.min(this.y,e.y),this.z=Math.min(this.z,e.z),this.w=Math.min(this.w,e.w),this}max(e){return this.x=Math.max(this.x,e.x),this.y=Math.max(this.y,e.y),this.z=Math.max(this.z,e.z),this.w=Math.max(this.w,e.w),this}clamp(e,t){return this.x=ot(this.x,e.x,t.x),this.y=ot(this.y,e.y,t.y),this.z=ot(this.z,e.z,t.z),this.w=ot(this.w,e.w,t.w),this}clampScalar(e,t){return this.x=ot(this.x,e,t),this.y=ot(this.y,e,t),this.z=ot(this.z,e,t),this.w=ot(this.w,e,t),this}clampLength(e,t){let n=this.length();return this.divideScalar(n||1).multiplyScalar(ot(n,e,t))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this.z=Math.floor(this.z),this.w=Math.floor(this.w),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this.z=Math.ceil(this.z),this.w=Math.ceil(this.w),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this.z=Math.round(this.z),this.w=Math.round(this.w),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this.z=Math.trunc(this.z),this.w=Math.trunc(this.w),this}negate(){return this.x=-this.x,this.y=-this.y,this.z=-this.z,this.w=-this.w,this}dot(e){return this.x*e.x+this.y*e.y+this.z*e.z+this.w*e.w}lengthSq(){return this.x*this.x+this.y*this.y+this.z*this.z+this.w*this.w}length(){return Math.sqrt(this.x*this.x+this.y*this.y+this.z*this.z+this.w*this.w)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)+Math.abs(this.z)+Math.abs(this.w)}normalize(){return this.divideScalar(this.length()||1)}setLength(e){return this.normalize().multiplyScalar(e)}lerp(e,t){return this.x+=(e.x-this.x)*t,this.y+=(e.y-this.y)*t,this.z+=(e.z-this.z)*t,this.w+=(e.w-this.w)*t,this}lerpVectors(e,t,n){return this.x=e.x+(t.x-e.x)*n,this.y=e.y+(t.y-e.y)*n,this.z=e.z+(t.z-e.z)*n,this.w=e.w+(t.w-e.w)*n,this}equals(e){return e.x===this.x&&e.y===this.y&&e.z===this.z&&e.w===this.w}fromArray(e,t=0){return this.x=e[t],this.y=e[t+1],this.z=e[t+2],this.w=e[t+3],this}toArray(e=[],t=0){return e[t]=this.x,e[t+1]=this.y,e[t+2]=this.z,e[t+3]=this.w,e}fromBufferAttribute(e,t){return this.x=e.getX(t),this.y=e.getY(t),this.z=e.getZ(t),this.w=e.getW(t),this}random(){return this.x=rt(),this.y=rt(),this.z=rt(),this.w=rt(),this}*[Symbol.iterator](){yield this.x,yield this.y,yield this.z,yield this.w}},Ba=class extends zn{constructor(e=1,t=1,n={}){super(),n=Object.assign({generateMipmaps:!1,internalFormat:null,minFilter:Yt,depthBuffer:!0,stencilBuffer:!1,resolveColorBuffer:!0,resolveDepthBuffer:!0,resolveStencilBuffer:!0,storeMultisampledColorBuffer:!0,storeMultisampledDepthBuffer:!0,storeMultisampledStencilBuffer:!0,depthTexture:null,samples:0,count:1,depth:1,multiview:!1,useArrayDepthTexture:!1},n),this.isRenderTarget=!0,this.width=e,this.height=t,this.depth=n.depth,this.scissor=new It(0,0,e,t),this.scissorTest=!1,this.viewport=new It(0,0,e,t),this.textures=[];let s={width:e,height:t,depth:n.depth},r=new on(s),a=n.count;for(let o=0;o<a;o++)this.textures[o]=r.clone(),this.textures[o].isRenderTargetTexture=!0,this.textures[o].renderTarget=this;this._setTextureOptions(n),this.depthBuffer=n.depthBuffer,this.stencilBuffer=n.stencilBuffer,this.resolveColorBuffer=n.resolveColorBuffer,this.resolveDepthBuffer=n.resolveDepthBuffer,this.resolveStencilBuffer=n.resolveStencilBuffer,this.storeMultisampledColorBuffer=n.storeMultisampledColorBuffer,this.storeMultisampledDepthBuffer=n.storeMultisampledDepthBuffer,this.storeMultisampledStencilBuffer=n.storeMultisampledStencilBuffer,this._depthTexture=null,this.depthTexture=n.depthTexture,this.samples=n.samples,this.multiview=n.multiview,this.useArrayDepthTexture=n.useArrayDepthTexture}_setTextureOptions(e={}){let t={minFilter:Yt,generateMipmaps:!1,flipY:!1,internalFormat:null};e.mapping!==void 0&&(t.mapping=e.mapping),e.wrapS!==void 0&&(t.wrapS=e.wrapS),e.wrapT!==void 0&&(t.wrapT=e.wrapT),e.wrapR!==void 0&&(t.wrapR=e.wrapR),e.magFilter!==void 0&&(t.magFilter=e.magFilter),e.minFilter!==void 0&&(t.minFilter=e.minFilter),e.format!==void 0&&(t.format=e.format),e.type!==void 0&&(t.type=e.type),e.anisotropy!==void 0&&(t.anisotropy=e.anisotropy),e.colorSpace!==void 0&&(t.colorSpace=e.colorSpace),e.flipY!==void 0&&(t.flipY=e.flipY),e.generateMipmaps!==void 0&&(t.generateMipmaps=e.generateMipmaps),e.internalFormat!==void 0&&(t.internalFormat=e.internalFormat);for(let n=0;n<this.textures.length;n++)this.textures[n].setValues(t)}get texture(){return this.textures[0]}set texture(e){this.textures[0]=e}set depthTexture(e){this._depthTexture!==null&&this._depthTexture.renderTarget===this&&(this._depthTexture.renderTarget=null),e!==null&&e.renderTarget===null&&(e.renderTarget=this),this._depthTexture=e}get depthTexture(){return this._depthTexture}setSize(e,t,n=1){if(this.width!==e||this.height!==t||this.depth!==n){this.width=e,this.height=t,this.depth=n;for(let s=0,r=this.textures.length;s<r;s++)this.textures[s].image.width=e,this.textures[s].image.height=t,this.textures[s].image.depth=n,this.textures[s].isData3DTexture!==!0&&(this.textures[s].isArrayTexture=this.textures[s].image.depth>1);this.dispose()}this.viewport.set(0,0,e,t),this.scissor.set(0,0,e,t)}clone(){return new this.constructor().copy(this)}copy(e){this.width=e.width,this.height=e.height,this.depth=e.depth,this.scissor.copy(e.scissor),this.scissorTest=e.scissorTest,this.viewport.copy(e.viewport),this.textures.length=0;for(let t=0,n=e.textures.length;t<n;t++){this.textures[t]=e.textures[t].clone(),this.textures[t].isRenderTargetTexture=!0,this.textures[t].renderTarget=this;let s=Object.assign({},e.textures[t].image);this.textures[t].source=new _s(s)}if(this.depthBuffer=e.depthBuffer,this.stencilBuffer=e.stencilBuffer,this.resolveColorBuffer=e.resolveColorBuffer,this.resolveDepthBuffer=e.resolveDepthBuffer,this.resolveStencilBuffer=e.resolveStencilBuffer,this.storeMultisampledColorBuffer=e.storeMultisampledColorBuffer,this.storeMultisampledDepthBuffer=e.storeMultisampledDepthBuffer,this.storeMultisampledStencilBuffer=e.storeMultisampledStencilBuffer,e.depthTexture!==null)if(e.depthTexture.renderTarget===e){let t=e.depthTexture.clone();t.renderTarget=null,this.depthTexture=t}else this.depthTexture=e.depthTexture;return this.samples=e.samples,this.multiview=e.multiview,this.useArrayDepthTexture=e.useArrayDepthTexture,this}dispose(){this.dispatchEvent({type:"dispose"})}},Ft=class extends Ba{constructor(e=1,t=1,n={}){super(e,t,n),this.isWebGLRenderTarget=!0}},sr=class extends on{constructor(e=null,t=1,n=1,s=1){super(null),this.isDataArrayTexture=!0,this.image={data:e,width:t,height:n,depth:s},this.magFilter=Gt,this.minFilter=Gt,this.wrapR=On,this.generateMipmaps=!1,this.flipY=!1,this.unpackAlignment=1,this.layerUpdates=new Set}copy(e){return super.copy(e),this.wrapR=e.wrapR,this}addLayerUpdate(e){this.layerUpdates.add(e)}clearLayerUpdates(){this.layerUpdates.clear()}};var za=class extends on{constructor(e=null,t=1,n=1,s=1){super(null),this.isData3DTexture=!0,this.image={data:e,width:t,height:n,depth:s},this.magFilter=Gt,this.minFilter=Gt,this.wrapR=On,this.generateMipmaps=!1,this.flipY=!1,this.unpackAlignment=1}copy(e){return super.copy(e),this.wrapR=e.wrapR,this}};var ut=class i{static{i.prototype.isMatrix4=!0}constructor(e,t,n,s,r,a,o,l,c,h,f,u,d,_,S,g){this.elements=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1],e!==void 0&&this.set(e,t,n,s,r,a,o,l,c,h,f,u,d,_,S,g)}set(e,t,n,s,r,a,o,l,c,h,f,u,d,_,S,g){let p=this.elements;return p[0]=e,p[4]=t,p[8]=n,p[12]=s,p[1]=r,p[5]=a,p[9]=o,p[13]=l,p[2]=c,p[6]=h,p[10]=f,p[14]=u,p[3]=d,p[7]=_,p[11]=S,p[15]=g,this}identity(){return this.set(1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1),this}clone(){return new i().fromArray(this.elements)}copy(e){let t=this.elements,n=e.elements;return t[0]=n[0],t[1]=n[1],t[2]=n[2],t[3]=n[3],t[4]=n[4],t[5]=n[5],t[6]=n[6],t[7]=n[7],t[8]=n[8],t[9]=n[9],t[10]=n[10],t[11]=n[11],t[12]=n[12],t[13]=n[13],t[14]=n[14],t[15]=n[15],this}copyPosition(e){let t=this.elements,n=e.elements;return t[12]=n[12],t[13]=n[13],t[14]=n[14],this}setFromMatrix3(e){let t=e.elements;return this.set(t[0],t[3],t[6],0,t[1],t[4],t[7],0,t[2],t[5],t[8],0,0,0,0,1),this}extractBasis(e,t,n){return this.determinantAffine()===0?(e.set(1,0,0),t.set(0,1,0),n.set(0,0,1),this):(e.setFromMatrixColumn(this,0),t.setFromMatrixColumn(this,1),n.setFromMatrixColumn(this,2),this)}makeBasis(e,t,n){return this.set(e.x,t.x,n.x,0,e.y,t.y,n.y,0,e.z,t.z,n.z,0,0,0,0,1),this}extractRotation(e){if(e.determinantAffine()===0)return this.identity();let t=this.elements,n=e.elements,s=1/Ki.setFromMatrixColumn(e,0).length(),r=1/Ki.setFromMatrixColumn(e,1).length(),a=1/Ki.setFromMatrixColumn(e,2).length();return t[0]=n[0]*s,t[1]=n[1]*s,t[2]=n[2]*s,t[3]=0,t[4]=n[4]*r,t[5]=n[5]*r,t[6]=n[6]*r,t[7]=0,t[8]=n[8]*a,t[9]=n[9]*a,t[10]=n[10]*a,t[11]=0,t[12]=0,t[13]=0,t[14]=0,t[15]=1,this}makeRotationFromEuler(e){let t=this.elements,n=e.x,s=e.y,r=e.z,a=Math.cos(n),o=Math.sin(n),l=Math.cos(s),c=Math.sin(s),h=Math.cos(r),f=Math.sin(r);if(e.order==="XYZ"){let u=a*h,d=a*f,_=o*h,S=o*f;t[0]=l*h,t[4]=-l*f,t[8]=c,t[1]=d+_*c,t[5]=u-S*c,t[9]=-o*l,t[2]=S-u*c,t[6]=_+d*c,t[10]=a*l}else if(e.order==="YXZ"){let u=l*h,d=l*f,_=c*h,S=c*f;t[0]=u+S*o,t[4]=_*o-d,t[8]=a*c,t[1]=a*f,t[5]=a*h,t[9]=-o,t[2]=d*o-_,t[6]=S+u*o,t[10]=a*l}else if(e.order==="ZXY"){let u=l*h,d=l*f,_=c*h,S=c*f;t[0]=u-S*o,t[4]=-a*f,t[8]=_+d*o,t[1]=d+_*o,t[5]=a*h,t[9]=S-u*o,t[2]=-a*c,t[6]=o,t[10]=a*l}else if(e.order==="ZYX"){let u=a*h,d=a*f,_=o*h,S=o*f;t[0]=l*h,t[4]=_*c-d,t[8]=u*c+S,t[1]=l*f,t[5]=S*c+u,t[9]=d*c-_,t[2]=-c,t[6]=o*l,t[10]=a*l}else if(e.order==="YZX"){let u=a*l,d=a*c,_=o*l,S=o*c;t[0]=l*h,t[4]=S-u*f,t[8]=_*f+d,t[1]=f,t[5]=a*h,t[9]=-o*h,t[2]=-c*h,t[6]=d*f+_,t[10]=u-S*f}else if(e.order==="XZY"){let u=a*l,d=a*c,_=o*l,S=o*c;t[0]=l*h,t[4]=-f,t[8]=c*h,t[1]=u*f+S,t[5]=a*h,t[9]=d*f-_,t[2]=_*f-d,t[6]=o*h,t[10]=S*f+u}return t[3]=0,t[7]=0,t[11]=0,t[12]=0,t[13]=0,t[14]=0,t[15]=1,this}makeRotationFromQuaternion(e){return this.compose(Sd,e,Td)}lookAt(e,t,n){let s=this.elements;return dn.subVectors(e,t),dn.lengthSq()===0&&(dn.z=1),dn.normalize(),ci.crossVectors(n,dn),ci.lengthSq()===0&&(Math.abs(n.z)===1?dn.x+=1e-4:dn.z+=1e-4,dn.normalize(),ci.crossVectors(n,dn)),ci.normalize(),na.crossVectors(dn,ci),s[0]=ci.x,s[4]=na.x,s[8]=dn.x,s[1]=ci.y,s[5]=na.y,s[9]=dn.y,s[2]=ci.z,s[6]=na.z,s[10]=dn.z,this}multiply(e){return this.multiplyMatrices(this,e)}premultiply(e){return this.multiplyMatrices(e,this)}multiplyMatrices(e,t){let n=e.elements,s=t.elements,r=this.elements,a=n[0],o=n[4],l=n[8],c=n[12],h=n[1],f=n[5],u=n[9],d=n[13],_=n[2],S=n[6],g=n[10],p=n[14],w=n[3],I=n[7],y=n[11],A=n[15],E=s[0],D=s[4],v=s[8],C=s[12],O=s[1],V=s[5],q=s[9],j=s[13],z=s[2],Y=s[6],te=s[10],re=s[14],Z=s[3],Q=s[7],le=s[11],se=s[15];return r[0]=a*E+o*O+l*z+c*Z,r[4]=a*D+o*V+l*Y+c*Q,r[8]=a*v+o*q+l*te+c*le,r[12]=a*C+o*j+l*re+c*se,r[1]=h*E+f*O+u*z+d*Z,r[5]=h*D+f*V+u*Y+d*Q,r[9]=h*v+f*q+u*te+d*le,r[13]=h*C+f*j+u*re+d*se,r[2]=_*E+S*O+g*z+p*Z,r[6]=_*D+S*V+g*Y+p*Q,r[10]=_*v+S*q+g*te+p*le,r[14]=_*C+S*j+g*re+p*se,r[3]=w*E+I*O+y*z+A*Z,r[7]=w*D+I*V+y*Y+A*Q,r[11]=w*v+I*q+y*te+A*le,r[15]=w*C+I*j+y*re+A*se,this}multiplyScalar(e){let t=this.elements;return t[0]*=e,t[4]*=e,t[8]*=e,t[12]*=e,t[1]*=e,t[5]*=e,t[9]*=e,t[13]*=e,t[2]*=e,t[6]*=e,t[10]*=e,t[14]*=e,t[3]*=e,t[7]*=e,t[11]*=e,t[15]*=e,this}determinant(){let e=this.elements,t=e[0],n=e[4],s=e[8],r=e[12],a=e[1],o=e[5],l=e[9],c=e[13],h=e[2],f=e[6],u=e[10],d=e[14],_=e[3],S=e[7],g=e[11],p=e[15],w=l*d-c*u,I=o*d-c*f,y=o*u-l*f,A=a*d-c*h,E=a*u-l*h,D=a*f-o*h;return t*(S*w-g*I+p*y)-n*(_*w-g*A+p*E)+s*(_*I-S*A+p*D)-r*(_*y-S*E+g*D)}determinantAffine(){let e=this.elements,t=e[0],n=e[4],s=e[8],r=e[1],a=e[5],o=e[9],l=e[2],c=e[6],h=e[10];return t*(a*h-o*c)-n*(r*h-o*l)+s*(r*c-a*l)}transpose(){let e=this.elements,t;return t=e[1],e[1]=e[4],e[4]=t,t=e[2],e[2]=e[8],e[8]=t,t=e[6],e[6]=e[9],e[9]=t,t=e[3],e[3]=e[12],e[12]=t,t=e[7],e[7]=e[13],e[13]=t,t=e[11],e[11]=e[14],e[14]=t,this}setPosition(e,t,n){let s=this.elements;return e.isVector3?(s[12]=e.x,s[13]=e.y,s[14]=e.z):(s[12]=e,s[13]=t,s[14]=n),this}invert(){let e=this.elements,t=e[0],n=e[1],s=e[2],r=e[3],a=e[4],o=e[5],l=e[6],c=e[7],h=e[8],f=e[9],u=e[10],d=e[11],_=e[12],S=e[13],g=e[14],p=e[15],w=t*o-n*a,I=t*l-s*a,y=t*c-r*a,A=n*l-s*o,E=n*c-r*o,D=s*c-r*l,v=h*S-f*_,C=h*g-u*_,O=h*p-d*_,V=f*g-u*S,q=f*p-d*S,j=u*p-d*g,z=w*j-I*q+y*V+A*O-E*C+D*v;if(z===0)return this.set(0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0);let Y=1/z;return e[0]=(o*j-l*q+c*V)*Y,e[1]=(s*q-n*j-r*V)*Y,e[2]=(S*D-g*E+p*A)*Y,e[3]=(u*E-f*D-d*A)*Y,e[4]=(l*O-a*j-c*C)*Y,e[5]=(t*j-s*O+r*C)*Y,e[6]=(g*y-_*D-p*I)*Y,e[7]=(h*D-u*y+d*I)*Y,e[8]=(a*q-o*O+c*v)*Y,e[9]=(n*O-t*q-r*v)*Y,e[10]=(_*E-S*y+p*w)*Y,e[11]=(f*y-h*E-d*w)*Y,e[12]=(o*C-a*V-l*v)*Y,e[13]=(t*V-n*C+s*v)*Y,e[14]=(S*I-_*A-g*w)*Y,e[15]=(h*A-f*I+u*w)*Y,this}scale(e){let t=this.elements,n=e.x,s=e.y,r=e.z;return t[0]*=n,t[4]*=s,t[8]*=r,t[1]*=n,t[5]*=s,t[9]*=r,t[2]*=n,t[6]*=s,t[10]*=r,t[3]*=n,t[7]*=s,t[11]*=r,this}getMaxScaleOnAxis(){let e=this.elements,t=e[0]*e[0]+e[1]*e[1]+e[2]*e[2],n=e[4]*e[4]+e[5]*e[5]+e[6]*e[6],s=e[8]*e[8]+e[9]*e[9]+e[10]*e[10];return Math.sqrt(Math.max(t,n,s))}makeTranslation(e,t,n){return e.isVector3?this.set(1,0,0,e.x,0,1,0,e.y,0,0,1,e.z,0,0,0,1):this.set(1,0,0,e,0,1,0,t,0,0,1,n,0,0,0,1),this}makeRotationX(e){let t=Math.cos(e),n=Math.sin(e);return this.set(1,0,0,0,0,t,-n,0,0,n,t,0,0,0,0,1),this}makeRotationY(e){let t=Math.cos(e),n=Math.sin(e);return this.set(t,0,n,0,0,1,0,0,-n,0,t,0,0,0,0,1),this}makeRotationZ(e){let t=Math.cos(e),n=Math.sin(e);return this.set(t,-n,0,0,n,t,0,0,0,0,1,0,0,0,0,1),this}makeRotationAxis(e,t){let n=Math.cos(t),s=Math.sin(t),r=1-n,a=e.x,o=e.y,l=e.z,c=r*a,h=r*o;return this.set(c*a+n,c*o-s*l,c*l+s*o,0,c*o+s*l,h*o+n,h*l-s*a,0,c*l-s*o,h*l+s*a,r*l*l+n,0,0,0,0,1),this}makeScale(e,t,n){return this.set(e,0,0,0,0,t,0,0,0,0,n,0,0,0,0,1),this}makeShear(e,t,n,s,r,a){return this.set(1,n,r,0,e,1,a,0,t,s,1,0,0,0,0,1),this}compose(e,t,n){let s=this.elements,r=t._x,a=t._y,o=t._z,l=t._w,c=r+r,h=a+a,f=o+o,u=r*c,d=r*h,_=r*f,S=a*h,g=a*f,p=o*f,w=l*c,I=l*h,y=l*f,A=n.x,E=n.y,D=n.z;return s[0]=(1-(S+p))*A,s[1]=(d+y)*A,s[2]=(_-I)*A,s[3]=0,s[4]=(d-y)*E,s[5]=(1-(u+p))*E,s[6]=(g+w)*E,s[7]=0,s[8]=(_+I)*D,s[9]=(g-w)*D,s[10]=(1-(u+S))*D,s[11]=0,s[12]=e.x,s[13]=e.y,s[14]=e.z,s[15]=1,this}decompose(e,t,n){let s=this.elements;e.x=s[12],e.y=s[13],e.z=s[14];let r=this.determinantAffine();if(r===0)return n.set(1,1,1),t.identity(),this;let a=Ki.set(s[0],s[1],s[2]).length(),o=Ki.set(s[4],s[5],s[6]).length(),l=Ki.set(s[8],s[9],s[10]).length();r<0&&(a=-a),An.copy(this);let c=1/a,h=1/o,f=1/l;return An.elements[0]*=c,An.elements[1]*=c,An.elements[2]*=c,An.elements[4]*=h,An.elements[5]*=h,An.elements[6]*=h,An.elements[8]*=f,An.elements[9]*=f,An.elements[10]*=f,t.setFromRotationMatrix(An),n.x=a,n.y=o,n.z=l,this}makePerspective(e,t,n,s,r,a,o=Pn,l=!1){let c=this.elements,h=2*r/(t-e),f=2*r/(n-s),u=(t+e)/(t-e),d=(n+s)/(n-s),_,S;if(l)_=r/(a-r),S=a*r/(a-r);else if(o===Pn)_=-(a+r)/(a-r),S=-2*a*r/(a-r);else if(o===ps)_=-a/(a-r),S=-a*r/(a-r);else throw new Error("THREE.Matrix4.makePerspective(): Invalid coordinate system: "+o);return c[0]=h,c[4]=0,c[8]=u,c[12]=0,c[1]=0,c[5]=f,c[9]=d,c[13]=0,c[2]=0,c[6]=0,c[10]=_,c[14]=S,c[3]=0,c[7]=0,c[11]=-1,c[15]=0,this}makeOrthographic(e,t,n,s,r,a,o=Pn,l=!1){let c=this.elements,h=2/(t-e),f=2/(n-s),u=-(t+e)/(t-e),d=-(n+s)/(n-s),_,S;if(l)_=1/(a-r),S=a/(a-r);else if(o===Pn)_=-2/(a-r),S=-(a+r)/(a-r);else if(o===ps)_=-1/(a-r),S=-r/(a-r);else throw new Error("THREE.Matrix4.makeOrthographic(): Invalid coordinate system: "+o);return c[0]=h,c[4]=0,c[8]=0,c[12]=u,c[1]=0,c[5]=f,c[9]=0,c[13]=d,c[2]=0,c[6]=0,c[10]=_,c[14]=S,c[3]=0,c[7]=0,c[11]=0,c[15]=1,this}equals(e){let t=this.elements,n=e.elements;for(let s=0;s<16;s++)if(t[s]!==n[s])return!1;return!0}fromArray(e,t=0){for(let n=0;n<16;n++)this.elements[n]=e[n+t];return this}toArray(e=[],t=0){let n=this.elements;return e[t]=n[0],e[t+1]=n[1],e[t+2]=n[2],e[t+3]=n[3],e[t+4]=n[4],e[t+5]=n[5],e[t+6]=n[6],e[t+7]=n[7],e[t+8]=n[8],e[t+9]=n[9],e[t+10]=n[10],e[t+11]=n[11],e[t+12]=n[12],e[t+13]=n[13],e[t+14]=n[14],e[t+15]=n[15],e}},Ki=new B,An=new ut,Sd=new B(0,0,0),Td=new B(1,1,1),ci=new B,na=new B,dn=new B,Zc=new ut,jc=new Ot,vn=class i{constructor(e=0,t=0,n=0,s=i.DEFAULT_ORDER){this.isEuler=!0,this._x=e,this._y=t,this._z=n,this._order=s}get x(){return this._x}set x(e){this._x=e,this._onChangeCallback()}get y(){return this._y}set y(e){this._y=e,this._onChangeCallback()}get z(){return this._z}set z(e){this._z=e,this._onChangeCallback()}get order(){return this._order}set order(e){this._order=e,this._onChangeCallback()}set(e,t,n,s=this._order){return this._x=e,this._y=t,this._z=n,this._order=s,this._onChangeCallback(),this}clone(){return new this.constructor(this._x,this._y,this._z,this._order)}copy(e){return this._x=e._x,this._y=e._y,this._z=e._z,this._order=e._order,this._onChangeCallback(),this}setFromRotationMatrix(e,t=this._order,n=!0){let s=e.elements,r=s[0],a=s[4],o=s[8],l=s[1],c=s[5],h=s[9],f=s[2],u=s[6],d=s[10];switch(t){case"XYZ":this._y=Math.asin(ot(o,-1,1)),Math.abs(o)<.9999999?(this._x=Math.atan2(-h,d),this._z=Math.atan2(-a,r)):(this._x=Math.atan2(u,c),this._z=0);break;case"YXZ":this._x=Math.asin(-ot(h,-1,1)),Math.abs(h)<.9999999?(this._y=Math.atan2(o,d),this._z=Math.atan2(l,c)):(this._y=Math.atan2(-f,r),this._z=0);break;case"ZXY":this._x=Math.asin(ot(u,-1,1)),Math.abs(u)<.9999999?(this._y=Math.atan2(-f,d),this._z=Math.atan2(-a,c)):(this._y=0,this._z=Math.atan2(l,r));break;case"ZYX":this._y=Math.asin(-ot(f,-1,1)),Math.abs(f)<.9999999?(this._x=Math.atan2(u,d),this._z=Math.atan2(l,r)):(this._x=0,this._z=Math.atan2(-a,c));break;case"YZX":this._z=Math.asin(ot(l,-1,1)),Math.abs(l)<.9999999?(this._x=Math.atan2(-h,c),this._y=Math.atan2(-f,r)):(this._x=0,this._y=Math.atan2(o,d));break;case"XZY":this._z=Math.asin(-ot(a,-1,1)),Math.abs(a)<.9999999?(this._x=Math.atan2(u,c),this._y=Math.atan2(o,r)):(this._x=Math.atan2(-h,d),this._y=0);break;default:$e("Euler: .setFromRotationMatrix() encountered an unknown order: "+t)}return this._order=t,n===!0&&this._onChangeCallback(),this}setFromQuaternion(e,t,n){return Zc.makeRotationFromQuaternion(e),this.setFromRotationMatrix(Zc,t,n)}setFromVector3(e,t=this._order){return this.set(e.x,e.y,e.z,t)}reorder(e){return jc.setFromEuler(this),this.setFromQuaternion(jc,e)}equals(e){return e._x===this._x&&e._y===this._y&&e._z===this._z&&e._order===this._order}fromArray(e){return this._x=e[0],this._y=e[1],this._z=e[2],e[3]!==void 0&&(this._order=e[3]),this._onChangeCallback(),this}toArray(e=[],t=0){return e[t]=this._x,e[t+1]=this._y,e[t+2]=this._z,e[t+3]=this._order,e}_onChange(e){return this._onChangeCallback=e,this}_onChangeCallback(){}*[Symbol.iterator](){yield this._x,yield this._y,yield this._z,yield this._order}};vn.DEFAULT_ORDER="XYZ";var xs=class{constructor(){this.mask=1}set(e){this.mask=(1<<e|0)>>>0}enable(e){this.mask|=1<<e|0}enableAll(){this.mask=-1}toggle(e){this.mask^=1<<e|0}disable(e){this.mask&=~(1<<e|0)}disableAll(){this.mask=0}test(e){return(this.mask&e.mask)!==0}isEnabled(e){return(this.mask&(1<<e|0))!==0}},Ed=0,Jc=new B,Qi=new Ot,Xn=new ut,ia=new B,Gs=new B,wd=new B,Ad=new Ot,Kc=new B(1,0,0),Qc=new B(0,1,0),eu=new B(0,0,1),tu={type:"added"},Cd={type:"removed"},es={type:"childadded",child:null},El={type:"childremoved",child:null},kt=class i extends zn{constructor(){super(),this.isObject3D=!0,Object.defineProperty(this,"id",{value:Ed++}),this.uuid=Ps(),this.name="",this.type="Object3D",this.parent=null,this.children=[],this.up=i.DEFAULT_UP.clone();let e=new B,t=new vn,n=new Ot,s=new B(1,1,1);function r(){n.setFromEuler(t,!1)}function a(){t.setFromQuaternion(n,void 0,!1)}t._onChange(r),n._onChange(a),Object.defineProperties(this,{position:{configurable:!0,enumerable:!0,value:e},rotation:{configurable:!0,enumerable:!0,value:t},quaternion:{configurable:!0,enumerable:!0,value:n},scale:{configurable:!0,enumerable:!0,value:s},modelViewMatrix:{value:new ut},normalMatrix:{value:new Ye}}),this.matrix=new ut,this.matrixWorld=new ut,this.matrixAutoUpdate=i.DEFAULT_MATRIX_AUTO_UPDATE,this.matrixWorldAutoUpdate=i.DEFAULT_MATRIX_WORLD_AUTO_UPDATE,this.matrixWorldNeedsUpdate=!1,this.layers=new xs,this.visible=!0,this.castShadow=!1,this.receiveShadow=!1,this.frustumCulled=!0,this.renderOrder=0,this.animations=[],this.customDepthMaterial=void 0,this.customDistanceMaterial=void 0,this.static=!1,this.userData={},this.pivot=null}onBeforeShadow(){}onAfterShadow(){}onBeforeRender(){}onAfterRender(){}applyMatrix4(e){this.matrixAutoUpdate&&this.updateMatrix(),this.matrix.premultiply(e),this.matrix.decompose(this.position,this.quaternion,this.scale)}applyQuaternion(e){return this.quaternion.premultiply(e),this}setRotationFromAxisAngle(e,t){this.quaternion.setFromAxisAngle(e,t)}setRotationFromEuler(e){this.quaternion.setFromEuler(e,!0)}setRotationFromMatrix(e){this.quaternion.setFromRotationMatrix(e)}setRotationFromQuaternion(e){this.quaternion.copy(e)}rotateOnAxis(e,t){return Qi.setFromAxisAngle(e,t),this.quaternion.multiply(Qi),this}rotateOnWorldAxis(e,t){return Qi.setFromAxisAngle(e,t),this.quaternion.premultiply(Qi),this}rotateX(e){return this.rotateOnAxis(Kc,e)}rotateY(e){return this.rotateOnAxis(Qc,e)}rotateZ(e){return this.rotateOnAxis(eu,e)}translateOnAxis(e,t){return Jc.copy(e).applyQuaternion(this.quaternion),this.position.add(Jc.multiplyScalar(t)),this}translateX(e){return this.translateOnAxis(Kc,e)}translateY(e){return this.translateOnAxis(Qc,e)}translateZ(e){return this.translateOnAxis(eu,e)}localToWorld(e){return this.updateWorldMatrix(!0,!1),e.applyMatrix4(this.matrixWorld)}worldToLocal(e){return this.updateWorldMatrix(!0,!1),e.applyMatrix4(Xn.copy(this.matrixWorld).invert())}lookAt(e,t,n){e.isVector3?ia.copy(e):ia.set(e,t,n);let s=this.parent;this.updateWorldMatrix(!0,!1),Gs.setFromMatrixPosition(this.matrixWorld),this.isCamera||this.isLight?Xn.lookAt(Gs,ia,this.up):Xn.lookAt(ia,Gs,this.up),this.quaternion.setFromRotationMatrix(Xn),s&&(Xn.extractRotation(s.matrixWorld),Qi.setFromRotationMatrix(Xn),this.quaternion.premultiply(Qi.invert()))}add(e){if(arguments.length>1){for(let t=0;t<arguments.length;t++)this.add(arguments[t]);return this}return e===this?(Xe("Object3D.add: object can't be added as a child of itself.",e),this):(e&&e.isObject3D?(e.removeFromParent(),e.parent=this,this.children.push(e),e.dispatchEvent(tu),es.child=e,this.dispatchEvent(es),es.child=null):Xe("Object3D.add: object not an instance of THREE.Object3D.",e),this)}remove(e){if(arguments.length>1){for(let n=0;n<arguments.length;n++)this.remove(arguments[n]);return this}let t=this.children.indexOf(e);return t!==-1&&(e.parent=null,this.children.splice(t,1),e.dispatchEvent(Cd),El.child=e,this.dispatchEvent(El),El.child=null),this}removeFromParent(){let e=this.parent;return e!==null&&e.remove(this),this}clear(){return this.remove(...this.children)}attach(e){return this.updateWorldMatrix(!0,!1),Xn.copy(this.matrixWorld).invert(),e.parent!==null&&(e.parent.updateWorldMatrix(!0,!1),Xn.multiply(e.parent.matrixWorld)),e.applyMatrix4(Xn),e.removeFromParent(),e.parent=this,this.children.push(e),e.updateWorldMatrix(!1,!0),e.dispatchEvent(tu),es.child=e,this.dispatchEvent(es),es.child=null,this}getObjectById(e){return this.getObjectByProperty("id",e)}getObjectByName(e){return this.getObjectByProperty("name",e)}getObjectByProperty(e,t){if(this[e]===t)return this;for(let n=0,s=this.children.length;n<s;n++){let a=this.children[n].getObjectByProperty(e,t);if(a!==void 0)return a}}getObjectsByProperty(e,t,n=[]){this[e]===t&&n.push(this);let s=this.children;for(let r=0,a=s.length;r<a;r++)s[r].getObjectsByProperty(e,t,n);return n}getWorldPosition(e){return this.updateWorldMatrix(!0,!1),e.setFromMatrixPosition(this.matrixWorld)}getWorldQuaternion(e){return this.updateWorldMatrix(!0,!1),this.matrixWorld.decompose(Gs,e,wd),e}getWorldScale(e){return this.updateWorldMatrix(!0,!1),this.matrixWorld.decompose(Gs,Ad,e),e}getWorldDirection(e){this.updateWorldMatrix(!0,!1);let t=this.matrixWorld.elements;return e.set(t[8],t[9],t[10]).normalize()}raycast(){}intersectsFrustum(){}traverse(e){e(this);let t=this.children;for(let n=0,s=t.length;n<s;n++)t[n].traverse(e)}traverseVisible(e){if(this.visible===!1)return;e(this);let t=this.children;for(let n=0,s=t.length;n<s;n++)t[n].traverseVisible(e)}traverseAncestors(e){let t=this.parent;t!==null&&(e(t),t.traverseAncestors(e))}updateMatrix(){this.matrix.compose(this.position,this.quaternion,this.scale);let e=this.pivot;if(e!==null){let t=e.x,n=e.y,s=e.z,r=this.matrix.elements;r[12]+=t-r[0]*t-r[4]*n-r[8]*s,r[13]+=n-r[1]*t-r[5]*n-r[9]*s,r[14]+=s-r[2]*t-r[6]*n-r[10]*s}this.matrixWorldNeedsUpdate=!0}updateMatrixWorld(e){this.matrixAutoUpdate&&this.updateMatrix(),(this.matrixWorldNeedsUpdate||e)&&(this.matrixWorldAutoUpdate===!0&&(this.parent===null?this.matrixWorld.copy(this.matrix):this.matrixWorld.multiplyMatrices(this.parent.matrixWorld,this.matrix)),this.matrixWorldNeedsUpdate=!1,e=!0);let t=this.children;for(let n=0,s=t.length;n<s;n++)t[n].updateMatrixWorld(e)}updateWorldMatrix(e,t,n=!1){let s=this.parent;if(e===!0&&s!==null&&s.updateWorldMatrix(!0,!1),this.matrixAutoUpdate&&this.updateMatrix(),(this.matrixWorldNeedsUpdate||n)&&(this.matrixWorldAutoUpdate===!0&&(this.parent===null?this.matrixWorld.copy(this.matrix):this.matrixWorld.multiplyMatrices(this.parent.matrixWorld,this.matrix)),this.matrixWorldNeedsUpdate=!1,n=!0),t===!0){let r=this.children;for(let a=0,o=r.length;a<o;a++)r[a].updateWorldMatrix(!1,!0,n)}}toJSON(e){let t=e===void 0||typeof e=="string",n={};t&&(e={geometries:{},materials:{},textures:{},images:{},shapes:{},skeletons:{},animations:{},nodes:{}},n.metadata={version:4.7,type:"Object",generator:"Object3D.toJSON"});let s={};s.uuid=this.uuid,s.type=this.type,s.name=this.name,s.castShadow=this.castShadow,s.receiveShadow=this.receiveShadow,s.visible=this.visible,s.frustumCulled=this.frustumCulled,s.renderOrder=this.renderOrder,s.static=this.static,s.matrixAutoUpdate=this.matrixAutoUpdate,Object.keys(this.userData).length>0&&(s.userData=this.userData),s.layers=this.layers.mask,s.matrix=this.matrix.toArray(),s.up=this.up.toArray(),this.pivot!==null&&(s.pivot=this.pivot.toArray()),this.morphTargetDictionary!==void 0&&(s.morphTargetDictionary=Object.assign({},this.morphTargetDictionary)),this.morphTargetInfluences!==void 0&&(s.morphTargetInfluences=this.morphTargetInfluences.slice()),this.isInstancedMesh&&(s.type="InstancedMesh",s.count=this.count,s.instanceMatrix=this.instanceMatrix.toJSON(),this.instanceColor!==null&&(s.instanceColor=this.instanceColor.toJSON())),this.isBatchedMesh&&(s.type="BatchedMesh",s.perObjectFrustumCulled=this.perObjectFrustumCulled,s.sortObjects=this.sortObjects,s.drawRanges=this._drawRanges,s.reservedRanges=this._reservedRanges,s.geometryInfo=this._geometryInfo.map(o=>({...o,boundingBox:o.boundingBox?o.boundingBox.toJSON():void 0,boundingSphere:o.boundingSphere?o.boundingSphere.toJSON():void 0})),s.instanceInfo=this._instanceInfo.map(o=>({...o})),s.availableInstanceIds=this._availableInstanceIds.slice(),s.availableGeometryIds=this._availableGeometryIds.slice(),s.nextIndexStart=this._nextIndexStart,s.nextVertexStart=this._nextVertexStart,s.geometryCount=this._geometryCount,s.maxInstanceCount=this._maxInstanceCount,s.maxVertexCount=this._maxVertexCount,s.maxIndexCount=this._maxIndexCount,s.geometryInitialized=this._geometryInitialized,s.matricesTexture=this._matricesTexture.toJSON(e),s.indirectTexture=this._indirectTexture.toJSON(e),this._colorsTexture!==null&&(s.colorsTexture=this._colorsTexture.toJSON(e)),this.boundingSphere!==null&&(s.boundingSphere=this.boundingSphere.toJSON()),this.boundingBox!==null&&(s.boundingBox=this.boundingBox.toJSON()));function r(o,l){return o[l.uuid]===void 0&&(o[l.uuid]=l.toJSON(e)),l.uuid}if(this.isScene)this.background&&(this.background.isColor?s.background=this.background.toJSON():this.background.isTexture&&(s.background=this.background.toJSON(e).uuid)),this.environment&&this.environment.isTexture&&this.environment.isRenderTargetTexture!==!0&&(s.environment=this.environment.toJSON(e).uuid);else if(this.isMesh||this.isLine||this.isPoints){s.geometry=r(e.geometries,this.geometry);let o=this.geometry.parameters;if(o!==void 0&&o.shapes!==void 0){let l=o.shapes;if(Array.isArray(l))for(let c=0,h=l.length;c<h;c++){let f=l[c];r(e.shapes,f)}else r(e.shapes,l)}}if(this.isSkinnedMesh&&(s.bindMode=this.bindMode,s.bindMatrix=this.bindMatrix.toArray(),this.skeleton!==void 0&&(r(e.skeletons,this.skeleton),s.skeleton=this.skeleton.uuid)),this.material!==void 0)if(Array.isArray(this.material)){let o=[];for(let l=0,c=this.material.length;l<c;l++)o.push(r(e.materials,this.material[l]));s.material=o}else s.material=r(e.materials,this.material);if(this.children.length>0){s.children=[];for(let o=0;o<this.children.length;o++)s.children.push(this.children[o].toJSON(e).object)}if(this.animations.length>0){s.animations=[];for(let o=0;o<this.animations.length;o++){let l=this.animations[o];s.animations.push(r(e.animations,l))}}if(t){let o=a(e.geometries),l=a(e.materials),c=a(e.textures),h=a(e.images),f=a(e.shapes),u=a(e.skeletons),d=a(e.animations),_=a(e.nodes);o.length>0&&(n.geometries=o),l.length>0&&(n.materials=l),c.length>0&&(n.textures=c),h.length>0&&(n.images=h),f.length>0&&(n.shapes=f),u.length>0&&(n.skeletons=u),d.length>0&&(n.animations=d),_.length>0&&(n.nodes=_)}return n.object=s,n;function a(o){let l=[];for(let c in o){let h=o[c];delete h.metadata,l.push(h)}return l}}clone(e){return new this.constructor().copy(this,e)}copy(e,t=!0){if(this.name=e.name,this.up.copy(e.up),this.position.copy(e.position),this.rotation.order=e.rotation.order,this.quaternion.copy(e.quaternion),this.scale.copy(e.scale),this.pivot=e.pivot!==null?e.pivot.clone():null,this.matrix.copy(e.matrix),this.matrixWorld.copy(e.matrixWorld),this.matrixAutoUpdate=e.matrixAutoUpdate,this.matrixWorldAutoUpdate=e.matrixWorldAutoUpdate,this.matrixWorldNeedsUpdate=e.matrixWorldNeedsUpdate,this.layers.mask=e.layers.mask,this.visible=e.visible,this.castShadow=e.castShadow,this.receiveShadow=e.receiveShadow,this.frustumCulled=e.frustumCulled,this.renderOrder=e.renderOrder,this.static=e.static,this.animations=e.animations.slice(),this.userData=JSON.parse(JSON.stringify(e.userData)),t===!0)for(let n=0;n<e.children.length;n++){let s=e.children[n];this.add(s.clone())}return this}dispose(){this.dispatchEvent({type:"dispose"})}};kt.DEFAULT_UP=new B(0,1,0);kt.DEFAULT_MATRIX_AUTO_UPDATE=!0;kt.DEFAULT_MATRIX_WORLD_AUTO_UPDATE=!0;var Ut=class extends kt{constructor(){super(),this.isGroup=!0,this.type="Group"}},Rd={type:"move"},vs=class{constructor(){this._targetRay=null,this._grip=null,this._hand=null}getHandSpace(){return this._hand===null&&(this._hand=new Ut,this._hand.matrixAutoUpdate=!1,this._hand.visible=!1,this._hand.joints={},this._hand.inputState={pinching:!1}),this._hand}getTargetRaySpace(){return this._targetRay===null&&(this._targetRay=new Ut,this._targetRay.matrixAutoUpdate=!1,this._targetRay.visible=!1,this._targetRay.hasLinearVelocity=!1,this._targetRay.linearVelocity=new B,this._targetRay.hasAngularVelocity=!1,this._targetRay.angularVelocity=new B),this._targetRay}getGripSpace(){return this._grip===null&&(this._grip=new Ut,this._grip.matrixAutoUpdate=!1,this._grip.visible=!1,this._grip.hasLinearVelocity=!1,this._grip.linearVelocity=new B,this._grip.hasAngularVelocity=!1,this._grip.angularVelocity=new B,this._grip.eventsEnabled=!1),this._grip}dispatchEvent(e){return this._targetRay!==null&&this._targetRay.dispatchEvent(e),this._grip!==null&&this._grip.dispatchEvent(e),this._hand!==null&&this._hand.dispatchEvent(e),this}connect(e){if(e&&e.hand){let t=this._hand;if(t)for(let n of e.hand.values())this._getHandJoint(t,n)}return this.dispatchEvent({type:"connected",data:e}),this}disconnect(e){return this.dispatchEvent({type:"disconnected",data:e}),this._targetRay!==null&&(this._targetRay.visible=!1),this._grip!==null&&(this._grip.visible=!1),this._hand!==null&&(this._hand.visible=!1),this}update(e,t,n){let s=null,r=null,a=null,o=this._targetRay,l=this._grip,c=this._hand;if(e&&t.session.visibilityState!=="visible-blurred"){if(c&&e.hand){a=!0;for(let S of e.hand.values()){let g=t.getJointPose(S,n),p=this._getHandJoint(c,S);g!==null&&(p.matrix.fromArray(g.transform.matrix),p.matrix.decompose(p.position,p.rotation,p.scale),p.matrixWorldNeedsUpdate=!0,p.jointRadius=g.radius),p.visible=g!==null}let h=c.joints["index-finger-tip"],f=c.joints["thumb-tip"],u=h.position.distanceTo(f.position),d=.02,_=.005;c.inputState.pinching&&u>d+_?(c.inputState.pinching=!1,this.dispatchEvent({type:"pinchend",handedness:e.handedness,target:this})):!c.inputState.pinching&&u<=d-_&&(c.inputState.pinching=!0,this.dispatchEvent({type:"pinchstart",handedness:e.handedness,target:this}))}else l!==null&&e.gripSpace&&(r=t.getPose(e.gripSpace,n),r!==null&&(l.matrix.fromArray(r.transform.matrix),l.matrix.decompose(l.position,l.rotation,l.scale),l.matrixWorldNeedsUpdate=!0,r.linearVelocity?(l.hasLinearVelocity=!0,l.linearVelocity.copy(r.linearVelocity)):l.hasLinearVelocity=!1,r.angularVelocity?(l.hasAngularVelocity=!0,l.angularVelocity.copy(r.angularVelocity)):l.hasAngularVelocity=!1,l.eventsEnabled&&l.dispatchEvent({type:"gripUpdated",data:e,target:this})));o!==null&&(s=t.getPose(e.targetRaySpace,n),s===null&&r!==null&&(s=r),s!==null&&(o.matrix.fromArray(s.transform.matrix),o.matrix.decompose(o.position,o.rotation,o.scale),o.matrixWorldNeedsUpdate=!0,s.linearVelocity?(o.hasLinearVelocity=!0,o.linearVelocity.copy(s.linearVelocity)):o.hasLinearVelocity=!1,s.angularVelocity?(o.hasAngularVelocity=!0,o.angularVelocity.copy(s.angularVelocity)):o.hasAngularVelocity=!1,this.dispatchEvent(Rd)))}return o!==null&&(o.visible=s!==null),l!==null&&(l.visible=r!==null),c!==null&&(c.visible=a!==null),this}_getHandJoint(e,t){if(e.joints[t.jointName]===void 0){let n=new Ut;n.matrixAutoUpdate=!1,n.visible=!1,e.joints[t.jointName]=n,e.add(n)}return e.joints[t.jointName]}},oh={aliceblue:15792383,antiquewhite:16444375,aqua:65535,aquamarine:8388564,azure:15794175,beige:16119260,bisque:16770244,black:0,blanchedalmond:16772045,blue:255,blueviolet:9055202,brown:10824234,burlywood:14596231,cadetblue:6266528,chartreuse:8388352,chocolate:13789470,coral:16744272,cornflowerblue:6591981,cornsilk:16775388,crimson:14423100,cyan:65535,darkblue:139,darkcyan:35723,darkgoldenrod:12092939,darkgray:11119017,darkgreen:25600,darkgrey:11119017,darkkhaki:12433259,darkmagenta:9109643,darkolivegreen:5597999,darkorange:16747520,darkorchid:10040012,darkred:9109504,darksalmon:15308410,darkseagreen:9419919,darkslateblue:4734347,darkslategray:3100495,darkslategrey:3100495,darkturquoise:52945,darkviolet:9699539,deeppink:16716947,deepskyblue:49151,dimgray:6908265,dimgrey:6908265,dodgerblue:2003199,firebrick:11674146,floralwhite:16775920,forestgreen:2263842,fuchsia:16711935,gainsboro:14474460,ghostwhite:16316671,gold:16766720,goldenrod:14329120,gray:8421504,green:32768,greenyellow:11403055,grey:8421504,honeydew:15794160,hotpink:16738740,indianred:13458524,indigo:4915330,ivory:16777200,khaki:15787660,lavender:15132410,lavenderblush:16773365,lawngreen:8190976,lemonchiffon:16775885,lightblue:11393254,lightcoral:15761536,lightcyan:14745599,lightgoldenrodyellow:16448210,lightgray:13882323,lightgreen:9498256,lightgrey:13882323,lightpink:16758465,lightsalmon:16752762,lightseagreen:2142890,lightskyblue:8900346,lightslategray:7833753,lightslategrey:7833753,lightsteelblue:11584734,lightyellow:16777184,lime:65280,limegreen:3329330,linen:16445670,magenta:16711935,maroon:8388608,mediumaquamarine:6737322,mediumblue:205,mediumorchid:12211667,mediumpurple:9662683,mediumseagreen:3978097,mediumslateblue:8087790,mediumspringgreen:64154,mediumturquoise:4772300,mediumvioletred:13047173,midnightblue:1644912,mintcream:16121850,mistyrose:16770273,moccasin:16770229,navajowhite:16768685,navy:128,oldlace:16643558,olive:8421376,olivedrab:7048739,orange:16753920,orangered:16729344,orchid:14315734,palegoldenrod:15657130,palegreen:10025880,paleturquoise:11529966,palevioletred:14381203,papayawhip:16773077,peachpuff:16767673,peru:13468991,pink:16761035,plum:14524637,powderblue:11591910,purple:8388736,rebeccapurple:6697881,red:16711680,rosybrown:12357519,royalblue:4286945,saddlebrown:9127187,salmon:16416882,sandybrown:16032864,seagreen:3050327,seashell:16774638,sienna:10506797,silver:12632256,skyblue:8900331,slateblue:6970061,slategray:7372944,slategrey:7372944,snow:16775930,springgreen:65407,steelblue:4620980,tan:13808780,teal:32896,thistle:14204888,tomato:16737095,turquoise:4251856,violet:15631086,wheat:16113331,white:16777215,whitesmoke:16119285,yellow:16776960,yellowgreen:10145074},ui={h:0,s:0,l:0},sa={h:0,s:0,l:0};function wl(i,e,t){return t<0&&(t+=1),t>1&&(t-=1),t<1/6?i+(e-i)*6*t:t<1/2?e:t<2/3?i+(e-i)*6*(2/3-t):i}var qe=class{constructor(e,t,n){return this.isColor=!0,this.r=1,this.g=1,this.b=1,this.set(e,t,n)}set(e,t,n){if(t===void 0&&n===void 0){let s=e;s&&s.isColor?this.copy(s):typeof s=="number"?this.setHex(s):typeof s=="string"&&this.setStyle(s)}else this.setRGB(e,t,n);return this}setScalar(e){return this.r=e,this.g=e,this.b=e,this}setHex(e,t=nn){return e=Math.floor(e),this.r=(e>>16&255)/255,this.g=(e>>8&255)/255,this.b=(e&255)/255,at.colorSpaceToWorking(this,t),this}setRGB(e,t,n,s=at.workingColorSpace){return this.r=e,this.g=t,this.b=n,at.colorSpaceToWorking(this,s),this}setHSL(e,t,n,s=at.workingColorSpace){if(e=_c(e,1),t=ot(t,0,1),n=ot(n,0,1),t===0)this.r=this.g=this.b=n;else{let r=n<=.5?n*(1+t):n+t-n*t,a=2*n-r;this.r=wl(a,r,e+1/3),this.g=wl(a,r,e),this.b=wl(a,r,e-1/3)}return at.colorSpaceToWorking(this,s),this}setStyle(e,t=nn){function n(r){r!==void 0&&parseFloat(r)<1&&$e("Color: Alpha component of "+e+" will be ignored.")}let s;if(s=/^(\w+)\(([^\)]*)\)/.exec(e)){let r,a=s[1],o=s[2];switch(a){case"rgb":case"rgba":if(r=/^\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(o))return n(r[4]),this.setRGB(Math.min(255,parseInt(r[1],10))/255,Math.min(255,parseInt(r[2],10))/255,Math.min(255,parseInt(r[3],10))/255,t);if(r=/^\s*(\d+)\%\s*,\s*(\d+)\%\s*,\s*(\d+)\%\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(o))return n(r[4]),this.setRGB(Math.min(100,parseInt(r[1],10))/100,Math.min(100,parseInt(r[2],10))/100,Math.min(100,parseInt(r[3],10))/100,t);break;case"hsl":case"hsla":if(r=/^\s*(\d*\.?\d+)\s*,\s*(\d*\.?\d+)\%\s*,\s*(\d*\.?\d+)\%\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(o))return n(r[4]),this.setHSL(parseFloat(r[1])/360,parseFloat(r[2])/100,parseFloat(r[3])/100,t);break;default:$e("Color: Unknown color model "+e)}}else if(s=/^\#([A-Fa-f\d]+)$/.exec(e)){let r=s[1],a=r.length;if(a===3)return this.setRGB(parseInt(r.charAt(0),16)/15,parseInt(r.charAt(1),16)/15,parseInt(r.charAt(2),16)/15,t);if(a===6)return this.setHex(parseInt(r,16),t);$e("Color: Invalid hex color "+e)}else if(e&&e.length>0)return this.setColorName(e,t);return this}setColorName(e,t=nn){let n=oh[e.toLowerCase()];return n!==void 0?this.setHex(n,t):$e("Color: Unknown color "+e),this}clone(){return new this.constructor(this.r,this.g,this.b)}copy(e){return this.r=e.r,this.g=e.g,this.b=e.b,this}copySRGBToLinear(e){return this.r=Kn(e.r),this.g=Kn(e.g),this.b=Kn(e.b),this}copyLinearToSRGB(e){return this.r=ds(e.r),this.g=ds(e.g),this.b=ds(e.b),this}convertSRGBToLinear(){return this.copySRGBToLinear(this),this}convertLinearToSRGB(){return this.copyLinearToSRGB(this),this}getHex(e=nn){return at.workingToColorSpace(Kt.copy(this),e),Math.round(ot(Kt.r*255,0,255))*65536+Math.round(ot(Kt.g*255,0,255))*256+Math.round(ot(Kt.b*255,0,255))}getHexString(e=nn){return("000000"+this.getHex(e).toString(16)).slice(-6)}getHSL(e,t=at.workingColorSpace){at.workingToColorSpace(Kt.copy(this),t);let n=Kt.r,s=Kt.g,r=Kt.b,a=Math.max(n,s,r),o=Math.min(n,s,r),l,c,h=(o+a)/2;if(o===a)l=0,c=0;else{let f=a-o;switch(c=h<=.5?f/(a+o):f/(2-a-o),a){case n:l=(s-r)/f+(s<r?6:0);break;case s:l=(r-n)/f+2;break;case r:l=(n-s)/f+4;break}l/=6}return e.h=l,e.s=c,e.l=h,e}getRGB(e,t=at.workingColorSpace){return at.workingToColorSpace(Kt.copy(this),t),e.r=Kt.r,e.g=Kt.g,e.b=Kt.b,e}getStyle(e=nn){at.workingToColorSpace(Kt.copy(this),e);let t=Kt.r,n=Kt.g,s=Kt.b;return e!==nn?`color(${e} ${t.toFixed(3)} ${n.toFixed(3)} ${s.toFixed(3)})`:`rgb(${Math.round(t*255)},${Math.round(n*255)},${Math.round(s*255)})`}offsetHSL(e,t,n){return this.getHSL(ui),this.setHSL(ui.h+e,ui.s+t,ui.l+n)}add(e){return this.r+=e.r,this.g+=e.g,this.b+=e.b,this}addColors(e,t){return this.r=e.r+t.r,this.g=e.g+t.g,this.b=e.b+t.b,this}addScalar(e){return this.r+=e,this.g+=e,this.b+=e,this}sub(e){return this.r=Math.max(0,this.r-e.r),this.g=Math.max(0,this.g-e.g),this.b=Math.max(0,this.b-e.b),this}multiply(e){return this.r*=e.r,this.g*=e.g,this.b*=e.b,this}multiplyScalar(e){return this.r*=e,this.g*=e,this.b*=e,this}lerp(e,t){return this.r+=(e.r-this.r)*t,this.g+=(e.g-this.g)*t,this.b+=(e.b-this.b)*t,this}lerpColors(e,t,n){return this.r=e.r+(t.r-e.r)*n,this.g=e.g+(t.g-e.g)*n,this.b=e.b+(t.b-e.b)*n,this}lerpHSL(e,t){this.getHSL(ui),e.getHSL(sa);let n=Js(ui.h,sa.h,t),s=Js(ui.s,sa.s,t),r=Js(ui.l,sa.l,t);return this.setHSL(n,s,r),this}setFromVector3(e){return this.r=e.x,this.g=e.y,this.b=e.z,this}applyMatrix3(e){let t=this.r,n=this.g,s=this.b,r=e.elements;return this.r=r[0]*t+r[3]*n+r[6]*s,this.g=r[1]*t+r[4]*n+r[7]*s,this.b=r[2]*t+r[5]*n+r[8]*s,this}equals(e){return e.r===this.r&&e.g===this.g&&e.b===this.b}fromArray(e,t=0){return this.r=e[t],this.g=e[t+1],this.b=e[t+2],this}toArray(e=[],t=0){return e[t]=this.r,e[t+1]=this.g,e[t+2]=this.b,e}fromBufferAttribute(e,t){return this.r=e.getX(t),this.g=e.getY(t),this.b=e.getZ(t),this}toJSON(){return this.getHex()}*[Symbol.iterator](){yield this.r,yield this.g,yield this.b}},Kt=new qe;qe.NAMES=oh;var rr=class i{constructor(e,t=25e-5){this.isFogExp2=!0,this.name="",this.color=new qe(e),this.density=t}clone(){return new i(this.color,this.density)}toJSON(){return{type:"FogExp2",name:this.name,color:this.color.getHex(),density:this.density}}};var Di=class extends kt{constructor(){super(),this.isScene=!0,this.type="Scene",this.background=null,this.environment=null,this.fog=null,this.backgroundBlurriness=0,this.backgroundIntensity=1,this.backgroundRotation=new vn,this.environmentIntensity=1,this.environmentRotation=new vn,this.overrideMaterial=null,typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("observe",{detail:this}))}copy(e,t){return super.copy(e,t),e.background!==null&&(this.background=e.background.clone()),e.environment!==null&&(this.environment=e.environment.clone()),e.fog!==null&&(this.fog=e.fog.clone()),this.backgroundBlurriness=e.backgroundBlurriness,this.backgroundIntensity=e.backgroundIntensity,this.backgroundRotation.copy(e.backgroundRotation),this.environmentIntensity=e.environmentIntensity,this.environmentRotation.copy(e.environmentRotation),e.overrideMaterial!==null&&(this.overrideMaterial=e.overrideMaterial.clone()),this.matrixAutoUpdate=e.matrixAutoUpdate,this}toJSON(e){let t=super.toJSON(e);return this.fog!==null&&(t.object.fog=this.fog.toJSON()),t.object.backgroundBlurriness=this.backgroundBlurriness,t.object.backgroundIntensity=this.backgroundIntensity,t.object.backgroundRotation=this.backgroundRotation.toArray(),t.object.environmentIntensity=this.environmentIntensity,t.object.environmentRotation=this.environmentRotation.toArray(),t}},Cn=new B,Yn=new B,Al=new B,Zn=new B,ts=new B,ns=new B,nu=new B,Cl=new B,Rl=new B,Il=new B,Pl=new It,Ll=new It,Nl=new It,pi=class i{constructor(e=new B,t=new B,n=new B){this.a=e,this.b=t,this.c=n}static getNormal(e,t,n,s){s.subVectors(n,t),Cn.subVectors(e,t),s.cross(Cn);let r=s.lengthSq();return r>0?s.multiplyScalar(1/Math.sqrt(r)):s.set(0,0,0)}static getBarycoord(e,t,n,s,r){Cn.subVectors(s,t),Yn.subVectors(n,t),Al.subVectors(e,t);let a=Cn.dot(Cn),o=Cn.dot(Yn),l=Cn.dot(Al),c=Yn.dot(Yn),h=Yn.dot(Al),f=a*c-o*o;if(f===0)return r.set(0,0,0),null;let u=1/f,d=(c*l-o*h)*u,_=(a*h-o*l)*u;return r.set(1-d-_,_,d)}static containsPoint(e,t,n,s){return this.getBarycoord(e,t,n,s,Zn)===null?!1:Zn.x>=0&&Zn.y>=0&&Zn.x+Zn.y<=1}static getInterpolation(e,t,n,s,r,a,o,l){return this.getBarycoord(e,t,n,s,Zn)===null?(l.x=0,l.y=0,"z"in l&&(l.z=0),"w"in l&&(l.w=0),null):(l.setScalar(0),l.addScaledVector(r,Zn.x),l.addScaledVector(a,Zn.y),l.addScaledVector(o,Zn.z),l)}static getInterpolatedAttribute(e,t,n,s,r,a){return Pl.setScalar(0),Ll.setScalar(0),Nl.setScalar(0),Pl.fromBufferAttribute(e,t),Ll.fromBufferAttribute(e,n),Nl.fromBufferAttribute(e,s),a.setScalar(0),a.addScaledVector(Pl,r.x),a.addScaledVector(Ll,r.y),a.addScaledVector(Nl,r.z),a}static isFrontFacing(e,t,n,s){return Cn.subVectors(n,t),Yn.subVectors(e,t),Cn.cross(Yn).dot(s)<0}set(e,t,n){return this.a.copy(e),this.b.copy(t),this.c.copy(n),this}setFromPointsAndIndices(e,t,n,s){return this.a.copy(e[t]),this.b.copy(e[n]),this.c.copy(e[s]),this}setFromAttributeAndIndices(e,t,n,s){return this.a.fromBufferAttribute(e,t),this.b.fromBufferAttribute(e,n),this.c.fromBufferAttribute(e,s),this}clone(){return new this.constructor().copy(this)}copy(e){return this.a.copy(e.a),this.b.copy(e.b),this.c.copy(e.c),this}getArea(){return Cn.subVectors(this.c,this.b),Yn.subVectors(this.a,this.b),Cn.cross(Yn).length()*.5}getMidpoint(e){return e.addVectors(this.a,this.b).add(this.c).multiplyScalar(1/3)}getNormal(e){return i.getNormal(this.a,this.b,this.c,e)}getPlane(e){return e.setFromCoplanarPoints(this.a,this.b,this.c)}getBarycoord(e,t){return i.getBarycoord(e,this.a,this.b,this.c,t)}getInterpolation(e,t,n,s,r){return i.getInterpolation(e,this.a,this.b,this.c,t,n,s,r)}containsPoint(e){return i.containsPoint(e,this.a,this.b,this.c)}isFrontFacing(e){return i.isFrontFacing(this.a,this.b,this.c,e)}intersectsBox(e){return e.intersectsTriangle(this)}closestPointToPoint(e,t){let n=this.a,s=this.b,r=this.c,a,o;ts.subVectors(s,n),ns.subVectors(r,n),Cl.subVectors(e,n);let l=ts.dot(Cl),c=ns.dot(Cl);if(l<=0&&c<=0)return t.copy(n);Rl.subVectors(e,s);let h=ts.dot(Rl),f=ns.dot(Rl);if(h>=0&&f<=h)return t.copy(s);let u=l*f-h*c;if(u<=0&&l>=0&&h<=0)return a=l/(l-h),t.copy(n).addScaledVector(ts,a);Il.subVectors(e,r);let d=ts.dot(Il),_=ns.dot(Il);if(_>=0&&d<=_)return t.copy(r);let S=d*c-l*_;if(S<=0&&c>=0&&_<=0)return o=c/(c-_),t.copy(n).addScaledVector(ns,o);let g=h*_-d*f;if(g<=0&&f-h>=0&&d-_>=0)return nu.subVectors(r,s),o=(f-h)/(f-h+(d-_)),t.copy(s).addScaledVector(nu,o);let p=1/(g+S+u);return a=S*p,o=u*p,t.copy(n).addScaledVector(ts,a).addScaledVector(ns,o)}equals(e){return e.a.equals(this.a)&&e.b.equals(this.b)&&e.c.equals(this.c)}},Vn=class{constructor(e=new B(1/0,1/0,1/0),t=new B(-1/0,-1/0,-1/0)){this.isBox3=!0,this.min=e,this.max=t}set(e,t){return this.min.copy(e),this.max.copy(t),this}setFromArray(e){this.makeEmpty();for(let t=0,n=e.length;t<n;t+=3)this.expandByPoint(Rn.fromArray(e,t));return this}setFromBufferAttribute(e){this.makeEmpty();for(let t=0,n=e.count;t<n;t++)this.expandByPoint(Rn.fromBufferAttribute(e,t));return this}setFromPoints(e){this.makeEmpty();for(let t=0,n=e.length;t<n;t++)this.expandByPoint(e[t]);return this}setFromCenterAndSize(e,t){let n=Rn.copy(t).multiplyScalar(.5);return this.min.copy(e).sub(n),this.max.copy(e).add(n),this}setFromObject(e,t=!1){return this.makeEmpty(),this.expandByObject(e,t)}clone(){return new this.constructor().copy(this)}copy(e){return this.min.copy(e.min),this.max.copy(e.max),this}makeEmpty(){return this.min.x=this.min.y=this.min.z=1/0,this.max.x=this.max.y=this.max.z=-1/0,this}isEmpty(){return this.max.x<this.min.x||this.max.y<this.min.y||this.max.z<this.min.z}getCenter(e){return this.isEmpty()?e.set(0,0,0):e.addVectors(this.min,this.max).multiplyScalar(.5)}getSize(e){return this.isEmpty()?e.set(0,0,0):e.subVectors(this.max,this.min)}expandByPoint(e){return this.min.min(e),this.max.max(e),this}expandByVector(e){return this.min.sub(e),this.max.add(e),this}expandByScalar(e){return this.min.addScalar(-e),this.max.addScalar(e),this}expandByObject(e,t=!1){e.updateWorldMatrix(!1,!1);let n=e.geometry;if(n!==void 0){let r=n.getAttribute("position");if(t===!0&&r!==void 0&&e.isInstancedMesh!==!0)for(let a=0,o=r.count;a<o;a++)e.isMesh===!0?e.getVertexPosition(a,Rn):Rn.fromBufferAttribute(r,a),Rn.applyMatrix4(e.matrixWorld),this.expandByPoint(Rn);else e.boundingBox!==void 0?(e.boundingBox===null&&e.computeBoundingBox(),ra.copy(e.boundingBox)):(n.boundingBox===null&&n.computeBoundingBox(),ra.copy(n.boundingBox)),ra.applyMatrix4(e.matrixWorld),this.union(ra)}let s=e.children;for(let r=0,a=s.length;r<a;r++)this.expandByObject(s[r],t);return this}containsPoint(e){return e.x>=this.min.x&&e.x<=this.max.x&&e.y>=this.min.y&&e.y<=this.max.y&&e.z>=this.min.z&&e.z<=this.max.z}containsBox(e){return this.min.x<=e.min.x&&e.max.x<=this.max.x&&this.min.y<=e.min.y&&e.max.y<=this.max.y&&this.min.z<=e.min.z&&e.max.z<=this.max.z}getParameter(e,t){return t.set((e.x-this.min.x)/(this.max.x-this.min.x),(e.y-this.min.y)/(this.max.y-this.min.y),(e.z-this.min.z)/(this.max.z-this.min.z))}intersectsBox(e){return e.max.x>=this.min.x&&e.min.x<=this.max.x&&e.max.y>=this.min.y&&e.min.y<=this.max.y&&e.max.z>=this.min.z&&e.min.z<=this.max.z}intersectsSphere(e){return this.clampPoint(e.center,Rn),Rn.distanceToSquared(e.center)<=e.radius*e.radius}intersectsPlane(e){let t,n;return e.normal.x>0?(t=e.normal.x*this.min.x,n=e.normal.x*this.max.x):(t=e.normal.x*this.max.x,n=e.normal.x*this.min.x),e.normal.y>0?(t+=e.normal.y*this.min.y,n+=e.normal.y*this.max.y):(t+=e.normal.y*this.max.y,n+=e.normal.y*this.min.y),e.normal.z>0?(t+=e.normal.z*this.min.z,n+=e.normal.z*this.max.z):(t+=e.normal.z*this.max.z,n+=e.normal.z*this.min.z),t<=-e.constant&&n>=-e.constant}intersectsTriangle(e){if(this.isEmpty())return!1;this.getCenter(Ws),aa.subVectors(this.max,Ws),is.subVectors(e.a,Ws),ss.subVectors(e.b,Ws),rs.subVectors(e.c,Ws),hi.subVectors(ss,is),di.subVectors(rs,ss),Ri.subVectors(is,rs);let t=[0,-hi.z,hi.y,0,-di.z,di.y,0,-Ri.z,Ri.y,hi.z,0,-hi.x,di.z,0,-di.x,Ri.z,0,-Ri.x,-hi.y,hi.x,0,-di.y,di.x,0,-Ri.y,Ri.x,0];return!Dl(t,is,ss,rs,aa)||(t=[1,0,0,0,1,0,0,0,1],!Dl(t,is,ss,rs,aa))?!1:(oa.crossVectors(hi,di),t=[oa.x,oa.y,oa.z],Dl(t,is,ss,rs,aa))}clampPoint(e,t){return t.copy(e).clamp(this.min,this.max)}distanceToPoint(e){return this.clampPoint(e,Rn).distanceTo(e)}getBoundingSphere(e){return this.isEmpty()?e.makeEmpty():(this.getCenter(e.center),e.radius=this.getSize(Rn).length()*.5),e}intersect(e){return this.min.max(e.min),this.max.min(e.max),this.isEmpty()&&this.makeEmpty(),this}union(e){return this.min.min(e.min),this.max.max(e.max),this}applyMatrix4(e){return this.isEmpty()?this:(jn[0].set(this.min.x,this.min.y,this.min.z).applyMatrix4(e),jn[1].set(this.min.x,this.min.y,this.max.z).applyMatrix4(e),jn[2].set(this.min.x,this.max.y,this.min.z).applyMatrix4(e),jn[3].set(this.min.x,this.max.y,this.max.z).applyMatrix4(e),jn[4].set(this.max.x,this.min.y,this.min.z).applyMatrix4(e),jn[5].set(this.max.x,this.min.y,this.max.z).applyMatrix4(e),jn[6].set(this.max.x,this.max.y,this.min.z).applyMatrix4(e),jn[7].set(this.max.x,this.max.y,this.max.z).applyMatrix4(e),this.setFromPoints(jn),this)}translate(e){return this.min.add(e),this.max.add(e),this}equals(e){return e.min.equals(this.min)&&e.max.equals(this.max)}toJSON(){return{min:this.min.toArray(),max:this.max.toArray()}}fromJSON(e){return this.min.fromArray(e.min),this.max.fromArray(e.max),this}},jn=[new B,new B,new B,new B,new B,new B,new B,new B],Rn=new B,ra=new Vn,is=new B,ss=new B,rs=new B,hi=new B,di=new B,Ri=new B,Ws=new B,aa=new B,oa=new B,Ii=new B;function Dl(i,e,t,n,s){for(let r=0,a=i.length-3;r<=a;r+=3){Ii.fromArray(i,r);let o=s.x*Math.abs(Ii.x)+s.y*Math.abs(Ii.y)+s.z*Math.abs(Ii.z),l=e.dot(Ii),c=t.dot(Ii),h=n.dot(Ii);if(Math.max(-Math.max(l,c,h),Math.min(l,c,h))>o)return!1}return!0}var Dt=new B,la=new De,Id=0,Xt=class extends zn{constructor(e,t,n=!1){if(super(),Array.isArray(e))throw new TypeError("THREE.BufferAttribute: array should be a Typed Array.");this.isBufferAttribute=!0,Object.defineProperty(this,"id",{value:Id++}),this.name="",this.array=e,this.itemSize=t,this.count=e!==void 0?e.length/t:0,this.normalized=n,this.usage=nh,this.updateRanges=[],this.gpuType=Sn,this.version=0}onUploadCallback(){}set needsUpdate(e){e===!0&&this.version++}setUsage(e){return this.usage=e,this}addUpdateRange(e,t){this.updateRanges.push({start:e,count:t})}clearUpdateRanges(){this.updateRanges.length=0}copy(e){return this.name=e.name,this.array=new e.array.constructor(e.array),this.itemSize=e.itemSize,this.count=e.count,this.normalized=e.normalized,this.usage=e.usage,this.gpuType=e.gpuType,this}copyAt(e,t,n){e*=this.itemSize,n*=t.itemSize;for(let s=0,r=this.itemSize;s<r;s++)this.array[e+s]=t.array[n+s];return this}copyArray(e){return this.array.set(e),this}applyMatrix3(e){if(this.itemSize===2)for(let t=0,n=this.count;t<n;t++)la.fromBufferAttribute(this,t),la.applyMatrix3(e),this.setXY(t,la.x,la.y);else if(this.itemSize===3)for(let t=0,n=this.count;t<n;t++)Dt.fromBufferAttribute(this,t),Dt.applyMatrix3(e),this.setXYZ(t,Dt.x,Dt.y,Dt.z);return this}applyMatrix4(e){for(let t=0,n=this.count;t<n;t++)Dt.fromBufferAttribute(this,t),Dt.applyMatrix4(e),this.setXYZ(t,Dt.x,Dt.y,Dt.z);return this}applyNormalMatrix(e){for(let t=0,n=this.count;t<n;t++)Dt.fromBufferAttribute(this,t),Dt.applyNormalMatrix(e),this.setXYZ(t,Dt.x,Dt.y,Dt.z);return this}transformDirection(e){for(let t=0,n=this.count;t<n;t++)Dt.fromBufferAttribute(this,t),Dt.transformDirection(e),this.setXYZ(t,Dt.x,Dt.y,Dt.z);return this}set(e,t=0){return this.array.set(e,t),this}getComponent(e,t){let n=this.array[e*this.itemSize+t];return this.normalized&&(n=hs(n,this.array)),n}setComponent(e,t,n){return this.normalized&&(n=tn(n,this.array)),this.array[e*this.itemSize+t]=n,this}getX(e){let t=this.array[e*this.itemSize];return this.normalized&&(t=hs(t,this.array)),t}setX(e,t){return this.normalized&&(t=tn(t,this.array)),this.array[e*this.itemSize]=t,this}getY(e){let t=this.array[e*this.itemSize+1];return this.normalized&&(t=hs(t,this.array)),t}setY(e,t){return this.normalized&&(t=tn(t,this.array)),this.array[e*this.itemSize+1]=t,this}getZ(e){let t=this.array[e*this.itemSize+2];return this.normalized&&(t=hs(t,this.array)),t}setZ(e,t){return this.normalized&&(t=tn(t,this.array)),this.array[e*this.itemSize+2]=t,this}getW(e){let t=this.array[e*this.itemSize+3];return this.normalized&&(t=hs(t,this.array)),t}setW(e,t){return this.normalized&&(t=tn(t,this.array)),this.array[e*this.itemSize+3]=t,this}setXY(e,t,n){return e*=this.itemSize,this.normalized&&(t=tn(t,this.array),n=tn(n,this.array)),this.array[e+0]=t,this.array[e+1]=n,this}setXYZ(e,t,n,s){return e*=this.itemSize,this.normalized&&(t=tn(t,this.array),n=tn(n,this.array),s=tn(s,this.array)),this.array[e+0]=t,this.array[e+1]=n,this.array[e+2]=s,this}setXYZW(e,t,n,s,r){return e*=this.itemSize,this.normalized&&(t=tn(t,this.array),n=tn(n,this.array),s=tn(s,this.array),r=tn(r,this.array)),this.array[e+0]=t,this.array[e+1]=n,this.array[e+2]=s,this.array[e+3]=r,this}onUpload(e){return this.onUploadCallback=e,this}clone(){return new this.constructor(this.array,this.itemSize).copy(this)}toJSON(){let e={itemSize:this.itemSize,type:this.array.constructor.name,array:Array.from(this.array),normalized:this.normalized};return e.name=this.name,e.usage=this.usage,e.gpuType=this.gpuType,e}dispose(){this.dispatchEvent({type:"dispose"})}};var ar=class extends Xt{constructor(e,t,n){super(new Uint16Array(e),t,n)}};var or=class extends Xt{constructor(e,t,n){super(new Uint32Array(e),t,n)}};var pt=class extends Xt{constructor(e,t,n){super(new Float32Array(e),t,n)}},Pd=new Vn,$s=new B,Ul=new B,Hn=class{constructor(e=new B,t=-1){this.isSphere=!0,this.center=e,this.radius=t}set(e,t){return this.center.copy(e),this.radius=t,this}setFromPoints(e,t){let n=this.center;t!==void 0?n.copy(t):Pd.setFromPoints(e).getCenter(n);let s=0;for(let r=0,a=e.length;r<a;r++)s=Math.max(s,n.distanceToSquared(e[r]));return this.radius=Math.sqrt(s),this}copy(e){return this.center.copy(e.center),this.radius=e.radius,this}isEmpty(){return this.radius<0}makeEmpty(){return this.center.set(0,0,0),this.radius=-1,this}containsPoint(e){return e.distanceToSquared(this.center)<=this.radius*this.radius}distanceToPoint(e){return e.distanceTo(this.center)-this.radius}intersectsSphere(e){let t=this.radius+e.radius;return e.center.distanceToSquared(this.center)<=t*t}intersectsBox(e){return e.intersectsSphere(this)}intersectsPlane(e){return Math.abs(e.distanceToPoint(this.center))<=this.radius}clampPoint(e,t){let n=this.center.distanceToSquared(e);return t.copy(e),n>this.radius*this.radius&&(t.sub(this.center).normalize(),t.multiplyScalar(this.radius).add(this.center)),t}getBoundingBox(e){return this.isEmpty()?(e.makeEmpty(),e):(e.set(this.center,this.center),e.expandByScalar(this.radius),e)}applyMatrix4(e){return this.center.applyMatrix4(e),this.radius=this.radius*e.getMaxScaleOnAxis(),this}translate(e){return this.center.add(e),this}expandByPoint(e){if(this.isEmpty())return this.center.copy(e),this.radius=0,this;$s.subVectors(e,this.center);let t=$s.lengthSq();if(t>this.radius*this.radius){let n=Math.sqrt(t),s=(n-this.radius)*.5;this.center.addScaledVector($s,s/n),this.radius+=s}return this}union(e){return e.isEmpty()?this:this.isEmpty()?(this.copy(e),this):(this.center.equals(e.center)===!0?this.radius=Math.max(this.radius,e.radius):(Ul.subVectors(e.center,this.center).setLength(e.radius),this.expandByPoint($s.copy(e.center).add(Ul)),this.expandByPoint($s.copy(e.center).sub(Ul))),this)}equals(e){return e.center.equals(this.center)&&e.radius===this.radius}clone(){return new this.constructor().copy(this)}toJSON(){return{radius:this.radius,center:this.center.toArray()}}fromJSON(e){return this.radius=e.radius,this.center.fromArray(e.center),this}},Ld=0,xn=new ut,Fl=new kt,as=new B,fn=new Vn,qs=new Vn,Ht=new B,St=class i extends zn{constructor(){super(),this.isBufferGeometry=!0,Object.defineProperty(this,"id",{value:Ld++}),this.uuid=Ps(),this.name="",this.type="BufferGeometry",this.index=null,this.indirect=null,this.indirectOffset=0,this.attributes={},this.morphAttributes={},this.morphTargetsRelative=!1,this.groups=[],this.boundingBox=null,this.boundingSphere=null,this.drawRange={start:0,count:1/0},this.userData={},this._transformed=!1}getIndex(){return this.index}setIndex(e){return Array.isArray(e)?this.index=new(nd(e)?or:ar)(e,1):this.index=e,this}setIndirect(e,t=0){return this.indirect=e,this.indirectOffset=t,this}getIndirect(){return this.indirect}getAttribute(e){return this.attributes[e]}setAttribute(e,t){return this.attributes[e]=t,this}deleteAttribute(e){return delete this.attributes[e],this}hasAttribute(e){return this.attributes[e]!==void 0}addGroup(e,t,n=0){this.groups.push({start:e,count:t,materialIndex:n})}clearGroups(){this.groups=[]}setDrawRange(e,t){this.drawRange.start=e,this.drawRange.count=t}applyMatrix4(e){let t=this.attributes.position;t!==void 0&&(t.applyMatrix4(e),t.needsUpdate=!0);let n=this.attributes.normal;if(n!==void 0){let r=new Ye().getNormalMatrix(e);n.applyNormalMatrix(r),n.needsUpdate=!0}let s=this.attributes.tangent;return s!==void 0&&(s.transformDirection(e),s.needsUpdate=!0),this.boundingBox!==null&&this.computeBoundingBox(),this.boundingSphere!==null&&this.computeBoundingSphere(),this._transformed=!0,this}applyQuaternion(e){return xn.makeRotationFromQuaternion(e),this.applyMatrix4(xn),this}rotateX(e){return xn.makeRotationX(e),this.applyMatrix4(xn),this}rotateY(e){return xn.makeRotationY(e),this.applyMatrix4(xn),this}rotateZ(e){return xn.makeRotationZ(e),this.applyMatrix4(xn),this}translate(e,t,n){return xn.makeTranslation(e,t,n),this.applyMatrix4(xn),this}scale(e,t,n){return xn.makeScale(e,t,n),this.applyMatrix4(xn),this}lookAt(e){return Fl.lookAt(e),Fl.updateMatrix(),this.applyMatrix4(Fl.matrix),this}center(){return this.computeBoundingBox(),this.boundingBox.getCenter(as).negate(),this.translate(as.x,as.y,as.z),this}setFromPoints(e){let t=this.getAttribute("position");if(t===void 0){let n=[];for(let s=0,r=e.length;s<r;s++){let a=e[s];n.push(a.x,a.y,a.z||0)}this.setAttribute("position",new pt(n,3))}else{let n=Math.min(e.length,t.count);for(let s=0;s<n;s++){let r=e[s];t.setXYZ(s,r.x,r.y,r.z||0)}e.length>t.count&&$e("BufferGeometry: Buffer size too small for points data. Use .dispose() and create a new geometry."),t.needsUpdate=!0}return this}computeBoundingBox(){this.boundingBox===null&&(this.boundingBox=new Vn);let e=this.attributes.position,t=this.morphAttributes.position;if(e&&e.isGLBufferAttribute){Xe("BufferGeometry.computeBoundingBox(): GLBufferAttribute requires a manual bounding box.",this),this.boundingBox.set(new B(-1/0,-1/0,-1/0),new B(1/0,1/0,1/0));return}if(e!==void 0){if(this.boundingBox.setFromBufferAttribute(e),t)for(let n=0,s=t.length;n<s;n++){let r=t[n];fn.setFromBufferAttribute(r),this.morphTargetsRelative?(Ht.addVectors(this.boundingBox.min,fn.min),this.boundingBox.expandByPoint(Ht),Ht.addVectors(this.boundingBox.max,fn.max),this.boundingBox.expandByPoint(Ht)):(this.boundingBox.expandByPoint(fn.min),this.boundingBox.expandByPoint(fn.max))}}else this.boundingBox.makeEmpty();(isNaN(this.boundingBox.min.x)||isNaN(this.boundingBox.min.y)||isNaN(this.boundingBox.min.z))&&Xe('BufferGeometry.computeBoundingBox(): Computed min/max have NaN values. The "position" attribute is likely to have NaN values.',this)}computeBoundingSphere(){this.boundingSphere===null&&(this.boundingSphere=new Hn);let e=this.attributes.position,t=this.morphAttributes.position;if(e&&e.isGLBufferAttribute){Xe("BufferGeometry.computeBoundingSphere(): GLBufferAttribute requires a manual bounding sphere.",this),this.boundingSphere.set(new B,1/0);return}if(e){let n=this.boundingSphere.center;if(fn.setFromBufferAttribute(e),t)for(let r=0,a=t.length;r<a;r++){let o=t[r];qs.setFromBufferAttribute(o),this.morphTargetsRelative?(Ht.addVectors(fn.min,qs.min),fn.expandByPoint(Ht),Ht.addVectors(fn.max,qs.max),fn.expandByPoint(Ht)):(fn.expandByPoint(qs.min),fn.expandByPoint(qs.max))}fn.getCenter(n);let s=0;for(let r=0,a=e.count;r<a;r++)Ht.fromBufferAttribute(e,r),s=Math.max(s,n.distanceToSquared(Ht));if(t)for(let r=0,a=t.length;r<a;r++){let o=t[r],l=this.morphTargetsRelative;for(let c=0,h=o.count;c<h;c++)Ht.fromBufferAttribute(o,c),l&&(as.fromBufferAttribute(e,c),Ht.add(as)),s=Math.max(s,n.distanceToSquared(Ht))}this.boundingSphere.radius=Math.sqrt(s),isNaN(this.boundingSphere.radius)&&Xe('BufferGeometry.computeBoundingSphere(): Computed radius is NaN. The "position" attribute is likely to have NaN values.',this)}}computeTangents(){let e=this.index,t=this.attributes;if(e===null||t.position===void 0||t.normal===void 0||t.uv===void 0){Xe("BufferGeometry: .computeTangents() failed. Missing required attributes (index, position, normal or uv)");return}let n=t.position,s=t.normal,r=t.uv,a=this.getAttribute("tangent");(a===void 0||a.count!==n.count)&&(a=new Xt(new Float32Array(4*n.count),4),this.setAttribute("tangent",a));let o=[],l=[];for(let v=0;v<n.count;v++)o[v]=new B,l[v]=new B;let c=new B,h=new B,f=new B,u=new De,d=new De,_=new De,S=new B,g=new B;function p(v,C,O){c.fromBufferAttribute(n,v),h.fromBufferAttribute(n,C),f.fromBufferAttribute(n,O),u.fromBufferAttribute(r,v),d.fromBufferAttribute(r,C),_.fromBufferAttribute(r,O),h.sub(c),f.sub(c),d.sub(u),_.sub(u);let V=1/(d.x*_.y-_.x*d.y);isFinite(V)&&(S.copy(h).multiplyScalar(_.y).addScaledVector(f,-d.y).multiplyScalar(V),g.copy(f).multiplyScalar(d.x).addScaledVector(h,-_.x).multiplyScalar(V),o[v].add(S),o[C].add(S),o[O].add(S),l[v].add(g),l[C].add(g),l[O].add(g))}let w=this.groups;w.length===0&&(w=[{start:0,count:e.count}]);for(let v=0,C=w.length;v<C;++v){let O=w[v],V=O.start,q=O.count;for(let j=V,z=V+q;j<z;j+=3)p(e.getX(j+0),e.getX(j+1),e.getX(j+2))}let I=new B,y=new B,A=new B,E=new B;function D(v){A.fromBufferAttribute(s,v),E.copy(A);let C=o[v];I.copy(C),I.sub(A.multiplyScalar(A.dot(C))).normalize(),y.crossVectors(E,C);let V=y.dot(l[v])<0?-1:1;a.setXYZW(v,I.x,I.y,I.z,V)}for(let v=0,C=w.length;v<C;++v){let O=w[v],V=O.start,q=O.count;for(let j=V,z=V+q;j<z;j+=3)D(e.getX(j+0)),D(e.getX(j+1)),D(e.getX(j+2))}this._transformed=!0}computeVertexNormals(){let e=this.index,t=this.getAttribute("position");if(t!==void 0){let n=this.getAttribute("normal");if(n===void 0||n.count!==t.count)n=new Xt(new Float32Array(t.count*3),3),this.setAttribute("normal",n);else for(let u=0,d=n.count;u<d;u++)n.setXYZ(u,0,0,0);let s=new B,r=new B,a=new B,o=new B,l=new B,c=new B,h=new B,f=new B;if(e)for(let u=0,d=e.count;u<d;u+=3){let _=e.getX(u+0),S=e.getX(u+1),g=e.getX(u+2);s.fromBufferAttribute(t,_),r.fromBufferAttribute(t,S),a.fromBufferAttribute(t,g),h.subVectors(a,r),f.subVectors(s,r),h.cross(f),o.fromBufferAttribute(n,_),l.fromBufferAttribute(n,S),c.fromBufferAttribute(n,g),o.add(h),l.add(h),c.add(h),n.setXYZ(_,o.x,o.y,o.z),n.setXYZ(S,l.x,l.y,l.z),n.setXYZ(g,c.x,c.y,c.z)}else for(let u=0,d=t.count;u<d;u+=3)s.fromBufferAttribute(t,u+0),r.fromBufferAttribute(t,u+1),a.fromBufferAttribute(t,u+2),h.subVectors(a,r),f.subVectors(s,r),h.cross(f),n.setXYZ(u+0,h.x,h.y,h.z),n.setXYZ(u+1,h.x,h.y,h.z),n.setXYZ(u+2,h.x,h.y,h.z);this.normalizeNormals(),n.needsUpdate=!0}}normalizeNormals(){let e=this.attributes.normal;for(let t=0,n=e.count;t<n;t++)Ht.fromBufferAttribute(e,t),Ht.normalize(),e.setXYZ(t,Ht.x,Ht.y,Ht.z)}toNonIndexed(){function e(o,l){let c=o.array,h=o.itemSize,f=o.normalized,u=new c.constructor(l.length*h),d=0,_=0;for(let S=0,g=l.length;S<g;S++){o.isInterleavedBufferAttribute?d=l[S]*o.data.stride+o.offset:d=l[S]*h;for(let p=0;p<h;p++)u[_++]=c[d++]}return new Xt(u,h,f)}if(this.index===null)return $e("BufferGeometry.toNonIndexed(): BufferGeometry is already non-indexed."),this;let t=new i,n=this.index.array,s=this.attributes;for(let o in s){let l=s[o],c=e(l,n);t.setAttribute(o,c)}let r=this.morphAttributes;for(let o in r){let l=[],c=r[o];for(let h=0,f=c.length;h<f;h++){let u=c[h],d=e(u,n);l.push(d)}t.morphAttributes[o]=l}t.morphTargetsRelative=this.morphTargetsRelative;let a=this.groups;for(let o=0,l=a.length;o<l;o++){let c=a[o];t.addGroup(c.start,c.count,c.materialIndex)}return t}toJSON(){let e={metadata:{version:4.7,type:"BufferGeometry",generator:"BufferGeometry.toJSON"}};if(e.uuid=this.uuid,e.type=this.parameters!==void 0&&this._transformed===!0?"BufferGeometry":this.type,e.name=this.name,Object.keys(this.userData).length>0&&(e.userData=this.userData),this.parameters!==void 0&&this._transformed!==!0){let l=this.parameters;for(let c in l)l[c]!==void 0&&(e[c]=l[c]);return e}e.data={attributes:{}};let t=this.index;t!==null&&(e.data.index={type:t.array.constructor.name,array:Array.prototype.slice.call(t.array)});let n=this.attributes;for(let l in n){let c=n[l];e.data.attributes[l]=c.toJSON(e.data)}let s={},r=!1;for(let l in this.morphAttributes){let c=this.morphAttributes[l],h=[];for(let f=0,u=c.length;f<u;f++){let d=c[f];h.push(d.toJSON(e.data))}h.length>0&&(s[l]=h,r=!0)}r&&(e.data.morphAttributes=s,e.data.morphTargetsRelative=this.morphTargetsRelative);let a=this.groups;a.length>0&&(e.data.groups=JSON.parse(JSON.stringify(a)));let o=this.boundingSphere;return o!==null&&(e.data.boundingSphere=o.toJSON()),e}clone(){return new this.constructor().copy(this)}copy(e){this.index=null,this.attributes={},this.morphAttributes={},this.groups=[],this.boundingBox=null,this.boundingSphere=null;let t={};this.name=e.name;let n=e.index;n!==null&&this.setIndex(n.clone());let s=e.attributes;for(let c in s){let h=s[c];this.setAttribute(c,h.clone(t))}let r=e.morphAttributes;for(let c in r){let h=[],f=r[c];for(let u=0,d=f.length;u<d;u++)h.push(f[u].clone(t));this.morphAttributes[c]=h}this.morphTargetsRelative=e.morphTargetsRelative;let a=e.groups;for(let c=0,h=a.length;c<h;c++){let f=a[c];this.addGroup(f.start,f.count,f.materialIndex)}let o=e.boundingBox;o!==null&&(this.boundingBox=o.clone());let l=e.boundingSphere;return l!==null&&(this.boundingSphere=l.clone()),this.drawRange.start=e.drawRange.start,this.drawRange.count=e.drawRange.count,this.userData=e.userData,this._transformed=e._transformed,this}dispose(){this.dispatchEvent({type:"dispose"})}};var kl=new B,Nd=new B,Dd=new Ye,In=class{constructor(e=new B(1,0,0),t=0){this.isPlane=!0,this.normal=e,this.constant=t}set(e,t){return this.normal.copy(e),this.constant=t,this}setComponents(e,t,n,s){return this.normal.set(e,t,n),this.constant=s,this}setFromNormalAndCoplanarPoint(e,t){return this.normal.copy(e),this.constant=-t.dot(this.normal),this}setFromCoplanarPoints(e,t,n){let s=kl.subVectors(n,t).cross(Nd.subVectors(e,t)).normalize();return this.setFromNormalAndCoplanarPoint(s,e),this}copy(e){return this.normal.copy(e.normal),this.constant=e.constant,this}normalize(){let e=1/this.normal.length();return this.normal.multiplyScalar(e),this.constant*=e,this}negate(){return this.constant*=-1,this.normal.negate(),this}distanceToPoint(e){return this.normal.dot(e)+this.constant}distanceToSphere(e){return this.distanceToPoint(e.center)-e.radius}projectPoint(e,t){return t.copy(e).addScaledVector(this.normal,-this.distanceToPoint(e))}intersectLine(e,t,n=!0){let s=e.delta(kl),r=this.normal.dot(s);if(r===0)return this.distanceToPoint(e.start)===0?t.copy(e.start):null;let a=-(e.start.dot(this.normal)+this.constant)/r;return n===!0&&(a<0||a>1)?null:t.copy(e.start).addScaledVector(s,a)}intersectsLine(e){let t=this.distanceToPoint(e.start),n=this.distanceToPoint(e.end);return t<0&&n>0||n<0&&t>0}intersectsBox(e){return e.intersectsPlane(this)}intersectsSphere(e){return e.intersectsPlane(this)}coplanarPoint(e){return e.copy(this.normal).multiplyScalar(-this.constant)}applyMatrix4(e,t){let n=t||Dd.getNormalMatrix(e),s=this.coplanarPoint(kl).applyMatrix4(e),r=this.normal.applyMatrix3(n).normalize();return this.constant=-s.dot(r),this}translate(e){return this.constant-=e.dot(this.normal),this}equals(e){return e.normal.equals(this.normal)&&e.constant===this.constant}clone(){return new this.constructor().copy(this)}toJSON(){return{normal:this.normal.toArray(),constant:this.constant}}fromJSON(e){return this.normal.fromArray(e.normal),this.constant=e.constant,this}},Ud=0,Ln=class extends zn{constructor(){super(),this.isMaterial=!0,Object.defineProperty(this,"id",{value:Ud++}),this.uuid=Ps(),this.name="",this.type="Material",this.blending=Cs,this.side=yi,this.vertexColors=!1,this.opacity=1,this.transparent=!1,this.alphaHash=!1,this.blendSrc=rc,this.blendDst=ac,this.blendEquation=zi,this.blendSrcAlpha=null,this.blendDstAlpha=null,this.blendEquationAlpha=null,this.blendColor=new qe(0,0,0),this.blendAlpha=0,this.depthFunc=fs,this.depthTest=!0,this.depthWrite=!0,this.stencilWriteMask=255,this.stencilFunc=Zu,this.stencilRef=0,this.stencilFuncMask=255,this.stencilFail=Aa,this.stencilZFail=Aa,this.stencilZPass=Aa,this.stencilWrite=!1,this.clippingPlanes=null,this.clipIntersection=!1,this.clipShadows=!1,this.shadowSide=null,this.colorWrite=!0,this.precision=null,this.polygonOffset=!1,this.polygonOffsetFactor=0,this.polygonOffsetUnits=0,this.dithering=!1,this.alphaToCoverage=!1,this.premultipliedAlpha=!1,this.forceSinglePass=!1,this.allowOverride=!0,this.visible=!0,this.toneMapped=!0,this.userData={},this.version=0,this._alphaTest=0}get alphaTest(){return this._alphaTest}set alphaTest(e){this._alphaTest>0!=e>0&&this.version++,this._alphaTest=e}onBeforeRender(){}onBeforeCompile(){}customProgramCacheKey(){return this.onBeforeCompile.toString()}setValues(e){if(e!==void 0)for(let t in e){let n=e[t];if(n===void 0){$e(`Material: parameter '${t}' has value of undefined.`);continue}let s=this[t];if(s===void 0){$e(`Material: '${t}' is not a property of THREE.${this.type}.`);continue}s&&s.isColor?s.set(n):s&&s.isVector2&&n&&n.isVector2||s&&s.isEuler&&n&&n.isEuler||s&&s.isVector3&&n&&n.isVector3?s.copy(n):this[t]=n}}toJSON(e){let t=e===void 0||typeof e=="string";t&&(e={textures:{},images:{}});let n={metadata:{version:4.7,type:"Material",generator:"Material.toJSON"}};n.uuid=this.uuid,n.type=this.type,n.blending=this.blending,n.side=this.side,n.shadowSide=this.shadowSide,n.vertexColors=this.vertexColors,n.opacity=this.opacity,n.transparent=this.transparent,n.blendSrc=this.blendSrc,n.blendDst=this.blendDst,n.blendEquation=this.blendEquation,n.blendSrcAlpha=this.blendSrcAlpha,n.blendDstAlpha=this.blendDstAlpha,n.blendEquationAlpha=this.blendEquationAlpha,n.blendColor=this.blendColor.getHex(),n.blendAlpha=this.blendAlpha,n.depthFunc=this.depthFunc,n.depthTest=this.depthTest,n.depthWrite=this.depthWrite,n.colorWrite=this.colorWrite,n.clipIntersection=this.clipIntersection,n.clipShadows=this.clipShadows,n.stencilWriteMask=this.stencilWriteMask,n.stencilFunc=this.stencilFunc,n.stencilRef=this.stencilRef,n.stencilFuncMask=this.stencilFuncMask,n.stencilFail=this.stencilFail,n.stencilZFail=this.stencilZFail,n.stencilZPass=this.stencilZPass,n.stencilWrite=this.stencilWrite,n.polygonOffset=this.polygonOffset,n.polygonOffsetFactor=this.polygonOffsetFactor,n.polygonOffsetUnits=this.polygonOffsetUnits,n.dithering=this.dithering,n.alphaTest=this.alphaTest,n.alphaHash=this.alphaHash,n.alphaToCoverage=this.alphaToCoverage,n.premultipliedAlpha=this.premultipliedAlpha,n.forceSinglePass=this.forceSinglePass,n.allowOverride=this.allowOverride,n.visible=this.visible,n.toneMapped=this.toneMapped,n.name=this.name,this.color&&this.color.isColor&&(n.color=this.color.getHex()),this.roughness!==void 0&&(n.roughness=this.roughness),this.metalness!==void 0&&(n.metalness=this.metalness),this.sheen!==void 0&&(n.sheen=this.sheen),this.sheenColor&&this.sheenColor.isColor&&(n.sheenColor=this.sheenColor.getHex()),this.sheenRoughness!==void 0&&(n.sheenRoughness=this.sheenRoughness),this.emissive&&this.emissive.isColor&&(n.emissive=this.emissive.getHex()),this.emissiveIntensity!==void 0&&(n.emissiveIntensity=this.emissiveIntensity),this.specular&&this.specular.isColor&&(n.specular=this.specular.getHex()),this.specularIntensity!==void 0&&(n.specularIntensity=this.specularIntensity),this.specularColor&&this.specularColor.isColor&&(n.specularColor=this.specularColor.getHex()),this.shininess!==void 0&&(n.shininess=this.shininess),this.clearcoat!==void 0&&(n.clearcoat=this.clearcoat),this.clearcoatRoughness!==void 0&&(n.clearcoatRoughness=this.clearcoatRoughness),this.clearcoatMap&&this.clearcoatMap.isTexture&&(n.clearcoatMap=this.clearcoatMap.toJSON(e).uuid),this.clearcoatRoughnessMap&&this.clearcoatRoughnessMap.isTexture&&(n.clearcoatRoughnessMap=this.clearcoatRoughnessMap.toJSON(e).uuid),this.clearcoatNormalMap&&this.clearcoatNormalMap.isTexture&&(n.clearcoatNormalMap=this.clearcoatNormalMap.toJSON(e).uuid,n.clearcoatNormalScale=this.clearcoatNormalScale.toArray()),this.sheenColorMap&&this.sheenColorMap.isTexture&&(n.sheenColorMap=this.sheenColorMap.toJSON(e).uuid),this.sheenRoughnessMap&&this.sheenRoughnessMap.isTexture&&(n.sheenRoughnessMap=this.sheenRoughnessMap.toJSON(e).uuid),this.dispersion!==void 0&&(n.dispersion=this.dispersion),this.retroreflectivity!==void 0&&(n.retroreflectivity=this.retroreflectivity),this.iridescence!==void 0&&(n.iridescence=this.iridescence),this.iridescenceIOR!==void 0&&(n.iridescenceIOR=this.iridescenceIOR),this.iridescenceThicknessRange!==void 0&&(n.iridescenceThicknessRange=this.iridescenceThicknessRange),this.iridescenceMap&&this.iridescenceMap.isTexture&&(n.iridescenceMap=this.iridescenceMap.toJSON(e).uuid),this.iridescenceThicknessMap&&this.iridescenceThicknessMap.isTexture&&(n.iridescenceThicknessMap=this.iridescenceThicknessMap.toJSON(e).uuid),this.anisotropy!==void 0&&(n.anisotropy=this.anisotropy),this.anisotropyRotation!==void 0&&(n.anisotropyRotation=this.anisotropyRotation),this.anisotropyMap&&this.anisotropyMap.isTexture&&(n.anisotropyMap=this.anisotropyMap.toJSON(e).uuid),this.map&&this.map.isTexture&&(n.map=this.map.toJSON(e).uuid),this.matcap&&this.matcap.isTexture&&(n.matcap=this.matcap.toJSON(e).uuid),this.alphaMap&&this.alphaMap.isTexture&&(n.alphaMap=this.alphaMap.toJSON(e).uuid),this.lightMap&&this.lightMap.isTexture&&(n.lightMap=this.lightMap.toJSON(e).uuid,n.lightMapIntensity=this.lightMapIntensity),this.aoMap&&this.aoMap.isTexture&&(n.aoMap=this.aoMap.toJSON(e).uuid,n.aoMapIntensity=this.aoMapIntensity),this.bumpMap&&this.bumpMap.isTexture&&(n.bumpMap=this.bumpMap.toJSON(e).uuid,n.bumpScale=this.bumpScale),this.normalMap&&this.normalMap.isTexture&&(n.normalMap=this.normalMap.toJSON(e).uuid,n.normalMapType=this.normalMapType,n.normalScale=this.normalScale.toArray()),this.displacementMap&&this.displacementMap.isTexture&&(n.displacementMap=this.displacementMap.toJSON(e).uuid,n.displacementScale=this.displacementScale,n.displacementBias=this.displacementBias),this.roughnessMap&&this.roughnessMap.isTexture&&(n.roughnessMap=this.roughnessMap.toJSON(e).uuid),this.metalnessMap&&this.metalnessMap.isTexture&&(n.metalnessMap=this.metalnessMap.toJSON(e).uuid),this.emissiveMap&&this.emissiveMap.isTexture&&(n.emissiveMap=this.emissiveMap.toJSON(e).uuid),this.specularMap&&this.specularMap.isTexture&&(n.specularMap=this.specularMap.toJSON(e).uuid),this.specularIntensityMap&&this.specularIntensityMap.isTexture&&(n.specularIntensityMap=this.specularIntensityMap.toJSON(e).uuid),this.specularColorMap&&this.specularColorMap.isTexture&&(n.specularColorMap=this.specularColorMap.toJSON(e).uuid),this.envMap&&this.envMap.isTexture&&(n.envMap=this.envMap.toJSON(e).uuid,this.combine!==void 0&&(n.combine=this.combine)),this.envMapRotation!==void 0&&(n.envMapRotation=this.envMapRotation.toArray()),this.envMapIntensity!==void 0&&(n.envMapIntensity=this.envMapIntensity),this.reflectivity!==void 0&&(n.reflectivity=this.reflectivity),this.refractionRatio!==void 0&&(n.refractionRatio=this.refractionRatio),this.gradientMap&&this.gradientMap.isTexture&&(n.gradientMap=this.gradientMap.toJSON(e).uuid),this.transmission!==void 0&&(n.transmission=this.transmission),this.transmissionMap&&this.transmissionMap.isTexture&&(n.transmissionMap=this.transmissionMap.toJSON(e).uuid),this.thickness!==void 0&&(n.thickness=this.thickness),this.thicknessMap&&this.thicknessMap.isTexture&&(n.thicknessMap=this.thicknessMap.toJSON(e).uuid),this.attenuationDistance!==void 0&&(n.attenuationDistance=this.attenuationDistance),this.attenuationColor!==void 0&&(n.attenuationColor=this.attenuationColor.getHex()),this.size!==void 0&&(n.size=this.size),this.sizeAttenuation!==void 0&&(n.sizeAttenuation=this.sizeAttenuation),Array.isArray(this.clippingPlanes)&&this.clippingPlanes.length>0&&(n.clippingPlanes=this.clippingPlanes.map(r=>r.toJSON())),this.rotation!==void 0&&(n.rotation=this.rotation),this.depthPacking!==void 0&&(n.depthPacking=this.depthPacking),this.linewidth!==void 0&&(n.linewidth=this.linewidth),this.linecap!==void 0&&(n.linecap=this.linecap),this.linejoin!==void 0&&(n.linejoin=this.linejoin),this.dashSize!==void 0&&(n.dashSize=this.dashSize),this.gapSize!==void 0&&(n.gapSize=this.gapSize),this.scale!==void 0&&(n.scale=this.scale),this.wireframe!==void 0&&(n.wireframe=this.wireframe),this.wireframeLinewidth!==void 0&&(n.wireframeLinewidth=this.wireframeLinewidth),this.wireframeLinecap!==void 0&&(n.wireframeLinecap=this.wireframeLinecap),this.wireframeLinejoin!==void 0&&(n.wireframeLinejoin=this.wireframeLinejoin),this.flatShading!==void 0&&(n.flatShading=this.flatShading),this.fog!==void 0&&(n.fog=this.fog),Object.keys(this.userData).length>0&&(n.userData=this.userData);function s(r){let a=[];for(let o in r){let l=r[o];delete l.metadata,a.push(l)}return a}if(t){let r=s(e.textures),a=s(e.images);r.length>0&&(n.textures=r),a.length>0&&(n.images=a)}return n}fromJSON(e,t){if(e.uuid!==void 0&&(this.uuid=e.uuid),e.name!==void 0&&(this.name=e.name),e.color!==void 0&&this.color!==void 0&&this.color.setHex(e.color),e.roughness!==void 0&&(this.roughness=e.roughness),e.metalness!==void 0&&(this.metalness=e.metalness),e.sheen!==void 0&&(this.sheen=e.sheen),e.sheenColor!==void 0&&(this.sheenColor=new qe().setHex(e.sheenColor)),e.sheenRoughness!==void 0&&(this.sheenRoughness=e.sheenRoughness),e.emissive!==void 0&&this.emissive!==void 0&&this.emissive.setHex(e.emissive),e.specular!==void 0&&this.specular!==void 0&&this.specular.setHex(e.specular),e.specularIntensity!==void 0&&(this.specularIntensity=e.specularIntensity),e.specularColor!==void 0&&this.specularColor!==void 0&&this.specularColor.setHex(e.specularColor),e.shininess!==void 0&&(this.shininess=e.shininess),e.clearcoat!==void 0&&(this.clearcoat=e.clearcoat),e.clearcoatRoughness!==void 0&&(this.clearcoatRoughness=e.clearcoatRoughness),e.dispersion!==void 0&&(this.dispersion=e.dispersion),e.retroreflectivity!==void 0&&(this.retroreflectivity=e.retroreflectivity),e.iridescence!==void 0&&(this.iridescence=e.iridescence),e.iridescenceIOR!==void 0&&(this.iridescenceIOR=e.iridescenceIOR),e.iridescenceThicknessRange!==void 0&&(this.iridescenceThicknessRange=e.iridescenceThicknessRange),e.transmission!==void 0&&(this.transmission=e.transmission),e.thickness!==void 0&&(this.thickness=e.thickness),e.attenuationDistance!==void 0&&(this.attenuationDistance=e.attenuationDistance),e.attenuationColor!==void 0&&this.attenuationColor!==void 0&&this.attenuationColor.setHex(e.attenuationColor),e.anisotropy!==void 0&&(this.anisotropy=e.anisotropy),e.anisotropyRotation!==void 0&&(this.anisotropyRotation=e.anisotropyRotation),e.fog!==void 0&&(this.fog=e.fog),e.flatShading!==void 0&&(this.flatShading=e.flatShading),e.blending!==void 0&&(this.blending=e.blending),e.combine!==void 0&&(this.combine=e.combine),e.side!==void 0&&(this.side=e.side),e.shadowSide!==void 0&&(this.shadowSide=e.shadowSide),e.opacity!==void 0&&(this.opacity=e.opacity),e.transparent!==void 0&&(this.transparent=e.transparent),e.alphaTest!==void 0&&(this.alphaTest=e.alphaTest),e.alphaHash!==void 0&&(this.alphaHash=e.alphaHash),e.depthFunc!==void 0&&(this.depthFunc=e.depthFunc),e.depthTest!==void 0&&(this.depthTest=e.depthTest),e.depthWrite!==void 0&&(this.depthWrite=e.depthWrite),e.colorWrite!==void 0&&(this.colorWrite=e.colorWrite),e.clippingPlanes!==void 0&&(this.clippingPlanes=e.clippingPlanes.map(n=>new In().fromJSON(n))),e.clipIntersection!==void 0&&(this.clipIntersection=e.clipIntersection),e.clipShadows!==void 0&&(this.clipShadows=e.clipShadows),e.depthPacking!==void 0&&(this.depthPacking=e.depthPacking),e.blendSrc!==void 0&&(this.blendSrc=e.blendSrc),e.blendDst!==void 0&&(this.blendDst=e.blendDst),e.blendEquation!==void 0&&(this.blendEquation=e.blendEquation),e.blendSrcAlpha!==void 0&&(this.blendSrcAlpha=e.blendSrcAlpha),e.blendDstAlpha!==void 0&&(this.blendDstAlpha=e.blendDstAlpha),e.blendEquationAlpha!==void 0&&(this.blendEquationAlpha=e.blendEquationAlpha),e.blendColor!==void 0&&this.blendColor!==void 0&&this.blendColor.setHex(e.blendColor),e.blendAlpha!==void 0&&(this.blendAlpha=e.blendAlpha),e.stencilWriteMask!==void 0&&(this.stencilWriteMask=e.stencilWriteMask),e.stencilFunc!==void 0&&(this.stencilFunc=e.stencilFunc),e.stencilRef!==void 0&&(this.stencilRef=e.stencilRef),e.stencilFuncMask!==void 0&&(this.stencilFuncMask=e.stencilFuncMask),e.stencilFail!==void 0&&(this.stencilFail=e.stencilFail),e.stencilZFail!==void 0&&(this.stencilZFail=e.stencilZFail),e.stencilZPass!==void 0&&(this.stencilZPass=e.stencilZPass),e.stencilWrite!==void 0&&(this.stencilWrite=e.stencilWrite),e.wireframe!==void 0&&(this.wireframe=e.wireframe),e.wireframeLinewidth!==void 0&&(this.wireframeLinewidth=e.wireframeLinewidth),e.wireframeLinecap!==void 0&&(this.wireframeLinecap=e.wireframeLinecap),e.wireframeLinejoin!==void 0&&(this.wireframeLinejoin=e.wireframeLinejoin),e.rotation!==void 0&&(this.rotation=e.rotation),e.linewidth!==void 0&&(this.linewidth=e.linewidth),e.linecap!==void 0&&(this.linecap=e.linecap),e.linejoin!==void 0&&(this.linejoin=e.linejoin),e.dashSize!==void 0&&(this.dashSize=e.dashSize),e.gapSize!==void 0&&(this.gapSize=e.gapSize),e.scale!==void 0&&(this.scale=e.scale),e.polygonOffset!==void 0&&(this.polygonOffset=e.polygonOffset),e.polygonOffsetFactor!==void 0&&(this.polygonOffsetFactor=e.polygonOffsetFactor),e.polygonOffsetUnits!==void 0&&(this.polygonOffsetUnits=e.polygonOffsetUnits),e.dithering!==void 0&&(this.dithering=e.dithering),e.alphaToCoverage!==void 0&&(this.alphaToCoverage=e.alphaToCoverage),e.premultipliedAlpha!==void 0&&(this.premultipliedAlpha=e.premultipliedAlpha),e.forceSinglePass!==void 0&&(this.forceSinglePass=e.forceSinglePass),e.allowOverride!==void 0&&(this.allowOverride=e.allowOverride),e.visible!==void 0&&(this.visible=e.visible),e.toneMapped!==void 0&&(this.toneMapped=e.toneMapped),e.userData!==void 0&&(this.userData=e.userData),e.vertexColors!==void 0&&(typeof e.vertexColors=="number"?this.vertexColors=e.vertexColors>0:this.vertexColors=e.vertexColors),e.size!==void 0&&(this.size=e.size),e.sizeAttenuation!==void 0&&(this.sizeAttenuation=e.sizeAttenuation),e.map!==void 0&&(this.map=t[e.map]||null),e.matcap!==void 0&&(this.matcap=t[e.matcap]||null),e.alphaMap!==void 0&&(this.alphaMap=t[e.alphaMap]||null),e.bumpMap!==void 0&&(this.bumpMap=t[e.bumpMap]||null),e.bumpScale!==void 0&&(this.bumpScale=e.bumpScale),e.normalMap!==void 0&&(this.normalMap=t[e.normalMap]||null),e.normalMapType!==void 0&&(this.normalMapType=e.normalMapType),e.normalScale!==void 0){let n=e.normalScale;Array.isArray(n)===!1&&(n=[n,n]),this.normalScale=new De().fromArray(n)}return e.displacementMap!==void 0&&(this.displacementMap=t[e.displacementMap]||null),e.displacementScale!==void 0&&(this.displacementScale=e.displacementScale),e.displacementBias!==void 0&&(this.displacementBias=e.displacementBias),e.roughnessMap!==void 0&&(this.roughnessMap=t[e.roughnessMap]||null),e.metalnessMap!==void 0&&(this.metalnessMap=t[e.metalnessMap]||null),e.emissiveMap!==void 0&&(this.emissiveMap=t[e.emissiveMap]||null),e.emissiveIntensity!==void 0&&(this.emissiveIntensity=e.emissiveIntensity),e.specularMap!==void 0&&(this.specularMap=t[e.specularMap]||null),e.specularIntensityMap!==void 0&&(this.specularIntensityMap=t[e.specularIntensityMap]||null),e.specularColorMap!==void 0&&(this.specularColorMap=t[e.specularColorMap]||null),e.envMap!==void 0&&(this.envMap=t[e.envMap]||null),e.envMapRotation!==void 0&&this.envMapRotation.fromArray(e.envMapRotation),e.envMapIntensity!==void 0&&(this.envMapIntensity=e.envMapIntensity),e.reflectivity!==void 0&&(this.reflectivity=e.reflectivity),e.refractionRatio!==void 0&&(this.refractionRatio=e.refractionRatio),e.lightMap!==void 0&&(this.lightMap=t[e.lightMap]||null),e.lightMapIntensity!==void 0&&(this.lightMapIntensity=e.lightMapIntensity),e.aoMap!==void 0&&(this.aoMap=t[e.aoMap]||null),e.aoMapIntensity!==void 0&&(this.aoMapIntensity=e.aoMapIntensity),e.gradientMap!==void 0&&(this.gradientMap=t[e.gradientMap]||null),e.clearcoatMap!==void 0&&(this.clearcoatMap=t[e.clearcoatMap]||null),e.clearcoatRoughnessMap!==void 0&&(this.clearcoatRoughnessMap=t[e.clearcoatRoughnessMap]||null),e.clearcoatNormalMap!==void 0&&(this.clearcoatNormalMap=t[e.clearcoatNormalMap]||null),e.clearcoatNormalScale!==void 0&&(this.clearcoatNormalScale=new De().fromArray(e.clearcoatNormalScale)),e.iridescenceMap!==void 0&&(this.iridescenceMap=t[e.iridescenceMap]||null),e.iridescenceThicknessMap!==void 0&&(this.iridescenceThicknessMap=t[e.iridescenceThicknessMap]||null),e.transmissionMap!==void 0&&(this.transmissionMap=t[e.transmissionMap]||null),e.thicknessMap!==void 0&&(this.thicknessMap=t[e.thicknessMap]||null),e.anisotropyMap!==void 0&&(this.anisotropyMap=t[e.anisotropyMap]||null),e.sheenColorMap!==void 0&&(this.sheenColorMap=t[e.sheenColorMap]||null),e.sheenRoughnessMap!==void 0&&(this.sheenRoughnessMap=t[e.sheenRoughnessMap]||null),this}clone(){return new this.constructor().copy(this)}copy(e){this.name=e.name,this.blending=e.blending,this.side=e.side,this.vertexColors=e.vertexColors,this.opacity=e.opacity,this.transparent=e.transparent,this.blendSrc=e.blendSrc,this.blendDst=e.blendDst,this.blendEquation=e.blendEquation,this.blendSrcAlpha=e.blendSrcAlpha,this.blendDstAlpha=e.blendDstAlpha,this.blendEquationAlpha=e.blendEquationAlpha,this.blendColor.copy(e.blendColor),this.blendAlpha=e.blendAlpha,this.depthFunc=e.depthFunc,this.depthTest=e.depthTest,this.depthWrite=e.depthWrite,this.stencilWriteMask=e.stencilWriteMask,this.stencilFunc=e.stencilFunc,this.stencilRef=e.stencilRef,this.stencilFuncMask=e.stencilFuncMask,this.stencilFail=e.stencilFail,this.stencilZFail=e.stencilZFail,this.stencilZPass=e.stencilZPass,this.stencilWrite=e.stencilWrite;let t=e.clippingPlanes,n=null;if(t!==null){let s=t.length;n=new Array(s);for(let r=0;r!==s;++r)n[r]=t[r].clone()}return this.clippingPlanes=n,this.clipIntersection=e.clipIntersection,this.clipShadows=e.clipShadows,this.shadowSide=e.shadowSide,this.colorWrite=e.colorWrite,this.precision=e.precision,this.polygonOffset=e.polygonOffset,this.polygonOffsetFactor=e.polygonOffsetFactor,this.polygonOffsetUnits=e.polygonOffsetUnits,this.dithering=e.dithering,this.alphaTest=e.alphaTest,this.alphaHash=e.alphaHash,this.alphaToCoverage=e.alphaToCoverage,this.premultipliedAlpha=e.premultipliedAlpha,this.forceSinglePass=e.forceSinglePass,this.allowOverride=e.allowOverride,this.visible=e.visible,this.toneMapped=e.toneMapped,this.userData=JSON.parse(JSON.stringify(e.userData)),this}dispose(){this.dispatchEvent({type:"dispose"})}set needsUpdate(e){e===!0&&this.version++}};var Jn=new B,Ol=new B,ca=new B,ua=new B,Ui=class{constructor(e=new B,t=new B(0,0,-1)){this.origin=e,this.direction=t}set(e,t){return this.origin.copy(e),this.direction.copy(t),this}copy(e){return this.origin.copy(e.origin),this.direction.copy(e.direction),this}at(e,t){return t.copy(this.origin).addScaledVector(this.direction,e)}lookAt(e){return this.direction.copy(e).sub(this.origin).normalize(),this}recast(e){return this.origin.copy(this.at(e,Jn)),this}closestPointToPoint(e,t){t.subVectors(e,this.origin);let n=t.dot(this.direction);return n<0?t.copy(this.origin):t.copy(this.origin).addScaledVector(this.direction,n)}distanceToPoint(e){return Math.sqrt(this.distanceSqToPoint(e))}distanceSqToPoint(e){let t=Jn.subVectors(e,this.origin).dot(this.direction);return t<0?this.origin.distanceToSquared(e):(Jn.copy(this.origin).addScaledVector(this.direction,t),Jn.distanceToSquared(e))}distanceSqToSegment(e,t,n,s){Ol.copy(e).add(t).multiplyScalar(.5),ca.copy(t).sub(e).normalize(),ua.copy(this.origin).sub(Ol);let r=e.distanceTo(t)*.5,a=-this.direction.dot(ca),o=ua.dot(this.direction),l=-ua.dot(ca),c=ua.lengthSq(),h=Math.abs(1-a*a),f,u,d,_;if(h>0)if(f=a*l-o,u=a*o-l,_=r*h,f>=0)if(u>=-_)if(u<=_){let S=1/h;f*=S,u*=S,d=f*(f+a*u+2*o)+u*(a*f+u+2*l)+c}else u=r,f=Math.max(0,-(a*u+o)),d=-f*f+u*(u+2*l)+c;else u=-r,f=Math.max(0,-(a*u+o)),d=-f*f+u*(u+2*l)+c;else u<=-_?(f=Math.max(0,-(-a*r+o)),u=f>0?-r:Math.min(Math.max(-r,-l),r),d=-f*f+u*(u+2*l)+c):u<=_?(f=0,u=Math.min(Math.max(-r,-l),r),d=u*(u+2*l)+c):(f=Math.max(0,-(a*r+o)),u=f>0?r:Math.min(Math.max(-r,-l),r),d=-f*f+u*(u+2*l)+c);else u=a>0?-r:r,f=Math.max(0,-(a*u+o)),d=-f*f+u*(u+2*l)+c;return n&&n.copy(this.origin).addScaledVector(this.direction,f),s&&s.copy(Ol).addScaledVector(ca,u),d}intersectSphere(e,t){if(e.radius<0)return null;Jn.subVectors(e.center,this.origin);let n=Jn.dot(this.direction),s=Jn.dot(Jn)-n*n,r=e.radius*e.radius;if(s>r)return null;let a=Math.sqrt(r-s),o=n-a,l=n+a;return l<0?null:o<0?this.at(l,t):this.at(o,t)}intersectsSphere(e){return e.radius<0?!1:this.distanceSqToPoint(e.center)<=e.radius*e.radius}distanceToPlane(e){let t=e.normal.dot(this.direction);if(t===0)return e.distanceToPoint(this.origin)===0?0:null;let n=-(this.origin.dot(e.normal)+e.constant)/t;return n>=0?n:null}intersectPlane(e,t){let n=this.distanceToPlane(e);return n===null?null:this.at(n,t)}intersectsPlane(e){let t=e.distanceToPoint(this.origin);return t===0||e.normal.dot(this.direction)*t<0}intersectBox(e,t){let n,s,r,a,o,l,c=1/this.direction.x,h=1/this.direction.y,f=1/this.direction.z,u=this.origin;return c>=0?(n=(e.min.x-u.x)*c,s=(e.max.x-u.x)*c):(n=(e.max.x-u.x)*c,s=(e.min.x-u.x)*c),h>=0?(r=(e.min.y-u.y)*h,a=(e.max.y-u.y)*h):(r=(e.max.y-u.y)*h,a=(e.min.y-u.y)*h),n>a||r>s||((r>n||isNaN(n))&&(n=r),(a<s||isNaN(s))&&(s=a),f>=0?(o=(e.min.z-u.z)*f,l=(e.max.z-u.z)*f):(o=(e.max.z-u.z)*f,l=(e.min.z-u.z)*f),n>l||o>s)||((o>n||n!==n)&&(n=o),(l<s||s!==s)&&(s=l),s<0)?null:this.at(n>=0?n:s,t)}intersectsBox(e){return this.intersectBox(e,Jn)!==null}intersectTriangle(e,t,n,s,r){let a=this.origin,o=this.direction,l=o.x,c=o.y,h=o.z,f=e.x-a.x,u=e.y-a.y,d=e.z-a.z,_=t.x-a.x,S=t.y-a.y,g=t.z-a.z,p=n.x-a.x,w=n.y-a.y,I=n.z-a.z,y=Math.abs(l),A=Math.abs(c),E=Math.abs(h),D,v,C,O,V,q,j,z,Y,te,re,Z;if(y>=A&&y>=E?(C=l,q=f,Y=_,Z=p,l>=0?(D=c,v=h,O=u,V=d,j=S,z=g,te=w,re=I):(D=h,v=c,O=d,V=u,j=g,z=S,te=I,re=w)):A>=E?(C=c,q=u,Y=S,Z=w,c>=0?(D=h,v=l,O=d,V=f,j=g,z=_,te=I,re=p):(D=l,v=h,O=f,V=d,j=_,z=g,te=p,re=I)):(C=h,q=d,Y=g,Z=I,h>=0?(D=l,v=c,O=f,V=u,j=_,z=S,te=p,re=w):(D=c,v=l,O=u,V=f,j=S,z=_,te=w,re=p)),C===0)return null;let Q=D/C,le=v/C,se=1/C,Oe=O-Q*q,Ie=V-le*q,it=j-Q*Y,Ve=z-le*Y,He=te-Q*Z,ee=re-le*Z,ae=He*Ve-ee*it,Me=Oe*ee-Ie*He,Pe=it*Ie-Ve*Oe;if(s){if(ae<0||Me<0||Pe<0)return null}else if((ae<0||Me<0||Pe<0)&&(ae>0||Me>0||Pe>0))return null;let we=ae+Me+Pe;if(we===0)return null;let Ge=se*(ae*q+Me*Y+Pe*Z);return(we>0?Ge<0:Ge>0)?null:this.at(Ge/we,r)}applyMatrix4(e){return this.origin.applyMatrix4(e),this.direction.transformDirection(e),this}equals(e){return e.origin.equals(this.origin)&&e.direction.equals(this.direction)}clone(){return new this.constructor().copy(this)}},sn=class extends Ln{constructor(e){super(),this.isMeshBasicMaterial=!0,this.type="MeshBasicMaterial",this.color=new qe(16777215),this.map=null,this.lightMap=null,this.lightMapIntensity=1,this.aoMap=null,this.aoMapIntensity=1,this.specularMap=null,this.alphaMap=null,this.envMap=null,this.envMapRotation=new vn,this.combine=ho,this.reflectivity=1,this.refractionRatio=.98,this.wireframe=!1,this.wireframeLinewidth=1,this.wireframeLinecap="round",this.wireframeLinejoin="round",this.fog=!0,this.setValues(e)}copy(e){return super.copy(e),this.color.copy(e.color),this.map=e.map,this.lightMap=e.lightMap,this.lightMapIntensity=e.lightMapIntensity,this.aoMap=e.aoMap,this.aoMapIntensity=e.aoMapIntensity,this.specularMap=e.specularMap,this.alphaMap=e.alphaMap,this.envMap=e.envMap,this.envMapRotation.copy(e.envMapRotation),this.combine=e.combine,this.reflectivity=e.reflectivity,this.refractionRatio=e.refractionRatio,this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this.wireframeLinecap=e.wireframeLinecap,this.wireframeLinejoin=e.wireframeLinejoin,this.fog=e.fog,this}},iu=new ut,Pi=new Ui,ha=new Hn,su=new B,da=new B,fa=new B,pa=new B,Bl=new B,ma=new B,ru=new B,ga=new B,mt=class extends kt{constructor(e=new St,t=new sn){super(),this.isMesh=!0,this.type="Mesh",this.geometry=e,this.material=t,this.morphTargetDictionary=void 0,this.morphTargetInfluences=void 0,this.count=1,this.updateMorphTargets()}copy(e,t){return super.copy(e,t),e.morphTargetInfluences!==void 0&&(this.morphTargetInfluences=e.morphTargetInfluences.slice()),e.morphTargetDictionary!==void 0&&(this.morphTargetDictionary=Object.assign({},e.morphTargetDictionary)),this.material=Array.isArray(e.material)?e.material.slice():e.material,this.geometry=e.geometry,this}updateMorphTargets(){let t=this.geometry.morphAttributes,n=Object.keys(t);if(n.length>0){let s=t[n[0]];if(s!==void 0){this.morphTargetInfluences=[],this.morphTargetDictionary={};for(let r=0,a=s.length;r<a;r++){let o=s[r].name||String(r);this.morphTargetInfluences.push(0),this.morphTargetDictionary[o]=r}}}}getVertexPosition(e,t){let n=this.geometry,s=n.attributes.position,r=n.morphAttributes.position,a=n.morphTargetsRelative;t.fromBufferAttribute(s,e);let o=this.morphTargetInfluences;if(r&&o){ma.set(0,0,0);for(let l=0,c=r.length;l<c;l++){let h=o[l],f=r[l];h!==0&&(Bl.fromBufferAttribute(f,e),a?ma.addScaledVector(Bl,h):ma.addScaledVector(Bl.sub(t),h))}t.add(ma)}return t}intersectsFrustum(e){return e.intersectsObject(this)}raycast(e,t){let n=this.geometry,s=this.material,r=this.matrixWorld;s!==void 0&&(n.boundingSphere===null&&n.computeBoundingSphere(),ha.copy(n.boundingSphere),ha.applyMatrix4(r),Pi.copy(e.ray).recast(e.near),!(ha.containsPoint(Pi.origin)===!1&&(Pi.intersectSphere(ha,su)===null||Pi.origin.distanceToSquared(su)>(e.far-e.near)**2))&&(iu.copy(r).invert(),Pi.copy(e.ray).applyMatrix4(iu),!(n.boundingBox!==null&&Pi.intersectsBox(n.boundingBox)===!1)&&this._computeIntersections(e,t,Pi)))}_computeIntersections(e,t,n){let s,r=this.geometry,a=this.material,o=r.index,l=r.attributes.position,c=r.attributes.uv,h=r.attributes.uv1,f=r.attributes.normal,u=r.groups,d=r.drawRange;if(o!==null)if(Array.isArray(a))for(let _=0,S=u.length;_<S;_++){let g=u[_],p=a[g.materialIndex],w=Math.max(g.start,d.start),I=Math.min(o.count,Math.min(g.start+g.count,d.start+d.count));for(let y=w,A=I;y<A;y+=3){let E=o.getX(y),D=o.getX(y+1),v=o.getX(y+2);s=_a(this,p,e,n,c,h,f,E,D,v),s&&(s.faceIndex=Math.floor(y/3),s.face.materialIndex=g.materialIndex,t.push(s))}}else{let _=Math.max(0,d.start),S=Math.min(o.count,d.start+d.count);for(let g=_,p=S;g<p;g+=3){let w=o.getX(g),I=o.getX(g+1),y=o.getX(g+2);s=_a(this,a,e,n,c,h,f,w,I,y),s&&(s.faceIndex=Math.floor(g/3),t.push(s))}}else if(l!==void 0)if(Array.isArray(a))for(let _=0,S=u.length;_<S;_++){let g=u[_],p=a[g.materialIndex],w=Math.max(g.start,d.start),I=Math.min(l.count,Math.min(g.start+g.count,d.start+d.count));for(let y=w,A=I;y<A;y+=3){let E=y,D=y+1,v=y+2;s=_a(this,p,e,n,c,h,f,E,D,v),s&&(s.faceIndex=Math.floor(y/3),s.face.materialIndex=g.materialIndex,t.push(s))}}else{let _=Math.max(0,d.start),S=Math.min(l.count,d.start+d.count);for(let g=_,p=S;g<p;g+=3){let w=g,I=g+1,y=g+2;s=_a(this,a,e,n,c,h,f,w,I,y),s&&(s.faceIndex=Math.floor(g/3),t.push(s))}}}};function Fd(i,e,t,n,s,r,a,o){let l;if(e.side===Zt?l=n.intersectTriangle(a,r,s,!0,o):l=n.intersectTriangle(s,r,a,e.side===yi,o),l===null)return null;ga.copy(o),ga.applyMatrix4(i.matrixWorld);let c=t.ray.origin.distanceTo(ga);return c<t.near||c>t.far?null:{distance:c,point:ga.clone(),object:i}}function _a(i,e,t,n,s,r,a,o,l,c){i.getVertexPosition(o,da),i.getVertexPosition(l,fa),i.getVertexPosition(c,pa);let h=Fd(i,e,t,n,da,fa,pa,ru);if(h){let f=new B;pi.getBarycoord(ru,da,fa,pa,f),s&&(h.uv=pi.getInterpolatedAttribute(s,o,l,c,f,new De)),r&&(h.uv1=pi.getInterpolatedAttribute(r,o,l,c,f,new De)),a&&(h.normal=pi.getInterpolatedAttribute(a,o,l,c,f,new B),h.normal.dot(n.direction)>0&&h.normal.multiplyScalar(-1));let u={a:o,b:l,c,normal:new B,materialIndex:0};pi.getNormal(da,fa,pa,u.normal),h.face=u,h.barycoord=f}return h}var lr=class extends on{constructor(e=null,t=1,n=1,s,r,a,o,l,c=Gt,h=Gt,f,u){super(null,a,o,l,c,h,s,r,f,u),this.isDataTexture=!0,this.image={data:e,width:t,height:n},this.generateMipmaps=!1,this.flipY=!1,this.unpackAlignment=1}};var cr=class extends Xt{constructor(e,t,n,s=1){super(e,t,n),this.isInstancedBufferAttribute=!0,this.meshPerAttribute=s}copy(e){return super.copy(e),this.meshPerAttribute=e.meshPerAttribute,this}toJSON(){let e=super.toJSON();return e.meshPerAttribute=this.meshPerAttribute,e.isInstancedBufferAttribute=!0,e}},os=new ut,au=new ut,xa=[],ou=new Vn,kd=new ut,Xs=new mt,Ys=new Hn,ln=class extends mt{constructor(e,t,n){super(e,t),this.isInstancedMesh=!0,this.instanceMatrix=new cr(new Float32Array(n*16),16),this.instanceColor=null,this.morphTexture=null,this.count=n,this.boundingBox=null,this.boundingSphere=null;for(let s=0;s<n;s++)this.setMatrixAt(s,kd)}computeBoundingBox(){let e=this.geometry,t=this.count;this.boundingBox===null&&(this.boundingBox=new Vn),e.boundingBox===null&&e.computeBoundingBox(),this.boundingBox.makeEmpty();for(let n=0;n<t;n++)this.getMatrixAt(n,os),ou.copy(e.boundingBox).applyMatrix4(os),this.boundingBox.union(ou)}computeBoundingSphere(){let e=this.geometry,t=this.count;this.boundingSphere===null&&(this.boundingSphere=new Hn),e.boundingSphere===null&&e.computeBoundingSphere(),this.boundingSphere.makeEmpty();for(let n=0;n<t;n++)this.getMatrixAt(n,os),Ys.copy(e.boundingSphere).applyMatrix4(os),this.boundingSphere.union(Ys)}copy(e,t){return super.copy(e,t),this.instanceMatrix.copy(e.instanceMatrix),e.morphTexture!==null&&(this.morphTexture=e.morphTexture.clone()),e.instanceColor!==null&&(this.instanceColor=e.instanceColor.clone()),this.count=e.count,e.boundingBox!==null&&(this.boundingBox=e.boundingBox.clone()),e.boundingSphere!==null&&(this.boundingSphere=e.boundingSphere.clone()),this}getColorAt(e,t){return this.instanceColor===null?t.setRGB(1,1,1):t.fromArray(this.instanceColor.array,e*3)}getMatrixAt(e,t){return t.fromArray(this.instanceMatrix.array,e*16)}getMorphAt(e,t){let n=t.morphTargetInfluences,s=this.morphTexture.source.data.data,r=n.length+1,a=e*r+1;for(let o=0;o<n.length;o++)n[o]=s[a+o]}raycast(e,t){let n=this.matrixWorld,s=this.count;if(Xs.geometry=this.geometry,Xs.material=this.material,Xs.material!==void 0&&(this.boundingSphere===null&&this.computeBoundingSphere(),Ys.copy(this.boundingSphere),Ys.applyMatrix4(n),e.ray.intersectsSphere(Ys)!==!1))for(let r=0;r<s;r++){this.getMatrixAt(r,os),au.multiplyMatrices(n,os),Xs.matrixWorld=au,Xs.raycast(e,xa);for(let a=0,o=xa.length;a<o;a++){let l=xa[a];l.instanceId=r,l.object=this,t.push(l)}xa.length=0}}setColorAt(e,t){return this.instanceColor===null&&(this.instanceColor=new cr(new Float32Array(this.instanceMatrix.count*3).fill(1),3)),t.toArray(this.instanceColor.array,e*3),this}setMatrixAt(e,t){return t.toArray(this.instanceMatrix.array,e*16),this}setMorphAt(e,t){let n=t.morphTargetInfluences,s=n.length+1;this.morphTexture===null&&(this.morphTexture=new lr(new Float32Array(s*this.count),s,this.count,vo,Sn));let r=this.morphTexture.source.data.data,a=0;for(let c=0;c<n.length;c++)a+=n[c];let o=this.geometry.morphTargetsRelative?1:1-a,l=s*e;return r[l]=o,r.set(n,l+1),this}updateMorphTargets(){}dispose(){super.dispose(),this.morphTexture!==null&&(this.morphTexture.dispose(),this.morphTexture=null)}},Li=new Hn,Od=new De(.5,.5),va=new B,ys=class{constructor(e=new In,t=new In,n=new In,s=new In,r=new In,a=new In){this.planes=[e,t,n,s,r,a]}set(e,t,n,s,r,a){let o=this.planes;return o[0].copy(e),o[1].copy(t),o[2].copy(n),o[3].copy(s),o[4].copy(r),o[5].copy(a),this}copy(e){let t=this.planes;for(let n=0;n<6;n++)t[n].copy(e.planes[n]);return this}setFromProjectionMatrix(e,t=Pn,n=!1){let s=this.planes,r=e.elements,a=r[0],o=r[1],l=r[2],c=r[3],h=r[4],f=r[5],u=r[6],d=r[7],_=r[8],S=r[9],g=r[10],p=r[11],w=r[12],I=r[13],y=r[14],A=r[15];if(s[0].setComponents(c-a,d-h,p-_,A-w).normalize(),s[1].setComponents(c+a,d+h,p+_,A+w).normalize(),s[2].setComponents(c+o,d+f,p+S,A+I).normalize(),s[3].setComponents(c-o,d-f,p-S,A-I).normalize(),n)s[4].setComponents(l,u,g,y).normalize(),s[5].setComponents(c-l,d-u,p-g,A-y).normalize();else if(s[4].setComponents(c-l,d-u,p-g,A-y).normalize(),t===Pn)s[5].setComponents(c+l,d+u,p+g,A+y).normalize();else if(t===ps)s[5].setComponents(l,u,g,y).normalize();else throw new Error("THREE.Frustum.setFromProjectionMatrix(): Invalid coordinate system: "+t);return this}intersectsObject(e){if(e.boundingSphere!==void 0)e.boundingSphere===null&&e.computeBoundingSphere(),Li.copy(e.boundingSphere).applyMatrix4(e.matrixWorld);else{let t=e.geometry;t.boundingSphere===null&&t.computeBoundingSphere(),Li.copy(t.boundingSphere).applyMatrix4(e.matrixWorld)}return this.intersectsSphere(Li)}intersectsSprite(e){Li.center.set(0,0,0);let t=Od.distanceTo(e.center);return Li.radius=.7071067811865476+t,Li.applyMatrix4(e.matrixWorld),this.intersectsSphere(Li)}intersectsSphere(e){let t=this.planes,n=e.center,s=-e.radius;for(let r=0;r<6;r++)if(t[r].distanceToPoint(n)<s)return!1;return!0}intersectsBox(e){let t=this.planes;for(let n=0;n<6;n++){let s=t[n];if(va.x=s.normal.x>0?e.max.x:e.min.x,va.y=s.normal.y>0?e.max.y:e.min.y,va.z=s.normal.z>0?e.max.z:e.min.z,s.distanceToPoint(va)<0)return!1}return!0}containsPoint(e){let t=this.planes;for(let n=0;n<6;n++)if(t[n].distanceToPoint(e)<0)return!1;return!0}clone(){return new this.constructor().copy(this)}};var Qn=class extends Ln{constructor(e){super(),this.isLineBasicMaterial=!0,this.type="LineBasicMaterial",this.color=new qe(16777215),this.map=null,this.linewidth=1,this.linecap="round",this.linejoin="round",this.fog=!0,this.setValues(e)}copy(e){return super.copy(e),this.color.copy(e.color),this.map=e.map,this.linewidth=e.linewidth,this.linecap=e.linecap,this.linejoin=e.linejoin,this.fog=e.fog,this}},Va=new B,Ha=new B,lu=new ut,Zs=new Ui,ya=new Hn,zl=new B,cu=new B,Fi=class extends kt{constructor(e=new St,t=new Qn){super(),this.isLine=!0,this.type="Line",this.geometry=e,this.material=t,this.morphTargetDictionary=void 0,this.morphTargetInfluences=void 0,this.updateMorphTargets()}copy(e,t){return super.copy(e,t),this.material=Array.isArray(e.material)?e.material.slice():e.material,this.geometry=e.geometry,this}computeLineDistances(){let e=this.geometry;if(e.index===null){let t=e.attributes.position,n=[0];for(let s=1,r=t.count;s<r;s++)Va.fromBufferAttribute(t,s-1),Ha.fromBufferAttribute(t,s),n[s]=n[s-1],n[s]+=Va.distanceTo(Ha);e.setAttribute("lineDistance",new pt(n,1))}else $e("Line.computeLineDistances(): Computation only possible with non-indexed BufferGeometry.");return this}intersectsFrustum(e){return e.intersectsObject(this)}raycast(e,t){let n=this.geometry,s=this.matrixWorld,r=e.params.Line.threshold,a=n.drawRange;if(n.boundingSphere===null&&n.computeBoundingSphere(),ya.copy(n.boundingSphere),ya.applyMatrix4(s),ya.radius+=r,e.ray.intersectsSphere(ya)===!1)return;lu.copy(s).invert(),Zs.copy(e.ray).applyMatrix4(lu);let o=r/((this.scale.x+this.scale.y+this.scale.z)/3),l=o*o,c=this.isLineSegments?2:1,h=n.index,u=n.attributes.position;if(h!==null){let d=Math.max(0,a.start),_=Math.min(h.count,a.start+a.count);for(let S=d,g=_-1;S<g;S+=c){let p=h.getX(S),w=h.getX(S+1),I=ba(this,e,Zs,l,p,w,S);I&&t.push(I)}if(this.isLineLoop){let S=h.getX(_-1),g=h.getX(d),p=ba(this,e,Zs,l,S,g,_-1);p&&t.push(p)}}else{let d=Math.max(0,a.start),_=Math.min(u.count,a.start+a.count);for(let S=d,g=_-1;S<g;S+=c){let p=ba(this,e,Zs,l,S,S+1,S);p&&t.push(p)}if(this.isLineLoop){let S=ba(this,e,Zs,l,_-1,d,_-1);S&&t.push(S)}}}updateMorphTargets(){let t=this.geometry.morphAttributes,n=Object.keys(t);if(n.length>0){let s=t[n[0]];if(s!==void 0){this.morphTargetInfluences=[],this.morphTargetDictionary={};for(let r=0,a=s.length;r<a;r++){let o=s[r].name||String(r);this.morphTargetInfluences.push(0),this.morphTargetDictionary[o]=r}}}}};function ba(i,e,t,n,s,r,a){let o=i.geometry.attributes.position;if(Va.fromBufferAttribute(o,s),Ha.fromBufferAttribute(o,r),t.distanceSqToSegment(Va,Ha,zl,cu)>n)return;zl.applyMatrix4(i.matrixWorld);let c=e.ray.origin.distanceTo(zl);if(!(c<e.near||c>e.far))return{distance:c,point:cu.clone().applyMatrix4(i.matrixWorld),index:a,face:null,faceIndex:null,barycoord:null,object:i}}var ur=class extends Fi{constructor(e,t){super(e,t),this.isLineLoop=!0,this.type="LineLoop"}},bs=class extends Ln{constructor(e){super(),this.isPointsMaterial=!0,this.type="PointsMaterial",this.color=new qe(16777215),this.map=null,this.alphaMap=null,this.size=1,this.sizeAttenuation=!0,this.fog=!0,this.setValues(e)}copy(e){return super.copy(e),this.color.copy(e.color),this.map=e.map,this.alphaMap=e.alphaMap,this.size=e.size,this.sizeAttenuation=e.sizeAttenuation,this.fog=e.fog,this}},uu=new ut,jl=new Ui,Ma=new Hn,Sa=new B,hr=class extends kt{constructor(e=new St,t=new bs){super(),this.isPoints=!0,this.type="Points",this.geometry=e,this.material=t,this.morphTargetDictionary=void 0,this.morphTargetInfluences=void 0,this.updateMorphTargets()}copy(e,t){return super.copy(e,t),this.material=Array.isArray(e.material)?e.material.slice():e.material,this.geometry=e.geometry,this}intersectsFrustum(e){return e.intersectsObject(this)}raycast(e,t){let n=this.geometry,s=this.matrixWorld,r=e.params.Points.threshold,a=n.drawRange;if(n.boundingSphere===null&&n.computeBoundingSphere(),Ma.copy(n.boundingSphere),Ma.applyMatrix4(s),Ma.radius+=r,e.ray.intersectsSphere(Ma)===!1)return;uu.copy(s).invert(),jl.copy(e.ray).applyMatrix4(uu);let o=r/((this.scale.x+this.scale.y+this.scale.z)/3),l=o*o,c=n.index,f=n.attributes.position;if(c!==null){let u=Math.max(0,a.start),d=Math.min(c.count,a.start+a.count);for(let _=u,S=d;_<S;_++){let g=c.getX(_);Sa.fromBufferAttribute(f,g),hu(Sa,g,l,s,e,t,this)}}else{let u=Math.max(0,a.start),d=Math.min(f.count,a.start+a.count);for(let _=u,S=d;_<S;_++)Sa.fromBufferAttribute(f,_),hu(Sa,_,l,s,e,t,this)}}updateMorphTargets(){let t=this.geometry.morphAttributes,n=Object.keys(t);if(n.length>0){let s=t[n[0]];if(s!==void 0){this.morphTargetInfluences=[],this.morphTargetDictionary={};for(let r=0,a=s.length;r<a;r++){let o=s[r].name||String(r);this.morphTargetInfluences.push(0),this.morphTargetDictionary[o]=r}}}}};function hu(i,e,t,n,s,r,a){let o=jl.distanceSqToPoint(i);if(o<t){let l=new B;jl.closestPointToPoint(i,l),l.applyMatrix4(n);let c=s.ray.origin.distanceTo(l);if(c<s.near||c>s.far)return;r.push({distance:c,distanceToRay:Math.sqrt(o),point:l,index:e,face:null,faceIndex:null,barycoord:null,object:a})}}var dr=class extends on{constructor(e=[],t=bi,n,s,r,a,o,l,c,h){super(e,t,n,s,r,a,o,l,c,h),this.isCubeTexture=!0,this.flipY=!1}get images(){return this.image}set images(e){this.image=e}};var mi=class extends on{constructor(e,t,n=Un,s,r,a,o=Gt,l=Gt,c,h=Bn,f=1){if(h!==Bn&&h!==Si)throw new Error("THREE.DepthTexture: format must be either THREE.DepthFormat or THREE.DepthStencilFormat");let u={width:e,height:t,depth:f};super(u,s,r,a,o,l,h,n,c),this.isDepthTexture=!0,this.flipY=!1,this.generateMipmaps=!1,this.compareFunction=null}copy(e){return super.copy(e),this.source=new _s(Object.assign({},e.image)),this.compareFunction=e.compareFunction,this}toJSON(e){let t=super.toJSON(e);return t.compareFunction=this.compareFunction,t}},Ga=class extends mi{constructor(e,t=Un,n=bi,s,r,a=Gt,o=Gt,l,c=Bn){let h={width:e,height:e,depth:1},f=[h,h,h,h,h,h];super(e,e,t,n,s,r,a,o,l,c),this.image=f,this.isCubeDepthTexture=!0,this.isCubeTexture=!0}get images(){return this.image}set images(e){this.image=e}},fr=class extends on{constructor(e=null){super(),this.sourceTexture=e,this.isExternalTexture=!0}copy(e){return super.copy(e),this.sourceTexture=e.sourceTexture,this}},Nn=class i extends St{constructor(e=1,t=1,n=1,s=1,r=1,a=1){super(),this.type="BoxGeometry",this.parameters={width:e,height:t,depth:n,widthSegments:s,heightSegments:r,depthSegments:a};let o=this;s=Math.floor(s),r=Math.floor(r),a=Math.floor(a);let l=[],c=[],h=[],f=[],u=0,d=0;_("z","y","x",-1,-1,n,t,e,a,r,0),_("z","y","x",1,-1,n,t,-e,a,r,1),_("x","z","y",1,1,e,n,t,s,a,2),_("x","z","y",1,-1,e,n,-t,s,a,3),_("x","y","z",1,-1,e,t,n,s,r,4),_("x","y","z",-1,-1,e,t,-n,s,r,5),this.setIndex(l),this.setAttribute("position",new pt(c,3)),this.setAttribute("normal",new pt(h,3)),this.setAttribute("uv",new pt(f,2));function _(S,g,p,w,I,y,A,E,D,v,C){let O=y/D,V=A/v,q=y/2,j=A/2,z=E/2,Y=D+1,te=v+1,re=0,Z=0,Q=new B;for(let le=0;le<te;le++){let se=le*V-j;for(let Oe=0;Oe<Y;Oe++){let Ie=Oe*O-q;Q[S]=Ie*w,Q[g]=se*I,Q[p]=z,c.push(Q.x,Q.y,Q.z),Q[S]=0,Q[g]=0,Q[p]=E>0?1:-1,h.push(Q.x,Q.y,Q.z),f.push(Oe/D),f.push(1-le/v),re+=1}}for(let le=0;le<v;le++)for(let se=0;se<D;se++){let Oe=u+se+Y*le,Ie=u+se+Y*(le+1),it=u+(se+1)+Y*(le+1),Ve=u+(se+1)+Y*le;l.push(Oe,Ie,Ve),l.push(Ie,it,Ve),Z+=6}o.addGroup(d,Z,C),d+=Z,u+=re}}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}static fromJSON(e){return new i(e.width,e.height,e.depth,e.widthSegments,e.heightSegments,e.depthSegments)}};var Gn=class i extends St{constructor(e=1,t=1,n=1,s=32,r=1,a=!1,o=0,l=Math.PI*2){super(),this.type="CylinderGeometry",this.parameters={radiusTop:e,radiusBottom:t,height:n,radialSegments:s,heightSegments:r,openEnded:a,thetaStart:o,thetaLength:l};let c=this;s=Math.floor(s),r=Math.floor(r);let h=[],f=[],u=[],d=[],_=0,S=[],g=n/2,p=0;w(),a===!1&&(e>0&&I(!0),t>0&&I(!1)),this.setIndex(h),this.setAttribute("position",new pt(f,3)),this.setAttribute("normal",new pt(u,3)),this.setAttribute("uv",new pt(d,2));function w(){let y=new B,A=new B,E=0,D=(t-e)/n;for(let v=0;v<=r;v++){let C=[],O=v/r,V=O*(t-e)+e;for(let q=0;q<=s;q++){let j=q/s,z=j*l+o,Y=Math.sin(z),te=Math.cos(z);A.x=V*Y,A.y=-O*n+g,A.z=V*te,f.push(A.x,A.y,A.z),y.set(Y,D,te).normalize(),u.push(y.x,y.y,y.z),d.push(j,1-O),C.push(_++)}S.push(C)}for(let v=0;v<s;v++)for(let C=0;C<r;C++){let O=S[C][v],V=S[C+1][v],q=S[C+1][v+1],j=S[C][v+1];(e>0||C!==0)&&(h.push(O,V,j),E+=3),(t>0||C!==r-1)&&(h.push(V,q,j),E+=3)}c.addGroup(p,E,0),p+=E}function I(y){let A=_,E=new De,D=new B,v=0,C=y===!0?e:t,O=y===!0?1:-1;for(let q=1;q<=s;q++)f.push(0,g*O,0),u.push(0,O,0),d.push(.5,.5),_++;let V=_;for(let q=0;q<=s;q++){let z=q/s*l+o,Y=Math.cos(z),te=Math.sin(z);D.x=C*te,D.y=g*O,D.z=C*Y,f.push(D.x,D.y,D.z),u.push(0,O,0),E.x=Y*.5+.5,E.y=te*.5*O+.5,d.push(E.x,E.y),_++}for(let q=0;q<s;q++){let j=A+q,z=V+q;y===!0?h.push(z,z+1,j):h.push(z+1,z,j),v+=3}c.addGroup(p,v,y===!0?1:2),p+=v}}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}static fromJSON(e){return new i(e.radiusTop,e.radiusBottom,e.height,e.radialSegments,e.heightSegments,e.openEnded,e.thetaStart,e.thetaLength)}},pr=class i extends Gn{constructor(e=1,t=1,n=32,s=1,r=!1,a=0,o=Math.PI*2){super(0,e,t,n,s,r,a,o),this.type="ConeGeometry",this.parameters={radius:e,height:t,radialSegments:n,heightSegments:s,openEnded:r,thetaStart:a,thetaLength:o}}static fromJSON(e){return new i(e.radius,e.height,e.radialSegments,e.heightSegments,e.openEnded,e.thetaStart,e.thetaLength)}},Ms=class i extends St{constructor(e=[],t=[],n=1,s=0){super(),this.type="PolyhedronGeometry",this.parameters={vertices:e,indices:t,radius:n,detail:s};let r=[],a=[];o(s),c(n),h(),this.setAttribute("position",new pt(r,3)),this.setAttribute("normal",new pt(r.slice(),3)),this.setAttribute("uv",new pt(a,2)),s===0?this.computeVertexNormals():this.normalizeNormals();function o(w){let I=new B,y=new B,A=new B;for(let E=0;E<t.length;E+=3)d(t[E+0],I),d(t[E+1],y),d(t[E+2],A),l(I,y,A,w)}function l(w,I,y,A){let E=A+1,D=[];for(let v=0;v<=E;v++){D[v]=[];let C=w.clone().lerp(y,v/E),O=I.clone().lerp(y,v/E),V=E-v;for(let q=0;q<=V;q++)q===0&&v===E?D[v][q]=C:D[v][q]=C.clone().lerp(O,q/V)}for(let v=0;v<E;v++)for(let C=0;C<2*(E-v)-1;C++){let O=Math.floor(C/2);C%2===0?(u(D[v][O+1]),u(D[v+1][O]),u(D[v][O])):(u(D[v][O+1]),u(D[v+1][O+1]),u(D[v+1][O]))}}function c(w){let I=new B;for(let y=0;y<r.length;y+=3)I.x=r[y+0],I.y=r[y+1],I.z=r[y+2],I.normalize().multiplyScalar(w),r[y+0]=I.x,r[y+1]=I.y,r[y+2]=I.z}function h(){let w=new B;for(let I=0;I<r.length;I+=3){w.x=r[I+0],w.y=r[I+1],w.z=r[I+2];let y=g(w)/2/Math.PI+.5,A=p(w)/Math.PI+.5;a.push(y,1-A)}_(),f()}function f(){for(let w=0;w<a.length;w+=6){let I=a[w+0],y=a[w+2],A=a[w+4],E=Math.max(I,y,A),D=Math.min(I,y,A);E>.9&&D<.1&&(I<.2&&(a[w+0]+=1),y<.2&&(a[w+2]+=1),A<.2&&(a[w+4]+=1))}}function u(w){r.push(w.x,w.y,w.z)}function d(w,I){let y=w*3;I.x=e[y+0],I.y=e[y+1],I.z=e[y+2]}function _(){let w=new B,I=new B,y=new B,A=new B,E=new De,D=new De,v=new De;for(let C=0,O=0;C<r.length;C+=9,O+=6){w.set(r[C+0],r[C+1],r[C+2]),I.set(r[C+3],r[C+4],r[C+5]),y.set(r[C+6],r[C+7],r[C+8]),E.set(a[O+0],a[O+1]),D.set(a[O+2],a[O+3]),v.set(a[O+4],a[O+5]),A.copy(w).add(I).add(y).divideScalar(3);let V=g(A);S(E,O+0,w,V),S(D,O+2,I,V),S(v,O+4,y,V)}}function S(w,I,y,A){A<0&&w.x===1&&(a[I]=w.x-1),y.x===0&&y.z===0&&(a[I]=A/2/Math.PI+.5)}function g(w){return Math.atan2(w.z,-w.x)}function p(w){return Math.atan2(-w.y,Math.sqrt(w.x*w.x+w.z*w.z))}}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}static fromJSON(e){return new i(e.vertices,e.indices,e.radius,e.detail)}},mr=class i extends Ms{constructor(e=1,t=0){let n=(1+Math.sqrt(5))/2,s=1/n,r=[-1,-1,-1,-1,-1,1,-1,1,-1,-1,1,1,1,-1,-1,1,-1,1,1,1,-1,1,1,1,0,-s,-n,0,-s,n,0,s,-n,0,s,n,-s,-n,0,-s,n,0,s,-n,0,s,n,0,-n,0,-s,n,0,-s,-n,0,s,n,0,s],a=[3,11,7,3,7,15,3,15,13,7,19,17,7,17,6,7,6,15,17,4,8,17,8,10,17,10,6,8,0,16,8,16,2,8,2,10,0,12,1,0,1,18,0,18,16,6,10,2,6,2,13,6,13,15,2,16,18,2,18,3,2,3,13,18,1,9,18,9,11,18,11,3,4,14,12,4,12,0,4,0,8,11,9,5,11,5,19,11,19,7,19,5,14,19,14,4,19,4,17,1,12,14,1,14,5,1,5,9];super(r,a,e,t),this.type="DodecahedronGeometry",this.parameters={radius:e,detail:t}}static fromJSON(e){return new i(e.radius,e.detail)}};var yn=class{constructor(){this.type="Curve",this.arcLengthDivisions=200,this.needsUpdate=!1,this.cacheArcLengths=null}getPoint(){$e("Curve: .getPoint() not implemented.")}getPointAt(e,t){let n=this.getUtoTmapping(e);return this.getPoint(n,t)}getPoints(e=5){let t=[];for(let n=0;n<=e;n++)t.push(this.getPoint(n/e));return t}getSpacedPoints(e=5){let t=[];for(let n=0;n<=e;n++)t.push(this.getPointAt(n/e));return t}getLength(){let e=this.getLengths();return e[e.length-1]}getLengths(e=this.arcLengthDivisions){if(this.cacheArcLengths&&this.cacheArcLengths.length===e+1&&!this.needsUpdate)return this.cacheArcLengths;this.needsUpdate=!1;let t=[],n,s=this.getPoint(0),r=0;t.push(0);for(let a=1;a<=e;a++)n=this.getPoint(a/e),r+=n.distanceTo(s),t.push(r),s=n;return this.cacheArcLengths=t,t}updateArcLengths(){this.needsUpdate=!0,this.getLengths()}getUtoTmapping(e,t=null){let n=this.getLengths(),s=0,r=n.length,a;t?a=t:a=e*n[r-1];let o=0,l=r-1,c;for(;o<=l;)if(s=Math.floor(o+(l-o)/2),c=n[s]-a,c<0)o=s+1;else if(c>0)l=s-1;else{l=s;break}if(s=l,n[s]===a)return s/(r-1);let h=n[s],u=n[s+1]-h,d=(a-h)/u;return(s+d)/(r-1)}getTangent(e,t){let s=e-1e-4,r=e+1e-4;s<0&&(s=0),r>1&&(r=1);let a=this.getPoint(s),o=this.getPoint(r),l=t||(a.isVector2?new De:new B);return l.copy(o).sub(a).normalize(),l}getTangentAt(e,t){let n=this.getUtoTmapping(e);return this.getTangent(n,t)}computeFrenetFrames(e,t=!1){let n=new B,s=[],r=[],a=[],o=new B,l=new ut;for(let d=0;d<=e;d++){let _=d/e;s[d]=this.getTangentAt(_,new B)}r[0]=new B,a[0]=new B;let c=Number.MAX_VALUE,h=Math.abs(s[0].x),f=Math.abs(s[0].y),u=Math.abs(s[0].z);h<=c&&(c=h,n.set(1,0,0)),f<=c&&(c=f,n.set(0,1,0)),u<=c&&n.set(0,0,1),o.crossVectors(s[0],n).normalize(),r[0].crossVectors(s[0],o),a[0].crossVectors(s[0],r[0]);for(let d=1;d<=e;d++){if(r[d]=r[d-1].clone(),a[d]=a[d-1].clone(),o.crossVectors(s[d-1],s[d]),o.length()>Number.EPSILON){o.normalize();let _=Math.acos(ot(s[d-1].dot(s[d]),-1,1));r[d].applyMatrix4(l.makeRotationAxis(o,_))}a[d].crossVectors(s[d],r[d])}if(t===!0){let d=Math.acos(ot(r[0].dot(r[e]),-1,1));d/=e,s[0].dot(o.crossVectors(r[0],r[e]))>0&&(d=-d);for(let _=1;_<=e;_++)r[_].applyMatrix4(l.makeRotationAxis(s[_],d*_)),a[_].crossVectors(s[_],r[_])}return{tangents:s,normals:r,binormals:a}}clone(){return new this.constructor().copy(this)}copy(e){return this.arcLengthDivisions=e.arcLengthDivisions,this}toJSON(){let e={metadata:{version:4.7,type:"Curve",generator:"Curve.toJSON"}};return e.arcLengthDivisions=this.arcLengthDivisions,e.type=this.type,e}fromJSON(e){return this.arcLengthDivisions=e.arcLengthDivisions,this}},gr=class extends yn{constructor(e=0,t=0,n=1,s=1,r=0,a=Math.PI*2,o=!1,l=0){super(),this.isEllipseCurve=!0,this.type="EllipseCurve",this.aX=e,this.aY=t,this.xRadius=n,this.yRadius=s,this.aStartAngle=r,this.aEndAngle=a,this.aClockwise=o,this.aRotation=l}getPoint(e,t=new De){let n=t,s=Math.PI*2,r=this.aEndAngle-this.aStartAngle,a=Math.abs(r)<Number.EPSILON;for(;r<0;)r+=s;for(;r>s;)r-=s;r<Number.EPSILON&&(a?r=0:r=s),this.aClockwise===!0&&!a&&(r===s?r=-s:r=r-s);let o=this.aStartAngle+e*r,l=this.aX+this.xRadius*Math.cos(o),c=this.aY+this.yRadius*Math.sin(o);if(this.aRotation!==0){let h=Math.cos(this.aRotation),f=Math.sin(this.aRotation),u=l-this.aX,d=c-this.aY;l=u*h-d*f+this.aX,c=u*f+d*h+this.aY}return n.set(l,c)}copy(e){return super.copy(e),this.aX=e.aX,this.aY=e.aY,this.xRadius=e.xRadius,this.yRadius=e.yRadius,this.aStartAngle=e.aStartAngle,this.aEndAngle=e.aEndAngle,this.aClockwise=e.aClockwise,this.aRotation=e.aRotation,this}toJSON(){let e=super.toJSON();return e.aX=this.aX,e.aY=this.aY,e.xRadius=this.xRadius,e.yRadius=this.yRadius,e.aStartAngle=this.aStartAngle,e.aEndAngle=this.aEndAngle,e.aClockwise=this.aClockwise,e.aRotation=this.aRotation,e}fromJSON(e){return super.fromJSON(e),this.aX=e.aX,this.aY=e.aY,this.xRadius=e.xRadius,this.yRadius=e.yRadius,this.aStartAngle=e.aStartAngle,this.aEndAngle=e.aEndAngle,this.aClockwise=e.aClockwise,this.aRotation=e.aRotation,this}},Wa=class extends gr{constructor(e,t,n,s,r,a){super(e,t,n,n,s,r,a),this.isArcCurve=!0,this.type="ArcCurve"}};function xc(){let i=0,e=0,t=0,n=0;function s(r,a,o,l){i=r,e=o,t=-3*r+3*a-2*o-l,n=2*r-2*a+o+l}return{initCatmullRom:function(r,a,o,l,c){s(a,o,c*(o-r),c*(l-a))},initNonuniformCatmullRom:function(r,a,o,l,c,h,f){let u=(a-r)/c-(o-r)/(c+h)+(o-a)/h,d=(o-a)/h-(l-a)/(h+f)+(l-o)/f;u*=h,d*=h,s(a,o,u,d)},calc:function(r){let a=r*r,o=a*r;return i+e*r+t*a+n*o}}}var du=new B,fu=new B,Vl=new xc,Hl=new xc,Gl=new xc,Ss=class extends yn{constructor(e=[],t=!1,n="centripetal",s=.5){super(),this.isCatmullRomCurve3=!0,this.type="CatmullRomCurve3",this.points=e,this.closed=t,this.curveType=n,this.tension=s}getPoint(e,t=new B){let n=t,s=this.points,r=s.length,a=(r-(this.closed?0:1))*e,o=Math.floor(a),l=a-o;this.closed?o+=o>0?0:(Math.floor(Math.abs(o)/r)+1)*r:l===0&&o===r-1&&(o=r-2,l=1);let c,h;this.closed||o>0?c=s[(o-1)%r]:(fu.subVectors(s[0],s[1]).add(s[0]),c=fu);let f=s[o%r],u=s[(o+1)%r];if(this.closed||o+2<r?h=s[(o+2)%r]:(du.subVectors(s[r-1],s[r-2]).add(s[r-1]),h=du),this.curveType==="centripetal"||this.curveType==="chordal"){let d=this.curveType==="chordal"?.5:.25,_=Math.pow(c.distanceToSquared(f),d),S=Math.pow(f.distanceToSquared(u),d),g=Math.pow(u.distanceToSquared(h),d);S<1e-4&&(S=1),_<1e-4&&(_=S),g<1e-4&&(g=S),Vl.initNonuniformCatmullRom(c.x,f.x,u.x,h.x,_,S,g),Hl.initNonuniformCatmullRom(c.y,f.y,u.y,h.y,_,S,g),Gl.initNonuniformCatmullRom(c.z,f.z,u.z,h.z,_,S,g)}else this.curveType==="catmullrom"&&(Vl.initCatmullRom(c.x,f.x,u.x,h.x,this.tension),Hl.initCatmullRom(c.y,f.y,u.y,h.y,this.tension),Gl.initCatmullRom(c.z,f.z,u.z,h.z,this.tension));return n.set(Vl.calc(l),Hl.calc(l),Gl.calc(l)),n}copy(e){super.copy(e),this.points=[];for(let t=0,n=e.points.length;t<n;t++){let s=e.points[t];this.points.push(s.clone())}return this.closed=e.closed,this.curveType=e.curveType,this.tension=e.tension,this}toJSON(){let e=super.toJSON();e.points=[];for(let t=0,n=this.points.length;t<n;t++){let s=this.points[t];e.points.push(s.toArray())}return e.closed=this.closed,e.curveType=this.curveType,e.tension=this.tension,e}fromJSON(e){super.fromJSON(e),this.points=[];for(let t=0,n=e.points.length;t<n;t++){let s=e.points[t];this.points.push(new B().fromArray(s))}return this.closed=e.closed,this.curveType=e.curveType,this.tension=e.tension,this}};function pu(i,e,t,n,s){let r=(n-e)*.5,a=(s-t)*.5,o=i*i,l=i*o;return(2*t-2*n+r+a)*l+(-3*t+3*n-2*r-a)*o+r*i+t}function Bd(i,e){let t=1-i;return t*t*e}function zd(i,e){return 2*(1-i)*i*e}function Vd(i,e){return i*i*e}function Ks(i,e,t,n){return Bd(i,e)+zd(i,t)+Vd(i,n)}function Hd(i,e){let t=1-i;return t*t*t*e}function Gd(i,e){let t=1-i;return 3*t*t*i*e}function Wd(i,e){return 3*(1-i)*i*i*e}function $d(i,e){return i*i*i*e}function Qs(i,e,t,n,s){return Hd(i,e)+Gd(i,t)+Wd(i,n)+$d(i,s)}var $a=class extends yn{constructor(e=new De,t=new De,n=new De,s=new De){super(),this.isCubicBezierCurve=!0,this.type="CubicBezierCurve",this.v0=e,this.v1=t,this.v2=n,this.v3=s}getPoint(e,t=new De){let n=t,s=this.v0,r=this.v1,a=this.v2,o=this.v3;return n.set(Qs(e,s.x,r.x,a.x,o.x),Qs(e,s.y,r.y,a.y,o.y)),n}copy(e){return super.copy(e),this.v0.copy(e.v0),this.v1.copy(e.v1),this.v2.copy(e.v2),this.v3.copy(e.v3),this}toJSON(){let e=super.toJSON();return e.v0=this.v0.toArray(),e.v1=this.v1.toArray(),e.v2=this.v2.toArray(),e.v3=this.v3.toArray(),e}fromJSON(e){return super.fromJSON(e),this.v0.fromArray(e.v0),this.v1.fromArray(e.v1),this.v2.fromArray(e.v2),this.v3.fromArray(e.v3),this}},qa=class extends yn{constructor(e=new B,t=new B,n=new B,s=new B){super(),this.isCubicBezierCurve3=!0,this.type="CubicBezierCurve3",this.v0=e,this.v1=t,this.v2=n,this.v3=s}getPoint(e,t=new B){let n=t,s=this.v0,r=this.v1,a=this.v2,o=this.v3;return n.set(Qs(e,s.x,r.x,a.x,o.x),Qs(e,s.y,r.y,a.y,o.y),Qs(e,s.z,r.z,a.z,o.z)),n}copy(e){return super.copy(e),this.v0.copy(e.v0),this.v1.copy(e.v1),this.v2.copy(e.v2),this.v3.copy(e.v3),this}toJSON(){let e=super.toJSON();return e.v0=this.v0.toArray(),e.v1=this.v1.toArray(),e.v2=this.v2.toArray(),e.v3=this.v3.toArray(),e}fromJSON(e){return super.fromJSON(e),this.v0.fromArray(e.v0),this.v1.fromArray(e.v1),this.v2.fromArray(e.v2),this.v3.fromArray(e.v3),this}},Xa=class extends yn{constructor(e=new De,t=new De){super(),this.isLineCurve=!0,this.type="LineCurve",this.v1=e,this.v2=t}getPoint(e,t=new De){let n=t;return e===1?n.copy(this.v2):(n.copy(this.v2).sub(this.v1),n.multiplyScalar(e).add(this.v1)),n}getPointAt(e,t){return this.getPoint(e,t)}getTangent(e,t=new De){return t.subVectors(this.v2,this.v1).normalize()}getTangentAt(e,t){return this.getTangent(e,t)}copy(e){return super.copy(e),this.v1.copy(e.v1),this.v2.copy(e.v2),this}toJSON(){let e=super.toJSON();return e.v1=this.v1.toArray(),e.v2=this.v2.toArray(),e}fromJSON(e){return super.fromJSON(e),this.v1.fromArray(e.v1),this.v2.fromArray(e.v2),this}},Ya=class extends yn{constructor(e=new B,t=new B){super(),this.isLineCurve3=!0,this.type="LineCurve3",this.v1=e,this.v2=t}getPoint(e,t=new B){let n=t;return e===1?n.copy(this.v2):(n.copy(this.v2).sub(this.v1),n.multiplyScalar(e).add(this.v1)),n}getPointAt(e,t){return this.getPoint(e,t)}getTangent(e,t=new B){return t.subVectors(this.v2,this.v1).normalize()}getTangentAt(e,t){return this.getTangent(e,t)}copy(e){return super.copy(e),this.v1.copy(e.v1),this.v2.copy(e.v2),this}toJSON(){let e=super.toJSON();return e.v1=this.v1.toArray(),e.v2=this.v2.toArray(),e}fromJSON(e){return super.fromJSON(e),this.v1.fromArray(e.v1),this.v2.fromArray(e.v2),this}},Za=class extends yn{constructor(e=new De,t=new De,n=new De){super(),this.isQuadraticBezierCurve=!0,this.type="QuadraticBezierCurve",this.v0=e,this.v1=t,this.v2=n}getPoint(e,t=new De){let n=t,s=this.v0,r=this.v1,a=this.v2;return n.set(Ks(e,s.x,r.x,a.x),Ks(e,s.y,r.y,a.y)),n}copy(e){return super.copy(e),this.v0.copy(e.v0),this.v1.copy(e.v1),this.v2.copy(e.v2),this}toJSON(){let e=super.toJSON();return e.v0=this.v0.toArray(),e.v1=this.v1.toArray(),e.v2=this.v2.toArray(),e}fromJSON(e){return super.fromJSON(e),this.v0.fromArray(e.v0),this.v1.fromArray(e.v1),this.v2.fromArray(e.v2),this}},ki=class extends yn{constructor(e=new B,t=new B,n=new B){super(),this.isQuadraticBezierCurve3=!0,this.type="QuadraticBezierCurve3",this.v0=e,this.v1=t,this.v2=n}getPoint(e,t=new B){let n=t,s=this.v0,r=this.v1,a=this.v2;return n.set(Ks(e,s.x,r.x,a.x),Ks(e,s.y,r.y,a.y),Ks(e,s.z,r.z,a.z)),n}copy(e){return super.copy(e),this.v0.copy(e.v0),this.v1.copy(e.v1),this.v2.copy(e.v2),this}toJSON(){let e=super.toJSON();return e.v0=this.v0.toArray(),e.v1=this.v1.toArray(),e.v2=this.v2.toArray(),e}fromJSON(e){return super.fromJSON(e),this.v0.fromArray(e.v0),this.v1.fromArray(e.v1),this.v2.fromArray(e.v2),this}},ja=class extends yn{constructor(e=[]){super(),this.isSplineCurve=!0,this.type="SplineCurve",this.points=e}getPoint(e,t=new De){let n=t,s=this.points,r=(s.length-1)*e,a=Math.floor(r),o=r-a,l=s[a===0?a:a-1],c=s[a],h=s[a>s.length-2?s.length-1:a+1],f=s[a>s.length-3?s.length-1:a+2];return n.set(pu(o,l.x,c.x,h.x,f.x),pu(o,l.y,c.y,h.y,f.y)),n}copy(e){super.copy(e),this.points=[];for(let t=0,n=e.points.length;t<n;t++){let s=e.points[t];this.points.push(s.clone())}return this}toJSON(){let e=super.toJSON();e.points=[];for(let t=0,n=this.points.length;t<n;t++){let s=this.points[t];e.points.push(s.toArray())}return e}fromJSON(e){super.fromJSON(e),this.points=[];for(let t=0,n=e.points.length;t<n;t++){let s=e.points[t];this.points.push(new De().fromArray(s))}return this}},qd=Object.freeze({__proto__:null,ArcCurve:Wa,CatmullRomCurve3:Ss,CubicBezierCurve:$a,CubicBezierCurve3:qa,EllipseCurve:gr,LineCurve:Xa,LineCurve3:Ya,QuadraticBezierCurve:Za,QuadraticBezierCurve3:ki,SplineCurve:ja});var Ts=class i extends Ms{constructor(e=1,t=0){let n=(1+Math.sqrt(5))/2,s=[-1,n,0,1,n,0,-1,-n,0,1,-n,0,0,-1,n,0,1,n,0,-1,-n,0,1,-n,n,0,-1,n,0,1,-n,0,-1,-n,0,1],r=[0,11,5,0,5,1,0,1,7,0,7,10,0,10,11,1,5,9,5,11,4,11,10,2,10,7,6,7,1,8,3,9,4,3,4,2,3,2,6,3,6,8,3,8,9,4,9,5,2,4,11,6,2,10,8,6,7,9,8,1];super(s,r,e,t),this.type="IcosahedronGeometry",this.parameters={radius:e,detail:t}}static fromJSON(e){return new i(e.radius,e.detail)}};var _r=class i extends Ms{constructor(e=1,t=0){let n=[1,0,0,-1,0,0,0,1,0,0,-1,0,0,0,1,0,0,-1],s=[0,2,4,0,4,3,0,3,5,0,5,2,1,2,5,1,5,3,1,3,4,1,4,2];super(n,s,e,t),this.type="OctahedronGeometry",this.parameters={radius:e,detail:t}}static fromJSON(e){return new i(e.radius,e.detail)}},xr=class i extends St{constructor(e=1,t=1,n=1,s=1){super(),this.type="PlaneGeometry",this.parameters={width:e,height:t,widthSegments:n,heightSegments:s};let r=e/2,a=t/2,o=Math.floor(n),l=Math.floor(s),c=o+1,h=l+1,f=e/o,u=t/l,d=[],_=[],S=[],g=[];for(let p=0;p<h;p++){let w=p*u-a;for(let I=0;I<c;I++){let y=I*f-r;_.push(y,-w,0),S.push(0,0,1),g.push(I/o),g.push(1-p/l)}}for(let p=0;p<l;p++)for(let w=0;w<o;w++){let I=w+c*p,y=w+c*(p+1),A=w+1+c*(p+1),E=w+1+c*p;d.push(I,y,E),d.push(y,A,E)}this.setIndex(d),this.setAttribute("position",new pt(_,3)),this.setAttribute("normal",new pt(S,3)),this.setAttribute("uv",new pt(g,2))}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}static fromJSON(e){return new i(e.width,e.height,e.widthSegments,e.heightSegments)}};var cn=class i extends St{constructor(e=1,t=32,n=16,s=0,r=Math.PI*2,a=0,o=Math.PI){super(),this.type="SphereGeometry",this.parameters={radius:e,widthSegments:t,heightSegments:n,phiStart:s,phiLength:r,thetaStart:a,thetaLength:o},t=Math.max(3,Math.floor(t)),n=Math.max(2,Math.floor(n));let l=Math.min(a+o,Math.PI),c=0,h=[],f=new B,u=new B,d=[],_=[],S=[],g=[];for(let p=0;p<=n;p++){let w=[],I=p/n,y=a+I*o,A=e*Math.cos(y),E=Math.sqrt(e*e-A*A),D=0;p===0&&a===0?D=.5/t:p===n&&l===Math.PI&&(D=-.5/t);for(let v=0;v<=t;v++){let C=v/t,O=s+C*r;f.x=-E*Math.cos(O),f.y=A,f.z=E*Math.sin(O),_.push(f.x,f.y,f.z),u.copy(f).normalize(),S.push(u.x,u.y,u.z),g.push(C+D,1-I),w.push(c++)}h.push(w)}for(let p=0;p<n;p++)for(let w=0;w<t;w++){let I=h[p][w+1],y=h[p][w],A=h[p+1][w],E=h[p+1][w+1];(p!==0||a>0)&&d.push(I,y,E),(p!==n-1||l<Math.PI)&&d.push(y,A,E)}this.setIndex(d),this.setAttribute("position",new pt(_,3)),this.setAttribute("normal",new pt(S,3)),this.setAttribute("uv",new pt(g,2))}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}static fromJSON(e){return new i(e.radius,e.widthSegments,e.heightSegments,e.phiStart,e.phiLength,e.thetaStart,e.thetaLength)}};var bn=class i extends St{constructor(e=1,t=.4,n=12,s=48,r=Math.PI*2,a=0,o=Math.PI*2){super(),this.type="TorusGeometry",this.parameters={radius:e,tube:t,radialSegments:n,tubularSegments:s,arc:r,thetaStart:a,thetaLength:o},n=Math.floor(n),s=Math.floor(s);let l=[],c=[],h=[],f=[],u=new B,d=new B,_=new B;for(let S=0;S<=n;S++){let g=a+S/n*o;for(let p=0;p<=s;p++){let w=p/s*r;d.x=(e+t*Math.cos(g))*Math.cos(w),d.y=(e+t*Math.cos(g))*Math.sin(w),d.z=t*Math.sin(g),c.push(d.x,d.y,d.z),u.x=e*Math.cos(w),u.y=e*Math.sin(w),_.subVectors(d,u).normalize(),h.push(_.x,_.y,_.z),f.push(p/s),f.push(S/n)}}for(let S=1;S<=n;S++)for(let g=1;g<=s;g++){let p=(s+1)*S+g-1,w=(s+1)*(S-1)+g-1,I=(s+1)*(S-1)+g,y=(s+1)*S+g;l.push(p,w,y),l.push(w,I,y)}this.setIndex(l),this.setAttribute("position",new pt(c,3)),this.setAttribute("normal",new pt(h,3)),this.setAttribute("uv",new pt(f,2))}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}static fromJSON(e){return new i(e.radius,e.tube,e.radialSegments,e.tubularSegments,e.arc,e.thetaStart,e.thetaLength)}};var vr=class i extends St{constructor(e=new ki(new B(-1,-1,0),new B(-1,1,0),new B(1,1,0)),t=64,n=1,s=8,r=!1){super(),this.type="TubeGeometry",this.parameters={path:e,tubularSegments:t,radius:n,radialSegments:s,closed:r};let a=e.computeFrenetFrames(t,r);this.tangents=a.tangents,this.normals=a.normals,this.binormals=a.binormals;let o=new B,l=new B,c=new De,h=new B,f=[],u=[],d=[],_=[];S(),this.setIndex(_),this.setAttribute("position",new pt(f,3)),this.setAttribute("normal",new pt(u,3)),this.setAttribute("uv",new pt(d,2));function S(){for(let I=0;I<t;I++)g(I);g(r===!1?t:0),w(),p()}function g(I){h=e.getPointAt(I/t,h);let y=a.normals[I],A=a.binormals[I];for(let E=0;E<=s;E++){let D=E/s*Math.PI*2,v=Math.sin(D),C=-Math.cos(D);l.x=C*y.x+v*A.x,l.y=C*y.y+v*A.y,l.z=C*y.z+v*A.z,l.normalize(),u.push(l.x,l.y,l.z),o.x=h.x+n*l.x,o.y=h.y+n*l.y,o.z=h.z+n*l.z,f.push(o.x,o.y,o.z)}}function p(){for(let I=1;I<=t;I++)for(let y=1;y<=s;y++){let A=(s+1)*(I-1)+(y-1),E=(s+1)*I+(y-1),D=(s+1)*I+y,v=(s+1)*(I-1)+y;_.push(A,E,v),_.push(E,D,v)}}function w(){for(let I=0;I<=t;I++)for(let y=0;y<=s;y++)c.x=I/t,c.y=y/s,d.push(c.x,c.y)}}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}toJSON(){let e=super.toJSON();return e.path=this.parameters.path.toJSON(),e}static fromJSON(e){return new i(new qd[e.path.type]().fromJSON(e.path),e.tubularSegments,e.radius,e.radialSegments,e.closed)}};function Gi(i){let e={};for(let t in i){e[t]={};for(let n in i[t]){let s=i[t][n];if(mu(s))s.isRenderTargetTexture?($e("UniformsUtils: Textures of render targets cannot be cloned via cloneUniforms() or mergeUniforms()."),e[t][n]=null):e[t][n]=s.clone();else if(Array.isArray(s))if(mu(s[0])){let r=[];for(let a=0,o=s.length;a<o;a++)r[a]=s[a].clone();e[t][n]=r}else e[t][n]=s.slice();else e[t][n]=s}}return e}function Qt(i){let e={};for(let t=0;t<i.length;t++){let n=Gi(i[t]);for(let s in n)e[s]=n[s]}return e}function mu(i){return i&&(i.isColor||i.isMatrix3||i.isMatrix4||i.isVector2||i.isVector3||i.isVector4||i.isTexture||i.isQuaternion)}function Xd(i){let e=[];for(let t=0;t<i.length;t++)e.push(i[t].clone());return e}function vc(i){let e=i.getRenderTarget();return e===null?i.outputColorSpace:e.isXRRenderTarget===!0?e.texture.colorSpace:at.workingColorSpace}var ni={clone:Gi,merge:Qt},Yd=`void main() {
	gl_Position = projectionMatrix * modelViewMatrix * vec4( position, 1.0 );
}`,Zd=`void main() {
	gl_FragColor = vec4( 1.0, 0.0, 0.0, 1.0 );
}`,Nt=class extends Ln{constructor(e){super(),this.isShaderMaterial=!0,this.type="ShaderMaterial",this.defines={},this.uniforms={},this.uniformsGroups=[],this.vertexShader=Yd,this.fragmentShader=Zd,this.linewidth=1,this.wireframe=!1,this.wireframeLinewidth=1,this.fog=!1,this.lights=!1,this.clipping=!1,this.forceSinglePass=!0,this.extensions={clipCullDistance:!1,multiDraw:!1},this.defaultAttributeValues={color:[1,1,1],uv:[0,0],uv1:[0,0]},this.index0AttributeName=void 0,this.uniformsNeedUpdate=!1,this.glslVersion=null,e!==void 0&&this.setValues(e)}copy(e){return super.copy(e),this.fragmentShader=e.fragmentShader,this.vertexShader=e.vertexShader,this.uniforms=Gi(e.uniforms),this.uniformsGroups=Xd(e.uniformsGroups),this.defines=Object.assign({},e.defines),this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this.fog=e.fog,this.lights=e.lights,this.clipping=e.clipping,this.extensions=Object.assign({},e.extensions),this.glslVersion=e.glslVersion,this.defaultAttributeValues=Object.assign({},e.defaultAttributeValues),this.index0AttributeName=e.index0AttributeName,this.uniformsNeedUpdate=e.uniformsNeedUpdate,this}toJSON(e){let t=super.toJSON(e);t.glslVersion=this.glslVersion,t.uniforms={};for(let s in this.uniforms){let a=this.uniforms[s].value;a&&a.isTexture?t.uniforms[s]={type:"t",value:a.toJSON(e).uuid}:a&&a.isColor?t.uniforms[s]={type:"c",value:a.getHex()}:a&&a.isVector2?t.uniforms[s]={type:"v2",value:a.toArray()}:a&&a.isVector3?t.uniforms[s]={type:"v3",value:a.toArray()}:a&&a.isVector4?t.uniforms[s]={type:"v4",value:a.toArray()}:a&&a.isMatrix3?t.uniforms[s]={type:"m3",value:a.toArray()}:a&&a.isMatrix4?t.uniforms[s]={type:"m4",value:a.toArray()}:t.uniforms[s]={value:a}}Object.keys(this.defines).length>0&&(t.defines=this.defines),t.vertexShader=this.vertexShader,t.fragmentShader=this.fragmentShader,t.lights=this.lights,t.clipping=this.clipping;let n={};for(let s in this.extensions)this.extensions[s]===!0&&(n[s]=!0);return Object.keys(n).length>0&&(t.extensions=n),t}fromJSON(e,t){if(super.fromJSON(e,t),e.uniforms!==void 0)for(let n in e.uniforms){let s=e.uniforms[n];switch(this.uniforms[n]={},s.type){case"t":this.uniforms[n].value=t[s.value]||null;break;case"c":this.uniforms[n].value=new qe().setHex(s.value);break;case"v2":this.uniforms[n].value=new De().fromArray(s.value);break;case"v3":this.uniforms[n].value=new B().fromArray(s.value);break;case"v4":this.uniforms[n].value=new It().fromArray(s.value);break;case"m3":this.uniforms[n].value=new Ye().fromArray(s.value);break;case"m4":this.uniforms[n].value=new ut().fromArray(s.value);break;default:this.uniforms[n].value=s.value}}if(e.defines!==void 0&&(this.defines=e.defines),e.vertexShader!==void 0&&(this.vertexShader=e.vertexShader),e.fragmentShader!==void 0&&(this.fragmentShader=e.fragmentShader),e.glslVersion!==void 0&&(this.glslVersion=e.glslVersion),e.extensions!==void 0)for(let n in e.extensions)this.extensions[n]=e.extensions[n];return e.lights!==void 0&&(this.lights=e.lights),e.clipping!==void 0&&(this.clipping=e.clipping),this}},Es=class extends Nt{constructor(e){super(e),this.isRawShaderMaterial=!0,this.type="RawShaderMaterial"}},Wt=class extends Ln{constructor(e){super(),this.isMeshStandardMaterial=!0,this.type="MeshStandardMaterial",this.defines={STANDARD:""},this.color=new qe(16777215),this.roughness=1,this.metalness=0,this.map=null,this.lightMap=null,this.lightMapIntensity=1,this.aoMap=null,this.aoMapIntensity=1,this.emissive=new qe(0),this.emissiveIntensity=1,this.emissiveMap=null,this.bumpMap=null,this.bumpScale=1,this.normalMap=null,this.normalMapType=Hr,this.normalScale=new De(1,1),this.displacementMap=null,this.displacementScale=1,this.displacementBias=0,this.roughnessMap=null,this.metalnessMap=null,this.alphaMap=null,this.envMap=null,this.envMapRotation=new vn,this.envMapIntensity=1,this.wireframe=!1,this.wireframeLinewidth=1,this.wireframeLinecap="round",this.wireframeLinejoin="round",this.flatShading=!1,this.fog=!0,this.setValues(e)}copy(e){return super.copy(e),this.defines={STANDARD:""},this.color.copy(e.color),this.roughness=e.roughness,this.metalness=e.metalness,this.map=e.map,this.lightMap=e.lightMap,this.lightMapIntensity=e.lightMapIntensity,this.aoMap=e.aoMap,this.aoMapIntensity=e.aoMapIntensity,this.emissive.copy(e.emissive),this.emissiveMap=e.emissiveMap,this.emissiveIntensity=e.emissiveIntensity,this.bumpMap=e.bumpMap,this.bumpScale=e.bumpScale,this.normalMap=e.normalMap,this.normalMapType=e.normalMapType,this.normalScale.copy(e.normalScale),this.displacementMap=e.displacementMap,this.displacementScale=e.displacementScale,this.displacementBias=e.displacementBias,this.roughnessMap=e.roughnessMap,this.metalnessMap=e.metalnessMap,this.alphaMap=e.alphaMap,this.envMap=e.envMap,this.envMapRotation.copy(e.envMapRotation),this.envMapIntensity=e.envMapIntensity,this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this.wireframeLinecap=e.wireframeLinecap,this.wireframeLinejoin=e.wireframeLinejoin,this.flatShading=e.flatShading,this.fog=e.fog,this}};var yr=class extends Ln{constructor(e){super(),this.isMeshLambertMaterial=!0,this.type="MeshLambertMaterial",this.color=new qe(16777215),this.map=null,this.lightMap=null,this.lightMapIntensity=1,this.aoMap=null,this.aoMapIntensity=1,this.emissive=new qe(0),this.emissiveIntensity=1,this.emissiveMap=null,this.bumpMap=null,this.bumpScale=1,this.normalMap=null,this.normalMapType=Hr,this.normalScale=new De(1,1),this.displacementMap=null,this.displacementScale=1,this.displacementBias=0,this.specularMap=null,this.alphaMap=null,this.envMap=null,this.envMapRotation=new vn,this.combine=ho,this.reflectivity=1,this.envMapIntensity=1,this.refractionRatio=.98,this.wireframe=!1,this.wireframeLinewidth=1,this.wireframeLinecap="round",this.wireframeLinejoin="round",this.flatShading=!1,this.fog=!0,this.setValues(e)}copy(e){return super.copy(e),this.color.copy(e.color),this.map=e.map,this.lightMap=e.lightMap,this.lightMapIntensity=e.lightMapIntensity,this.aoMap=e.aoMap,this.aoMapIntensity=e.aoMapIntensity,this.emissive.copy(e.emissive),this.emissiveMap=e.emissiveMap,this.emissiveIntensity=e.emissiveIntensity,this.bumpMap=e.bumpMap,this.bumpScale=e.bumpScale,this.normalMap=e.normalMap,this.normalMapType=e.normalMapType,this.normalScale.copy(e.normalScale),this.displacementMap=e.displacementMap,this.displacementScale=e.displacementScale,this.displacementBias=e.displacementBias,this.specularMap=e.specularMap,this.alphaMap=e.alphaMap,this.envMap=e.envMap,this.envMapRotation.copy(e.envMapRotation),this.combine=e.combine,this.reflectivity=e.reflectivity,this.envMapIntensity=e.envMapIntensity,this.refractionRatio=e.refractionRatio,this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this.wireframeLinecap=e.wireframeLinecap,this.wireframeLinejoin=e.wireframeLinejoin,this.flatShading=e.flatShading,this.fog=e.fog,this}},Ja=class extends Ln{constructor(e){super(),this.isMeshDepthMaterial=!0,this.type="MeshDepthMaterial",this.depthPacking=Xu,this.map=null,this.alphaMap=null,this.displacementMap=null,this.displacementScale=1,this.displacementBias=0,this.wireframe=!1,this.wireframeLinewidth=1,this.setValues(e)}copy(e){return super.copy(e),this.depthPacking=e.depthPacking,this.map=e.map,this.alphaMap=e.alphaMap,this.displacementMap=e.displacementMap,this.displacementScale=e.displacementScale,this.displacementBias=e.displacementBias,this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this}},Ka=class extends Ln{constructor(e){super(),this.isMeshDistanceMaterial=!0,this.type="MeshDistanceMaterial",this.map=null,this.alphaMap=null,this.displacementMap=null,this.displacementScale=1,this.displacementBias=0,this.setValues(e)}copy(e){return super.copy(e),this.map=e.map,this.alphaMap=e.alphaMap,this.displacementMap=e.displacementMap,this.displacementScale=e.displacementScale,this.displacementBias=e.displacementBias,this}};function ls(i,e){return!i||i.constructor===e?i:typeof e.BYTES_PER_ELEMENT=="number"?new e(i):Array.prototype.slice.call(i)}function Wl(i){return i!==void 0&&i.inTangents!==void 0&&i.outTangents!==void 0}var gi=class{constructor(e,t,n,s){this.parameterPositions=e,this._cachedIndex=0,this.resultBuffer=s!==void 0?s:new t.constructor(n),this.sampleValues=t,this.valueSize=n,this.settings=null,this.DefaultSettings_={}}evaluate(e){let t=this.parameterPositions,n=this._cachedIndex,s=t[n],r=t[n-1];n:{e:{let a;t:{i:if(!(e<s)){for(let o=n+2;;){if(s===void 0){if(e<r)break i;return n=t.length,this._cachedIndex=n,this.copySampleValue_(n-1)}if(n===o)break;if(r=s,s=t[++n],e<s)break e}a=t.length;break t}if(!(e>=r)){let o=t[1];e<o&&(n=2,r=o);for(let l=n-2;;){if(r===void 0)return this._cachedIndex=0,this.copySampleValue_(0);if(n===l)break;if(s=r,r=t[--n-1],e>=r)break e}a=n,n=0;break t}break n}for(;n<a;){let o=n+a>>>1;e<t[o]?a=o:n=o+1}if(s=t[n],r=t[n-1],r===void 0)return this._cachedIndex=0,this.copySampleValue_(0);if(s===void 0)return n=t.length,this._cachedIndex=n,this.copySampleValue_(n-1)}this._cachedIndex=n,this.intervalChanged_(n,r,s)}return this.interpolate_(n,r,e,s)}getSettings_(){return this.settings||this.DefaultSettings_}copySampleValue_(e){let t=this.resultBuffer,n=this.sampleValues,s=this.valueSize,r=e*s;for(let a=0;a!==s;++a)t[a]=n[r+a];return t}interpolate_(){throw new Error("THREE.Interpolant: Call to abstract method.")}intervalChanged_(){}},Qa=class extends gi{constructor(e,t,n,s){super(e,t,n,s),this._weightPrev=-0,this._offsetPrev=-0,this._weightNext=-0,this._offsetNext=-0,this.DefaultSettings_={endingStart:Xl,endingEnd:Xl}}intervalChanged_(e,t,n){let s=this.parameterPositions,r=e-2,a=e+1,o=s[r],l=s[a];if(o===void 0)switch(this.getSettings_().endingStart){case Yl:r=e,o=2*t-n;break;case Zl:r=s.length-2,o=t+s[r]-s[r+1];break;default:r=e,o=n}if(l===void 0)switch(this.getSettings_().endingEnd){case Yl:a=e,l=2*n-t;break;case Zl:a=1,l=n+s[1]-s[0];break;default:a=e-1,l=t}let c=(n-t)*.5,h=this.valueSize;this._weightPrev=c/(t-o),this._weightNext=c/(l-n),this._offsetPrev=r*h,this._offsetNext=a*h}interpolate_(e,t,n,s){let r=this.resultBuffer,a=this.sampleValues,o=this.valueSize,l=e*o,c=l-o,h=this._offsetPrev,f=this._offsetNext,u=this._weightPrev,d=this._weightNext,_=(n-t)/(s-t),S=_*_,g=S*_,p=-u*g+2*u*S-u*_,w=(1+u)*g+(-1.5-2*u)*S+(-.5+u)*_+1,I=(-1-d)*g+(1.5+d)*S+.5*_,y=d*g-d*S;for(let A=0;A!==o;++A)r[A]=p*a[h+A]+w*a[c+A]+I*a[l+A]+y*a[f+A];return r}},eo=class extends gi{constructor(e,t,n,s){super(e,t,n,s)}interpolate_(e,t,n,s){let r=this.resultBuffer,a=this.sampleValues,o=this.valueSize,l=e*o,c=l-o,h=(n-t)/(s-t),f=1-h;for(let u=0;u!==o;++u)r[u]=a[c+u]*f+a[l+u]*h;return r}},to=class extends gi{constructor(e,t,n,s){super(e,t,n,s)}interpolate_(e){return this.copySampleValue_(e-1)}},no=class extends gi{interpolate_(e,t,n,s){let r=this.resultBuffer,a=this.sampleValues,o=this.valueSize,l=e*o,c=l-o,h=this.inTangents,f=this.outTangents;if(!h||!f){let _=(n-t)/(s-t),S=1-_;for(let g=0;g!==o;++g)r[g]=a[c+g]*S+a[l+g]*_;return r}let u=o*2,d=e-1;for(let _=0;_!==o;++_){let S=a[c+_],g=a[l+_],p=d*u+_*2,w=f[p],I=f[p+1],y=e*u+_*2,A=h[y],E=h[y+1],D=Jd(n,t,w,A,s);r[_]=lh(D,S,I,E,g)}return r}};function lh(i,e,t,n,s){let r=1-i;return r*r*r*e+3*r*r*i*t+3*r*i*i*n+i*i*i*s}function jd(i,e,t,n,s){let r=1-i;return 3*r*r*(t-e)+6*r*i*(n-t)+3*i*i*(s-n)}function Jd(i,e,t,n,s){let r=(i-e)/(s-e);for(let a=0;a<8;a++){let o=lh(r,e,t,n,s)-i;if(Math.abs(o)<1e-10)break;let l=jd(r,e,t,n,s);if(Math.abs(l)<1e-10)break;r=Math.max(0,Math.min(1,r-o/l))}return r}var pn=class{constructor(e,t,n,s){if(e===void 0)throw new Error("THREE.KeyframeTrack: track name is undefined");if(t===void 0||t.length===0)throw new Error("THREE.KeyframeTrack: no keyframes in track named "+e);this.name=e,this.times=ls(t,this.TimeBufferType),this.values=ls(n,this.ValueBufferType),this.setInterpolation(s||this.DefaultInterpolation)}static toJSON(e){let t=e.constructor,n;if(t.toJSON!==this.toJSON)n=t.toJSON(e);else{n={name:e.name,times:ls(e.times,Array),values:ls(e.values,Array)};let s=e.getInterpolation();s!==e.DefaultInterpolation&&(n.interpolation=s),Wl(e.settings)&&(n.settings={inTangents:ls(e.settings.inTangents,Array),outTangents:ls(e.settings.outTangents,Array)})}return n.type=e.ValueTypeName,n}InterpolantFactoryMethodDiscrete(e){return new to(this.times,this.values,this.getValueSize(),e)}InterpolantFactoryMethodLinear(e){return new eo(this.times,this.values,this.getValueSize(),e)}InterpolantFactoryMethodSmooth(e){return new Qa(this.times,this.values,this.getValueSize(),e)}InterpolantFactoryMethodBezier(e){let t=new no(this.times,this.values,this.getValueSize(),e);return this.settings&&(t.inTangents=this.settings.inTangents,t.outTangents=this.settings.outTangents),t}setInterpolation(e){let t;switch(e){case er:t=this.InterpolantFactoryMethodDiscrete;break;case ka:t=this.InterpolantFactoryMethodLinear;break;case wa:t=this.InterpolantFactoryMethodSmooth;break;case ql:t=this.InterpolantFactoryMethodBezier;break}if(t===void 0){let n="unsupported interpolation for "+this.ValueTypeName+" keyframe track named "+this.name;if(this.createInterpolant===void 0)if(e!==this.DefaultInterpolation)this.setInterpolation(this.DefaultInterpolation);else throw new Error(n);return $e("KeyframeTrack:",n),this}return this.createInterpolant=t,this}getInterpolation(){switch(this.createInterpolant){case this.InterpolantFactoryMethodDiscrete:return er;case this.InterpolantFactoryMethodLinear:return ka;case this.InterpolantFactoryMethodSmooth:return wa;case this.InterpolantFactoryMethodBezier:return ql}}getValueSize(){return this.values.length/this.times.length}shift(e){if(e!==0){let t=this.times;for(let n=0,s=t.length;n!==s;++n)t[n]+=e}return this}scale(e){if(e!==1){let t=this.times;for(let n=0,s=t.length;n!==s;++n)t[n]*=e;Wl(this.settings)&&(gu(this.settings.inTangents,e),gu(this.settings.outTangents,e))}return this}trim(e,t){let n=this.times,s=n.length,r=0,a=s-1;for(;r!==s&&n[r]<e;)++r;for(;a!==-1&&n[a]>t;)--a;if(++a,r!==0||a!==s){r>=a&&(a=Math.max(a,1),r=a-1);let o=this.getValueSize();this.times=n.slice(r,a),this.values=this.values.slice(r*o,a*o)}return this}validate(){let e=!0,t=this.getValueSize();t-Math.floor(t)!==0&&(Xe("KeyframeTrack: Invalid value size in track.",this),e=!1);let n=this.times,s=this.values,r=n.length;r===0&&(Xe("KeyframeTrack: Track is empty.",this),e=!1);let a=null;for(let o=0;o!==r;o++){let l=n[o];if(typeof l=="number"&&isNaN(l)){Xe("KeyframeTrack: Time is not a valid number.",this,o,l),e=!1;break}if(a!==null&&a>l){Xe("KeyframeTrack: Out of order keys.",this,o,l,a),e=!1;break}a=l}if(s!==void 0&&id(s))for(let o=0,l=s.length;o!==l;++o){let c=s[o];if(isNaN(c)){Xe("KeyframeTrack: Value is not a valid number.",this,o,c),e=!1;break}}return e}optimize(){let e=this.times.slice(),t=this.values.slice(),n=this.getValueSize(),s=this.getInterpolation()===wa,r=e.length-1,a=1;for(let o=1;o<r;++o){let l=!1,c=e[o],h=e[o+1];if(c!==h&&(o!==1||c!==e[0]))if(s)l=!0;else{let f=o*n,u=f-n,d=f+n;for(let _=0;_!==n;++_){let S=t[f+_];if(S!==t[u+_]||S!==t[d+_]){l=!0;break}}}if(l){if(o!==a){e[a]=e[o];let f=o*n,u=a*n;for(let d=0;d!==n;++d)t[u+d]=t[f+d]}++a}}if(r>0){e[a]=e[r];for(let o=r*n,l=a*n,c=0;c!==n;++c)t[l+c]=t[o+c];++a}return a!==e.length?(this.times=e.slice(0,a),this.values=t.slice(0,a*n)):(this.times=e,this.values=t),this}clone(){let e=this.times.slice(),t=this.values.slice(),n=this.constructor,s=new n(this.name,e,t);return s.createInterpolant=this.createInterpolant,Wl(this.settings)&&(s.settings={inTangents:this.settings.inTangents.slice(),outTangents:this.settings.outTangents.slice()}),s}};function gu(i,e){for(let t=0,n=i.length;t!==n;t+=2)i[t]*=e}pn.prototype.ValueTypeName="";pn.prototype.TimeBufferType=Float32Array;pn.prototype.ValueBufferType=Float32Array;pn.prototype.DefaultInterpolation=ka;var _i=class extends pn{constructor(e,t,n){super(e,t,n)}};_i.prototype.ValueTypeName="bool";_i.prototype.ValueBufferType=Array;_i.prototype.DefaultInterpolation=er;_i.prototype.InterpolantFactoryMethodLinear=void 0;_i.prototype.InterpolantFactoryMethodSmooth=void 0;var io=class extends pn{constructor(e,t,n,s){super(e,t,n,s)}};io.prototype.ValueTypeName="color";var so=class extends pn{constructor(e,t,n,s){super(e,t,n,s)}};so.prototype.ValueTypeName="number";var ro=class extends gi{constructor(e,t,n,s){super(e,t,n,s)}interpolate_(e,t,n,s){let r=this.resultBuffer,a=this.sampleValues,o=this.valueSize,l=(n-t)/(s-t),c=e*o;for(let h=c+o;c!==h;c+=4)Ot.slerpFlat(r,0,a,c-o,a,c,l);return r}},br=class extends pn{constructor(e,t,n,s){super(e,t,n,s)}InterpolantFactoryMethodLinear(e){return new ro(this.times,this.values,this.getValueSize(),e)}};br.prototype.ValueTypeName="quaternion";br.prototype.InterpolantFactoryMethodSmooth=void 0;var xi=class extends pn{constructor(e,t,n){super(e,t,n)}};xi.prototype.ValueTypeName="string";xi.prototype.ValueBufferType=Array;xi.prototype.DefaultInterpolation=er;xi.prototype.InterpolantFactoryMethodLinear=void 0;xi.prototype.InterpolantFactoryMethodSmooth=void 0;var ao=class extends pn{constructor(e,t,n,s){super(e,t,n,s)}};ao.prototype.ValueTypeName="vector";var oo=class{constructor(e,t,n){let s=this,r=!1,a=0,o=0,l,c=[];this.onStart=void 0,this.onLoad=e,this.onProgress=t,this.onError=n,this._abortController=null,this.itemStart=function(h){o++,r===!1&&s.onStart!==void 0&&s.onStart(h,a,o),r=!0},this.itemEnd=function(h){a++,s.onProgress!==void 0&&s.onProgress(h,a,o),a===o&&(r=!1,s.onLoad!==void 0&&s.onLoad())},this.itemError=function(h){s.onError!==void 0&&s.onError(h)},this.resolveURL=function(h){return h=h.normalize("NFC"),l?l(h):h},this.setURLModifier=function(h){return l=h,this},this.addHandler=function(h,f){return c.push(h,f),this},this.removeHandler=function(h){let f=c.indexOf(h);return f!==-1&&c.splice(f,2),this},this.getHandler=function(h){for(let f=0,u=c.length;f<u;f+=2){let d=c[f],_=c[f+1];if(d.global&&(d.lastIndex=0),d.test(h))return _}return null},this.abort=function(){return this.abortController.abort(),this._abortController=null,this}}get abortController(){return this._abortController||(this._abortController=new AbortController),this._abortController}},ch=new oo,lo=class{constructor(e){this.manager=e!==void 0?e:ch,this.crossOrigin="anonymous",this.withCredentials=!1,this.path="",this.resourcePath="",this.requestHeader={},typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("observe",{detail:this}))}load(){}loadAsync(e,t){let n=this;return new Promise(function(s,r){n.load(e,s,t,r)})}parse(){}setCrossOrigin(e){return this.crossOrigin=e,this}setWithCredentials(e){return this.withCredentials=e,this}setPath(e){return this.path=e,this}setResourcePath(e){return this.resourcePath=e,this}setRequestHeader(e){return this.requestHeader=e,this}abort(){return this}};lo.DEFAULT_MATERIAL_NAME="__DEFAULT";var ws=class extends kt{constructor(e,t=1){super(),this.isLight=!0,this.type="Light",this.color=new qe(e),this.intensity=t}copy(e,t){return super.copy(e,t),this.color.copy(e.color),this.intensity=e.intensity,this}toJSON(e){let t=super.toJSON(e);return t.object.color=this.color.getHex(),t.object.intensity=this.intensity,t}},Mr=class extends ws{constructor(e,t,n){super(e,n),this.isHemisphereLight=!0,this.type="HemisphereLight",this.position.copy(kt.DEFAULT_UP),this.updateMatrix(),this.groundColor=new qe(t)}copy(e,t){return super.copy(e,t),this.groundColor.copy(e.groundColor),this}toJSON(e){let t=super.toJSON(e);return t.object.groundColor=this.groundColor.getHex(),t}},$l=new ut,_u=new B,xu=new B,Sr=class{constructor(e){this.camera=e,this.intensity=1,this.bias=0,this.biasNode=null,this.normalBias=0,this.radius=1,this.blurSamples=8,this.mapSize=new De(512,512),this.mapType=un,this.map=null,this.mapPass=null,this.matrix=new ut,this.autoUpdate=!0,this.needsUpdate=!1,this._frustum=new ys,this._frameExtents=new De(1,1),this._viewportCount=1,this._viewports=[new It(0,0,1,1)]}getViewportCount(){return this._viewportCount}getCamera(){return this.camera}getFrustum(){return this._frustum}updateMatrices(e){let t=this.camera;_u.setFromMatrixPosition(e.matrixWorld),t.position.copy(_u),xu.setFromMatrixPosition(e.target.matrixWorld),t.lookAt(xu),t.updateMatrixWorld(),this._updateMatrix(t,this.matrix,this._frustum)}_updateMatrix(e,t,n,s){$l.multiplyMatrices(e.projectionMatrix,e.matrixWorldInverse),n.setFromProjectionMatrix($l,e.coordinateSystem,e.reversedDepth);let r=this._frameExtents,a=s?s.z/r.x:1,o=s?s.w/r.y:1,l=s?s.x/r.x:0,c=s?s.y/r.y:0;e.coordinateSystem===ps||e.reversedDepth?t.set(.5*a,0,0,.5*a+l,0,.5*o,0,.5*o+c,0,0,1,0,0,0,0,1):t.set(.5*a,0,0,.5*a+l,0,.5*o,0,.5*o+c,0,0,.5,.5,0,0,0,1),t.multiply($l)}getViewport(e){return this._viewports[e]}getFrameExtents(){return this._frameExtents}dispose(){this.map&&this.map.dispose(),this.mapPass&&this.mapPass.dispose()}copy(e){return this.camera=e.camera.clone(),this.intensity=e.intensity,this.bias=e.bias,this.radius=e.radius,this.autoUpdate=e.autoUpdate,this.needsUpdate=e.needsUpdate,this.normalBias=e.normalBias,this.blurSamples=e.blurSamples,this.mapSize.copy(e.mapSize),this.biasNode=e.biasNode,this}clone(){return new this.constructor().copy(this)}toJSON(){let e={};return e.intensity=this.intensity,e.bias=this.bias,e.normalBias=this.normalBias,e.radius=this.radius,e.blurSamples=this.blurSamples,e.mapSize=this.mapSize.toArray(),e.camera=this.camera.toJSON(!1).object,delete e.camera.matrix,e}},Ta=new B,Ea=new Ot,kn=new B,Tr=class extends kt{constructor(){super(),this.isCamera=!0,this.type="Camera",this.matrixWorldInverse=new ut,this.projectionMatrix=new ut,this.projectionMatrixInverse=new ut,this.coordinateSystem=Pn,this._reversedDepth=!1}get reversedDepth(){return this._reversedDepth}copy(e,t){return super.copy(e,t),this.matrixWorldInverse.copy(e.matrixWorldInverse),this.projectionMatrix.copy(e.projectionMatrix),this.projectionMatrixInverse.copy(e.projectionMatrixInverse),this.coordinateSystem=e.coordinateSystem,this}getWorldDirection(e){return super.getWorldDirection(e).negate()}updateMatrixWorld(e){super.updateMatrixWorld(e),this.matrixWorld.decompose(Ta,Ea,kn),kn.x===1&&kn.y===1&&kn.z===1?this.matrixWorldInverse.copy(this.matrixWorld).invert():this.matrixWorldInverse.compose(Ta,Ea,kn.set(1,1,1)).invert()}updateWorldMatrix(e,t,n=!1){super.updateWorldMatrix(e,t,n),this.matrixWorld.decompose(Ta,Ea,kn),kn.x===1&&kn.y===1&&kn.z===1?this.matrixWorldInverse.copy(this.matrixWorld).invert():this.matrixWorldInverse.compose(Ta,Ea,kn.set(1,1,1)).invert()}clone(){return new this.constructor().copy(this)}},fi=new B,vu=new De,yu=new De,qt=class extends Tr{constructor(e=50,t=1,n=.1,s=2e3){super(),this.isPerspectiveCamera=!0,this.type="PerspectiveCamera",this.fov=e,this.zoom=1,this.near=n,this.far=s,this.focus=10,this.aspect=t,this.view=null,this.filmGauge=35,this.filmOffset=0,this.updateProjectionMatrix()}copy(e,t){return super.copy(e,t),this.fov=e.fov,this.zoom=e.zoom,this.near=e.near,this.far=e.far,this.focus=e.focus,this.aspect=e.aspect,this.view=e.view===null?null:Object.assign({},e.view),this.filmGauge=e.filmGauge,this.filmOffset=e.filmOffset,this}setFocalLength(e){let t=.5*this.getFilmHeight()/e;this.fov=gs*2*Math.atan(t),this.updateProjectionMatrix()}getFocalLength(){let e=Math.tan(js*.5*this.fov);return .5*this.getFilmHeight()/e}getEffectiveFOV(){return gs*2*Math.atan(Math.tan(js*.5*this.fov)/this.zoom)}getFilmWidth(){return this.filmGauge*Math.min(this.aspect,1)}getFilmHeight(){return this.filmGauge/Math.max(this.aspect,1)}getViewBounds(e,t,n){fi.set(-1,-1,.5).applyMatrix4(this.projectionMatrixInverse),t.set(fi.x,fi.y).multiplyScalar(-e/fi.z),fi.set(1,1,.5).applyMatrix4(this.projectionMatrixInverse),n.set(fi.x,fi.y).multiplyScalar(-e/fi.z)}getViewSize(e,t){return this.getViewBounds(e,vu,yu),t.subVectors(yu,vu)}setViewOffset(e,t,n,s,r,a){this.aspect=e/t,this.view===null&&(this.view={enabled:!0,fullWidth:1,fullHeight:1,offsetX:0,offsetY:0,width:1,height:1}),this.view.enabled=!0,this.view.fullWidth=e,this.view.fullHeight=t,this.view.offsetX=n,this.view.offsetY=s,this.view.width=r,this.view.height=a,this.updateProjectionMatrix()}clearViewOffset(){this.view!==null&&(this.view.enabled=!1),this.updateProjectionMatrix()}updateProjectionMatrix(){let e=this.near,t=e*Math.tan(js*.5*this.fov)/this.zoom,n=2*t,s=this.aspect*n,r=-.5*s,a=this.view;if(this.view!==null&&this.view.enabled){let l=a.fullWidth,c=a.fullHeight;r+=a.offsetX*s/l,t-=a.offsetY*n/c,s*=a.width/l,n*=a.height/c}let o=this.filmOffset;o!==0&&(r+=e*o/this.getFilmWidth()),this.projectionMatrix.makePerspective(r,r+s,t,t-n,e,this.far,this.coordinateSystem,this.reversedDepth),this.projectionMatrixInverse.copy(this.projectionMatrix).invert()}toJSON(e){let t=super.toJSON(e);return t.object.fov=this.fov,t.object.zoom=this.zoom,t.object.near=this.near,t.object.far=this.far,t.object.focus=this.focus,t.object.aspect=this.aspect,this.view!==null&&(t.object.view=Object.assign({},this.view)),t.object.filmGauge=this.filmGauge,t.object.filmOffset=this.filmOffset,t}};var Jl=class extends Sr{constructor(){super(new qt(90,1,.5,500)),this.isPointLightShadow=!0}},ei=class extends ws{constructor(e,t,n=0,s=2){super(e,t),this.isPointLight=!0,this.type="PointLight",this.distance=n,this.decay=s,this.shadow=new Jl}get power(){return this.intensity*4*Math.PI}set power(e){this.intensity=e/(4*Math.PI)}dispose(){super.dispose(),this.shadow.dispose()}copy(e,t){return super.copy(e,t),this.distance=e.distance,this.decay=e.decay,this.shadow=e.shadow.clone(),this}toJSON(e){let t=super.toJSON(e);return t.object.distance=this.distance,t.object.decay=this.decay,t.object.shadow=this.shadow.toJSON(),t}},vi=class extends Tr{constructor(e=-1,t=1,n=1,s=-1,r=.1,a=2e3){super(),this.isOrthographicCamera=!0,this.type="OrthographicCamera",this.zoom=1,this.view=null,this.left=e,this.right=t,this.top=n,this.bottom=s,this.near=r,this.far=a,this.updateProjectionMatrix()}copy(e,t){return super.copy(e,t),this.left=e.left,this.right=e.right,this.top=e.top,this.bottom=e.bottom,this.near=e.near,this.far=e.far,this.zoom=e.zoom,this.view=e.view===null?null:Object.assign({},e.view),this}setViewOffset(e,t,n,s,r,a){this.view===null&&(this.view={enabled:!0,fullWidth:1,fullHeight:1,offsetX:0,offsetY:0,width:1,height:1}),this.view.enabled=!0,this.view.fullWidth=e,this.view.fullHeight=t,this.view.offsetX=n,this.view.offsetY=s,this.view.width=r,this.view.height=a,this.updateProjectionMatrix()}clearViewOffset(){this.view!==null&&(this.view.enabled=!1),this.updateProjectionMatrix()}updateProjectionMatrix(){let e=(this.right-this.left)/(2*this.zoom),t=(this.top-this.bottom)/(2*this.zoom),n=(this.right+this.left)/2,s=(this.top+this.bottom)/2,r=n-e,a=n+e,o=s+t,l=s-t;if(this.view!==null&&this.view.enabled){let c=(this.right-this.left)/this.view.fullWidth/this.zoom,h=(this.top-this.bottom)/this.view.fullHeight/this.zoom;r+=c*this.view.offsetX,a=r+c*this.view.width,o-=h*this.view.offsetY,l=o-h*this.view.height}this.projectionMatrix.makeOrthographic(r,a,o,l,this.near,this.far,this.coordinateSystem,this.reversedDepth),this.projectionMatrixInverse.copy(this.projectionMatrix).invert()}toJSON(e){let t=super.toJSON(e);return t.object.zoom=this.zoom,t.object.left=this.left,t.object.right=this.right,t.object.top=this.top,t.object.bottom=this.bottom,t.object.near=this.near,t.object.far=this.far,this.view!==null&&(t.object.view=Object.assign({},this.view)),t}},Kl=class extends Sr{constructor(){super(new vi(-5,5,5,-5,.5,500)),this.isDirectionalLightShadow=!0}},Oi=class extends ws{constructor(e,t){super(e,t),this.isDirectionalLight=!0,this.type="DirectionalLight",this.position.copy(kt.DEFAULT_UP),this.updateMatrix(),this.target=new kt,this.shadow=new Kl}dispose(){super.dispose(),this.shadow.dispose()}copy(e){return super.copy(e),this.target=e.target.clone(),this.shadow=e.shadow.clone(),this}toJSON(e){let t=super.toJSON(e);return t.object.shadow=this.shadow.toJSON(),t.object.target=this.target.uuid,t}};var cs=-90,us=1,co=class extends kt{constructor(e,t,n){super(),this.type="CubeCamera",this.renderTarget=n,this.coordinateSystem=null,this.activeMipmapLevel=0;let s=new qt(cs,us,e,t);s.layers=this.layers,this.add(s);let r=new qt(cs,us,e,t);r.layers=this.layers,this.add(r);let a=new qt(cs,us,e,t);a.layers=this.layers,this.add(a);let o=new qt(cs,us,e,t);o.layers=this.layers,this.add(o);let l=new qt(cs,us,e,t);l.layers=this.layers,this.add(l);let c=new qt(cs,us,e,t);c.layers=this.layers,this.add(c)}updateCoordinateSystem(){let e=this.coordinateSystem,t=this.children.concat(),[n,s,r,a,o,l]=t;for(let c of t)this.remove(c);if(e===Pn)n.up.set(0,1,0),n.lookAt(1,0,0),s.up.set(0,1,0),s.lookAt(-1,0,0),r.up.set(0,0,-1),r.lookAt(0,1,0),a.up.set(0,0,1),a.lookAt(0,-1,0),o.up.set(0,1,0),o.lookAt(0,0,1),l.up.set(0,1,0),l.lookAt(0,0,-1);else if(e===ps)n.up.set(0,-1,0),n.lookAt(-1,0,0),s.up.set(0,-1,0),s.lookAt(1,0,0),r.up.set(0,0,1),r.lookAt(0,1,0),a.up.set(0,0,-1),a.lookAt(0,-1,0),o.up.set(0,-1,0),o.lookAt(0,0,1),l.up.set(0,-1,0),l.lookAt(0,0,-1);else throw new Error("THREE.CubeCamera.updateCoordinateSystem(): Invalid coordinate system: "+e);for(let c of t)this.add(c),c.updateMatrixWorld()}update(e,t){this.parent===null&&this.updateMatrixWorld();let{renderTarget:n,activeMipmapLevel:s}=this;this.coordinateSystem!==e.coordinateSystem&&(this.coordinateSystem=e.coordinateSystem,this.updateCoordinateSystem());let[r,a,o,l,c,h]=this.children,f=e.getRenderTarget(),u=e.getActiveCubeFace(),d=e.getActiveMipmapLevel(),_=e.xr.enabled;e.xr.enabled=!1;let S=n.texture.generateMipmaps;n.texture.generateMipmaps=!1;let g=!1;e.isWebGLRenderer===!0?g=e.state.buffers.depth.getReversed():g=e.reversedDepthBuffer,e.setRenderTarget(n,0,s),g&&e.autoClear===!1&&e.clearDepth(),e.render(t,r),e.setRenderTarget(n,1,s),g&&e.autoClear===!1&&e.clearDepth(),e.render(t,a),e.setRenderTarget(n,2,s),g&&e.autoClear===!1&&e.clearDepth(),e.render(t,o),e.setRenderTarget(n,3,s),g&&e.autoClear===!1&&e.clearDepth(),e.render(t,l),e.setRenderTarget(n,4,s),g&&e.autoClear===!1&&e.clearDepth(),e.render(t,c),n.texture.generateMipmaps=S,e.setRenderTarget(n,5,s),g&&e.autoClear===!1&&e.clearDepth(),e.render(t,h),e.setRenderTarget(f,u,d),e.xr.enabled=_,n.texture.needsPMREMUpdate=!0}},uo=class extends qt{constructor(e=[]){super(),this.isArrayCamera=!0,this.isMultiViewCamera=!1,this.cameras=e}},Er=class{constructor(){this._previousTime=0,this._currentTime=0,this._startTime=performance.now(),this._delta=0,this._elapsed=0,this._timescale=1,this._document=null,this._pageVisibilityHandler=null}connect(e){this._document=e,e.hidden!==void 0&&(this._pageVisibilityHandler=Kd.bind(this),e.addEventListener("visibilitychange",this._pageVisibilityHandler,!1))}disconnect(){this._pageVisibilityHandler!==null&&(this._document.removeEventListener("visibilitychange",this._pageVisibilityHandler),this._pageVisibilityHandler=null),this._document=null}getDelta(){return this._delta/1e3}getElapsed(){return this._elapsed/1e3}getTimescale(){return this._timescale}setTimescale(e){return this._timescale=e,this}reset(){return this._currentTime=performance.now()-this._startTime,this}dispose(){this.disconnect()}update(e){return this._pageVisibilityHandler!==null&&this._document.hidden===!0?this._delta=0:(this._previousTime=this._currentTime,this._currentTime=(e!==void 0?e:performance.now())-this._startTime,this._delta=(this._currentTime-this._previousTime)*this._timescale,this._elapsed+=this._delta),this}};function Kd(){this._document.hidden===!1&&this.reset()}var yc="\\[\\]\\.:\\/",Qd=new RegExp("["+yc+"]","g"),bc="[^"+yc+"]",ef="[^"+yc.replace("\\.","")+"]",tf=/((?:WC+[\/:])*)/.source.replace("WC",bc),nf=/(WCOD+)?/.source.replace("WCOD",ef),sf=/(?:\.(WC+)(?:\[(.+)\])?)?/.source.replace("WC",bc),rf=/\.(WC+)(?:\[(.+)\])?/.source.replace("WC",bc),af=new RegExp("^"+tf+nf+sf+rf+"$"),of=["material","materials","bones","map"],Ql=class{constructor(e,t,n){let s=n||wt.parseTrackName(t);this._targetGroup=e,this._bindings=e.subscribe_(t,s)}getValue(e,t){this.bind();let n=this._targetGroup.nCachedObjects_,s=this._bindings[n];s!==void 0&&s.getValue(e,t)}setValue(e,t){let n=this._bindings;for(let s=this._targetGroup.nCachedObjects_,r=n.length;s!==r;++s)n[s].setValue(e,t)}bind(){let e=this._bindings;for(let t=this._targetGroup.nCachedObjects_,n=e.length;t!==n;++t)e[t].bind()}unbind(){let e=this._bindings;for(let t=this._targetGroup.nCachedObjects_,n=e.length;t!==n;++t)e[t].unbind()}},wt=class i{constructor(e,t,n){this.path=t,this.parsedPath=n||i.parseTrackName(t),this.node=i.findNode(e,this.parsedPath.nodeName),this.rootNode=e,this.getValue=this._getValue_unbound,this.setValue=this._setValue_unbound}static create(e,t,n){return e&&e.isAnimationObjectGroup?new i.Composite(e,t,n):new i(e,t,n)}static sanitizeNodeName(e){return e.replace(/\s/g,"_").replace(Qd,"")}static parseTrackName(e){let t=af.exec(e);if(t===null)throw new Error("THREE.PropertyBinding: Cannot parse trackName: "+e);let n={nodeName:t[2],objectName:t[3],objectIndex:t[4],propertyName:t[5],propertyIndex:t[6]},s=n.nodeName&&n.nodeName.lastIndexOf(".");if(s!==void 0&&s!==-1){let r=n.nodeName.substring(s+1);of.indexOf(r)!==-1&&(n.nodeName=n.nodeName.substring(0,s),n.objectName=r)}if(n.propertyName===null||n.propertyName.length===0)throw new Error("THREE.PropertyBinding: can not parse propertyName from trackName: "+e);return n}static findNode(e,t){if(t===void 0||t===""||t==="."||t===-1||t===e.name||t===e.uuid)return e;if(e.skeleton){let n=e.skeleton.getBoneByName(t);if(n!==void 0)return n}if(e.children){let n=function(r){for(let a=0;a<r.length;a++){let o=r[a];if(o.name===t||o.uuid===t)return o;let l=n(o.children);if(l)return l}return null},s=n(e.children);if(s)return s}return null}_getValue_unavailable(){}_setValue_unavailable(){}_getValue_direct(e,t){e[t]=this.targetObject[this.propertyName]}_getValue_array(e,t){let n=this.resolvedProperty;for(let s=0,r=n.length;s!==r;++s)e[t++]=n[s]}_getValue_arrayElement(e,t){e[t]=this.resolvedProperty[this.propertyIndex]}_getValue_toArray(e,t){this.resolvedProperty.toArray(e,t)}_setValue_direct(e,t){this.targetObject[this.propertyName]=e[t]}_setValue_direct_setNeedsUpdate(e,t){this.targetObject[this.propertyName]=e[t],this.targetObject.needsUpdate=!0}_setValue_direct_setMatrixWorldNeedsUpdate(e,t){this.targetObject[this.propertyName]=e[t],this.targetObject.matrixWorldNeedsUpdate=!0}_setValue_array(e,t){let n=this.resolvedProperty;for(let s=0,r=n.length;s!==r;++s)n[s]=e[t++]}_setValue_array_setNeedsUpdate(e,t){let n=this.resolvedProperty;for(let s=0,r=n.length;s!==r;++s)n[s]=e[t++];this.targetObject.needsUpdate=!0}_setValue_array_setMatrixWorldNeedsUpdate(e,t){let n=this.resolvedProperty;for(let s=0,r=n.length;s!==r;++s)n[s]=e[t++];this.targetObject.matrixWorldNeedsUpdate=!0}_setValue_arrayElement(e,t){this.resolvedProperty[this.propertyIndex]=e[t]}_setValue_arrayElement_setNeedsUpdate(e,t){this.resolvedProperty[this.propertyIndex]=e[t],this.targetObject.needsUpdate=!0}_setValue_arrayElement_setMatrixWorldNeedsUpdate(e,t){this.resolvedProperty[this.propertyIndex]=e[t],this.targetObject.matrixWorldNeedsUpdate=!0}_setValue_fromArray(e,t){this.resolvedProperty.fromArray(e,t)}_setValue_fromArray_setNeedsUpdate(e,t){this.resolvedProperty.fromArray(e,t),this.targetObject.needsUpdate=!0}_setValue_fromArray_setMatrixWorldNeedsUpdate(e,t){this.resolvedProperty.fromArray(e,t),this.targetObject.matrixWorldNeedsUpdate=!0}_getValue_unbound(e,t){this.bind(),this.getValue(e,t)}_setValue_unbound(e,t){this.bind(),this.setValue(e,t)}bind(){let e=this.node,t=this.parsedPath,n=t.objectName,s=t.propertyName,r=t.propertyIndex;if(e||(e=i.findNode(this.rootNode,t.nodeName),this.node=e),this.getValue=this._getValue_unavailable,this.setValue=this._setValue_unavailable,!e){$e("PropertyBinding: No target node found for track: "+this.path+".");return}if(n){let c=t.objectIndex;switch(n){case"materials":if(!e.material){Xe("PropertyBinding: Can not bind to material as node does not have a material.",this);return}if(!e.material.materials){Xe("PropertyBinding: Can not bind to material.materials as node.material does not have a materials array.",this);return}e=e.material.materials;break;case"bones":if(!e.skeleton){Xe("PropertyBinding: Can not bind to bones as node does not have a skeleton.",this);return}e=e.skeleton.bones;for(let h=0;h<e.length;h++)if(e[h].name===c){c=h;break}break;case"map":if("map"in e){e=e.map;break}if(!e.material){Xe("PropertyBinding: Can not bind to material as node does not have a material.",this);return}if(!e.material.map){Xe("PropertyBinding: Can not bind to material.map as node.material does not have a map.",this);return}e=e.material.map;break;default:if(e[n]===void 0){Xe("PropertyBinding: Can not bind to objectName of node undefined.",this);return}e=e[n]}if(c!==void 0){if(e[c]===void 0){Xe("PropertyBinding: Trying to bind to objectIndex of objectName, but is undefined.",this,e);return}e=e[c]}}let a=e[s];if(a===void 0){let c=t.nodeName;Xe("PropertyBinding: Trying to update property for track: "+c+"."+s+" but it wasn't found.",e);return}let o=this.Versioning.None;this.targetObject=e,e.isMaterial===!0?o=this.Versioning.NeedsUpdate:e.isObject3D===!0&&(o=this.Versioning.MatrixWorldNeedsUpdate);let l=this.BindingType.Direct;if(r!==void 0){if(s==="morphTargetInfluences"){if(!e.geometry){Xe("PropertyBinding: Can not bind to morphTargetInfluences because node does not have a geometry.",this);return}if(!e.geometry.morphAttributes){Xe("PropertyBinding: Can not bind to morphTargetInfluences because node does not have a geometry.morphAttributes.",this);return}e.morphTargetDictionary[r]!==void 0&&(r=e.morphTargetDictionary[r])}l=this.BindingType.ArrayElement,this.resolvedProperty=a,this.propertyIndex=r}else a.fromArray!==void 0&&a.toArray!==void 0?(l=this.BindingType.HasFromToArray,this.resolvedProperty=a):Array.isArray(a)?(l=this.BindingType.EntireArray,this.resolvedProperty=a):this.propertyName=s;this.getValue=this.GetterByBindingType[l],this.setValue=this.SetterByBindingTypeAndVersioning[l][o]}unbind(){this.node=null,this.getValue=this._getValue_unbound,this.setValue=this._setValue_unbound}};wt.Composite=Ql;wt.prototype.BindingType={Direct:0,EntireArray:1,ArrayElement:2,HasFromToArray:3};wt.prototype.Versioning={None:0,NeedsUpdate:1,MatrixWorldNeedsUpdate:2};wt.prototype.GetterByBindingType=[wt.prototype._getValue_direct,wt.prototype._getValue_array,wt.prototype._getValue_arrayElement,wt.prototype._getValue_toArray];wt.prototype.SetterByBindingTypeAndVersioning=[[wt.prototype._setValue_direct,wt.prototype._setValue_direct_setNeedsUpdate,wt.prototype._setValue_direct_setMatrixWorldNeedsUpdate],[wt.prototype._setValue_array,wt.prototype._setValue_array_setNeedsUpdate,wt.prototype._setValue_array_setMatrixWorldNeedsUpdate],[wt.prototype._setValue_arrayElement,wt.prototype._setValue_arrayElement_setNeedsUpdate,wt.prototype._setValue_arrayElement_setMatrixWorldNeedsUpdate],[wt.prototype._setValue_fromArray,wt.prototype._setValue_fromArray_setNeedsUpdate,wt.prototype._setValue_fromArray_setMatrixWorldNeedsUpdate]];var y_=new Float32Array(1);var bu=new ut,wr=class{constructor(e,t,n=0,s=1/0){this.ray=new Ui(e,t),this.near=n,this.far=s,this.camera=null,this.layers=new xs,this.params={Mesh:{},Line:{threshold:1},LOD:{},Points:{threshold:1},Sprite:{}}}set(e,t){this.ray.set(e,t)}setFromCamera(e,t){t.isPerspectiveCamera?(this.ray.origin.setFromMatrixPosition(t.matrixWorld),this.ray.direction.set(e.x,e.y,.5).unproject(t).sub(this.ray.origin).normalize(),this.camera=t):t.isOrthographicCamera?(this.ray.origin.set(e.x,e.y,t.projectionMatrix.elements[14]).unproject(t),this.ray.direction.set(0,0,-1).transformDirection(t.matrixWorld),this.camera=t):Xe("Raycaster: Unsupported camera type: "+t.type)}setFromXRController(e){return bu.identity().extractRotation(e.matrixWorld),this.ray.origin.setFromMatrixPosition(e.matrixWorld),this.ray.direction.set(0,0,-1).applyMatrix4(bu),this}intersectObject(e,t=!0,n=[]){return ec(e,this,n,t),n.sort(Mu),n}intersectObjects(e,t=!0,n=[]){for(let s=0,r=e.length;s<r;s++)ec(e[s],this,n,t);return n.sort(Mu),n}};function Mu(i,e){return i.distance-e.distance}function ec(i,e,t,n){let s=!0;if(i.layers.test(e.layers)&&i.raycast(e,t)===!1&&(s=!1),s===!0&&n===!0){let r=i.children;for(let a=0,o=r.length;a<o;a++)ec(r[a],e,t,!0)}}var tc=class i{static{i.prototype.isMatrix2=!0}constructor(e,t,n,s){this.elements=[1,0,0,1],e!==void 0&&this.set(e,t,n,s)}identity(){return this.set(1,0,0,1),this}fromArray(e,t=0){for(let n=0;n<4;n++)this.elements[n]=e[n+t];return this}set(e,t,n,s){let r=this.elements;return r[0]=e,r[2]=t,r[1]=n,r[3]=s,this}};function Mc(i,e,t,n){let s=lf(n);switch(t){case dc:return i*e;case vo:return i*e/s.components*s.byteLength;case yo:return i*e/s.components*s.byteLength;case Ti:return i*e*2/s.components*s.byteLength;case bo:return i*e*2/s.components*s.byteLength;case fc:return i*e*3/s.components*s.byteLength;case Tn:return i*e*4/s.components*s.byteLength;case Mo:return i*e*4/s.components*s.byteLength;case Fr:case kr:return Math.floor((i+3)/4)*Math.floor((e+3)/4)*8;case Or:case Br:return Math.floor((i+3)/4)*Math.floor((e+3)/4)*16;case To:case wo:return Math.max(i,16)*Math.max(e,8)/4;case So:case Eo:return Math.max(i,8)*Math.max(e,8)/2;case Ao:case Co:case Io:case Po:return Math.floor((i+3)/4)*Math.floor((e+3)/4)*8;case Ro:case zr:case Lo:return Math.floor((i+3)/4)*Math.floor((e+3)/4)*16;case No:return Math.floor((i+3)/4)*Math.floor((e+3)/4)*16;case Do:return Math.floor((i+4)/5)*Math.floor((e+3)/4)*16;case Uo:return Math.floor((i+4)/5)*Math.floor((e+4)/5)*16;case Fo:return Math.floor((i+5)/6)*Math.floor((e+4)/5)*16;case ko:return Math.floor((i+5)/6)*Math.floor((e+5)/6)*16;case Oo:return Math.floor((i+7)/8)*Math.floor((e+4)/5)*16;case Bo:return Math.floor((i+7)/8)*Math.floor((e+5)/6)*16;case zo:return Math.floor((i+7)/8)*Math.floor((e+7)/8)*16;case Vo:return Math.floor((i+9)/10)*Math.floor((e+4)/5)*16;case Ho:return Math.floor((i+9)/10)*Math.floor((e+5)/6)*16;case Go:return Math.floor((i+9)/10)*Math.floor((e+7)/8)*16;case Wo:return Math.floor((i+9)/10)*Math.floor((e+9)/10)*16;case $o:return Math.floor((i+11)/12)*Math.floor((e+9)/10)*16;case qo:return Math.floor((i+11)/12)*Math.floor((e+11)/12)*16;case Xo:case Yo:case Zo:return Math.ceil(i/4)*Math.ceil(e/4)*16;case jo:case Jo:return Math.ceil(i/4)*Math.ceil(e/4)*8;case Vr:case Ko:return Math.ceil(i/4)*Math.ceil(e/4)*16}throw new Error(`Unable to determine texture byte length for ${t} format.`)}function lf(i){switch(i){case un:case lc:return{byteLength:1,components:1};case Rs:case cc:case jt:return{byteLength:2,components:1};case _o:case xo:return{byteLength:2,components:4};case Un:case go:case Sn:return{byteLength:4,components:1};case uc:case hc:return{byteLength:4,components:3}}throw new Error(`THREE.TextureUtils: Unknown texture type ${i}.`)}typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("register",{detail:{revision:"186"}}));typeof window<"u"&&(window.__THREE__?$e("WARNING: Multiple instances of Three.js being imported."):window.__THREE__="186");function Ph(){let i=null,e=!1,t=null,n=null;function s(r,a){n=i.requestAnimationFrame(s),t(r,a)}return{start:function(){e!==!0&&t!==null&&i!==null&&(n=i.requestAnimationFrame(s),e=!0)},stop:function(){i!==null&&i.cancelAnimationFrame(n),e=!1},setAnimationLoop:function(r){t=r},setContext:function(r){i=r}}}function uf(i){let e=new WeakMap;function t(o,l){let c=o.array,h=o.usage,f=c.byteLength,u=i.createBuffer();i.bindBuffer(l,u),i.bufferData(l,c,h),o.onUploadCallback();let d;if(c instanceof Float32Array)d=i.FLOAT;else if(typeof Float16Array<"u"&&c instanceof Float16Array)d=i.HALF_FLOAT;else if(c instanceof Uint16Array)o.isFloat16BufferAttribute?d=i.HALF_FLOAT:d=i.UNSIGNED_SHORT;else if(c instanceof Int16Array)d=i.SHORT;else if(c instanceof Uint32Array)d=i.UNSIGNED_INT;else if(c instanceof Int32Array)d=i.INT;else if(c instanceof Int8Array)d=i.BYTE;else if(c instanceof Uint8Array)d=i.UNSIGNED_BYTE;else if(c instanceof Uint8ClampedArray)d=i.UNSIGNED_BYTE;else throw new Error("THREE.WebGLAttributes: Unsupported buffer data format: "+c);return{buffer:u,type:d,bytesPerElement:c.BYTES_PER_ELEMENT,version:o.version,size:f}}function n(o,l,c){let h=l.array,f=l.updateRanges;if(i.bindBuffer(c,o),f.length===0)i.bufferSubData(c,0,h);else{f.sort((d,_)=>d.start-_.start);let u=0;for(let d=1;d<f.length;d++){let _=f[u],S=f[d];S.start<=_.start+_.count+1?_.count=Math.max(_.count,S.start+S.count-_.start):(++u,f[u]=S)}f.length=u+1;for(let d=0,_=f.length;d<_;d++){let S=f[d];i.bufferSubData(c,S.start*h.BYTES_PER_ELEMENT,h,S.start,S.count)}l.clearUpdateRanges()}l.onUploadCallback()}function s(o){return o.isInterleavedBufferAttribute&&(o=o.data),e.get(o)}function r(o){o.isInterleavedBufferAttribute&&(o=o.data);let l=e.get(o);l&&(i.deleteBuffer(l.buffer),e.delete(o))}function a(o,l){if(o.isInterleavedBufferAttribute&&(o=o.data),o.isGLBufferAttribute){let h=e.get(o);(!h||h.version<o.version)&&e.set(o,{buffer:o.buffer,type:o.type,bytesPerElement:o.elementSize,version:o.version});return}let c=e.get(o);if(c===void 0)e.set(o,t(o,l));else if(c.version<o.version){if(c.size!==o.array.byteLength)throw new Error("THREE.WebGLAttributes: The size of the buffer attribute's array buffer does not match the original size. Resizing buffer attributes is not supported.");n(c.buffer,o,l),c.version=o.version}}return{get:s,remove:r,update:a}}var hf=`#ifdef USE_ALPHAHASH
	if ( diffuseColor.a < getAlphaHashThreshold( vPosition ) ) discard;
#endif`,df=`#ifdef USE_ALPHAHASH
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
#endif`,ff=`#ifdef USE_ALPHAMAP
	diffuseColor.a *= texture2D( alphaMap, vAlphaMapUv ).g;
#endif`,pf=`#ifdef USE_ALPHAMAP
	uniform sampler2D alphaMap;
#endif`,mf=`#ifdef USE_ALPHATEST
	#ifdef ALPHA_TO_COVERAGE
	diffuseColor.a = smoothstep( alphaTest, alphaTest + fwidth( diffuseColor.a ), diffuseColor.a );
	if ( diffuseColor.a == 0.0 ) discard;
	#else
	if ( diffuseColor.a < alphaTest ) discard;
	#endif
#endif`,gf=`#ifdef USE_ALPHATEST
	uniform float alphaTest;
#endif`,_f=`#ifdef USE_AOMAP
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
#endif`,xf=`#ifdef USE_AOMAP
	uniform sampler2D aoMap;
	uniform float aoMapIntensity;
#endif`,vf=`#ifdef USE_BATCHING
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
#endif`,yf=`#ifdef USE_BATCHING
	mat4 batchingMatrix = getBatchingMatrix( getIndirectIndex( gl_DrawID ) );
#endif`,bf=`vec3 transformed = vec3( position );
#ifdef USE_ALPHAHASH
	vPosition = vec3( position );
#endif`,Mf=`vec3 objectNormal = vec3( normal );
#ifdef USE_TANGENT
	vec3 objectTangent = vec3( tangent.xyz );
#endif`,Sf=`float G_BlinnPhong_Implicit( ) {
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
} // validated`,Tf=`#ifdef USE_IRIDESCENCE
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
#endif`,Ef=`#ifdef USE_BUMPMAP
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
#endif`,wf=`#if NUM_CLIPPING_PLANES > 0
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
#endif`,Af=`#if NUM_CLIPPING_PLANES > 0
	varying vec3 vClipPosition;
	uniform vec4 clippingPlanes[ NUM_CLIPPING_PLANES ];
#endif`,Cf=`#if NUM_CLIPPING_PLANES > 0
	varying vec3 vClipPosition;
#endif`,Rf=`#if NUM_CLIPPING_PLANES > 0
	vClipPosition = - mvPosition.xyz;
#endif`,If=`#if defined( USE_COLOR ) || defined( USE_COLOR_ALPHA )
	diffuseColor *= vColor;
#endif`,Pf=`#if defined( USE_COLOR ) || defined( USE_COLOR_ALPHA )
	varying vec4 vColor;
#endif`,Lf=`#if defined( USE_COLOR ) || defined( USE_COLOR_ALPHA ) || defined( USE_INSTANCING_COLOR ) || defined( USE_BATCHING_COLOR )
	varying vec4 vColor;
#endif`,Nf=`#if defined( USE_COLOR ) || defined( USE_COLOR_ALPHA ) || defined( USE_INSTANCING_COLOR ) || defined( USE_BATCHING_COLOR )
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
#endif`,Df=`#define PI 3.141592653589793
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
} // validated`,Uf=`#ifdef ENVMAP_TYPE_CUBE_UV
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
#endif`,Ff=`vec3 transformedNormal = objectNormal;
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
#endif`,kf=`#ifdef USE_DISPLACEMENTMAP
	uniform sampler2D displacementMap;
	uniform float displacementScale;
	uniform float displacementBias;
#endif`,Of=`#ifdef USE_DISPLACEMENTMAP
	transformed += normalize( objectNormal ) * ( texture2D( displacementMap, vDisplacementMapUv ).x * displacementScale + displacementBias );
#endif`,Bf=`#ifdef USE_EMISSIVEMAP
	vec4 emissiveColor = texture2D( emissiveMap, vEmissiveMapUv );
	#ifdef DECODE_VIDEO_TEXTURE_EMISSIVE
		emissiveColor = sRGBTransferEOTF( emissiveColor );
	#endif
	totalEmissiveRadiance *= emissiveColor.rgb;
#endif`,zf=`#ifdef USE_EMISSIVEMAP
	uniform sampler2D emissiveMap;
#endif`,Vf="gl_FragColor = linearToOutputTexel( gl_FragColor );",Hf=`vec4 LinearTransferOETF( in vec4 value ) {
	return value;
}
vec4 sRGBTransferEOTF( in vec4 value ) {
	return vec4( mix( pow( value.rgb * 0.9478672986 + vec3( 0.0521327014 ), vec3( 2.4 ) ), value.rgb * 0.0773993808, vec3( lessThanEqual( value.rgb, vec3( 0.04045 ) ) ) ), value.a );
}
vec4 sRGBTransferOETF( in vec4 value ) {
	return vec4( mix( pow( value.rgb, vec3( 0.41666 ) ) * 1.055 - vec3( 0.055 ), value.rgb * 12.92, vec3( lessThanEqual( value.rgb, vec3( 0.0031308 ) ) ) ), value.a );
}`,Gf=`#ifdef USE_ENVMAP
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
#endif`,Wf=`#ifdef USE_ENVMAP
	uniform float envMapIntensity;
	uniform mat3 envMapRotation;
	#ifdef ENVMAP_TYPE_CUBE
		uniform samplerCube envMap;
	#else
		uniform sampler2D envMap;
	#endif
#endif`,$f=`#ifdef USE_ENVMAP
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
#endif`,qf=`#ifdef USE_ENVMAP
	#if defined( USE_BUMPMAP ) || defined( USE_NORMALMAP ) || defined( PHONG ) || defined( LAMBERT )
		#define ENV_WORLDPOS
	#endif
	#ifdef ENV_WORLDPOS

		varying vec3 vWorldPosition;
	#else
		varying vec3 vReflect;
		uniform float refractionRatio;
	#endif
#endif`,Xf=`#ifdef USE_ENVMAP
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
#endif`,Yf=`#ifdef USE_FOG
	vFogDepth = - mvPosition.z;
#endif`,Zf=`#ifdef USE_FOG
	varying float vFogDepth;
#endif`,jf=`#ifdef USE_FOG
	#ifdef FOG_EXP2
		float fogFactor = 1.0 - exp( - fogDensity * fogDensity * vFogDepth * vFogDepth );
	#else
		float fogFactor = smoothstep( fogNear, fogFar, vFogDepth );
	#endif
	gl_FragColor.rgb = mix( gl_FragColor.rgb, fogColor, fogFactor );
#endif`,Jf=`#ifdef USE_FOG
	uniform vec3 fogColor;
	varying float vFogDepth;
	#ifdef FOG_EXP2
		uniform float fogDensity;
	#else
		uniform float fogNear;
		uniform float fogFar;
	#endif
#endif`,Kf=`#ifdef USE_GRADIENTMAP
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
}`,Qf=`#ifdef USE_LIGHTMAP
	uniform sampler2D lightMap;
	uniform float lightMapIntensity;
#endif`,ep=`LambertMaterial material;
material.diffuseColor = diffuseColor.rgb;
material.specularStrength = specularStrength;`,tp=`varying vec3 vViewPosition;
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
#define RE_IndirectDiffuse		RE_IndirectDiffuse_Lambert`,np=`uniform bool receiveShadow;
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
#include <lightprobes_pars_fragment>`,ip=`#ifdef USE_ENVMAP
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
#endif`,sp=`ToonMaterial material;
material.diffuseColor = diffuseColor.rgb;`,rp=`varying vec3 vViewPosition;
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
#define RE_IndirectDiffuse		RE_IndirectDiffuse_Toon`,ap=`BlinnPhongMaterial material;
material.diffuseColor = diffuseColor.rgb;
material.specularColor = specular;
material.specularShininess = shininess;
material.specularStrength = specularStrength;`,op=`varying vec3 vViewPosition;
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
#define RE_IndirectDiffuse		RE_IndirectDiffuse_BlinnPhong`,lp=`PhysicalMaterial material;
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
#endif`,cp=`uniform sampler2D dfgLUT;
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
}`,up=`
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
#endif`,hp=`#if defined( RE_IndirectDiffuse )
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
#endif`,dp=`#if defined( RE_IndirectDiffuse )
	#if defined( LAMBERT ) || defined( PHONG )
		irradiance += iblIrradiance;
	#endif
	RE_IndirectDiffuse( irradiance, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
#endif
#if defined( RE_IndirectSpecular )
	RE_IndirectSpecular( radiance, iblIrradiance, clearcoatRadiance, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
#endif`,fp=`#ifdef USE_LIGHT_PROBES_GRID
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
#endif`,pp=`#if defined( USE_LOGARITHMIC_DEPTH_BUFFER )
	gl_FragDepth = vIsPerspective == 0.0 ? gl_FragCoord.z : log2( vFragDepth ) * logDepthBufFC * 0.5;
#endif`,mp=`#if defined( USE_LOGARITHMIC_DEPTH_BUFFER )
	uniform float logDepthBufFC;
	varying float vFragDepth;
	varying float vIsPerspective;
#endif`,gp=`#ifdef USE_LOGARITHMIC_DEPTH_BUFFER
	varying float vFragDepth;
	varying float vIsPerspective;
#endif`,_p=`#ifdef USE_LOGARITHMIC_DEPTH_BUFFER
	vFragDepth = 1.0 + gl_Position.w;
	vIsPerspective = float( isPerspectiveMatrix( projectionMatrix ) );
#endif`,xp=`#ifdef USE_MAP
	vec4 sampledDiffuseColor = texture2D( map, vMapUv );
	#ifdef DECODE_VIDEO_TEXTURE
		sampledDiffuseColor = sRGBTransferEOTF( sampledDiffuseColor );
	#endif
	diffuseColor *= sampledDiffuseColor;
#endif`,vp=`#ifdef USE_MAP
	uniform sampler2D map;
#endif`,yp=`#if defined( USE_MAP ) || defined( USE_ALPHAMAP )
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
#endif`,bp=`#if defined( USE_POINTS_UV )
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
#endif`,Mp=`float metalnessFactor = metalness;
#ifdef USE_METALNESSMAP
	vec4 texelMetalness = texture2D( metalnessMap, vMetalnessMapUv );
	metalnessFactor *= texelMetalness.b;
#endif`,Sp=`#ifdef USE_METALNESSMAP
	uniform sampler2D metalnessMap;
#endif`,Tp=`#ifdef USE_INSTANCING_MORPH
	float morphTargetInfluences[ MORPHTARGETS_COUNT ];
	float morphTargetBaseInfluence = texelFetch( morphTexture, ivec2( 0, gl_InstanceID ), 0 ).r;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		morphTargetInfluences[i] =  texelFetch( morphTexture, ivec2( i + 1, gl_InstanceID ), 0 ).r;
	}
#endif`,Ep=`#if defined( USE_MORPHCOLORS )
	vColor *= morphTargetBaseInfluence;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		#if defined( USE_COLOR_ALPHA )
			if ( morphTargetInfluences[ i ] != 0.0 ) vColor += getMorph( gl_VertexID, i, 2 ) * morphTargetInfluences[ i ];
		#elif defined( USE_COLOR )
			if ( morphTargetInfluences[ i ] != 0.0 ) vColor += getMorph( gl_VertexID, i, 2 ).rgb * morphTargetInfluences[ i ];
		#endif
	}
#endif`,wp=`#ifdef USE_MORPHNORMALS
	objectNormal *= morphTargetBaseInfluence;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		if ( morphTargetInfluences[ i ] != 0.0 ) objectNormal += getMorph( gl_VertexID, i, 1 ).xyz * morphTargetInfluences[ i ];
	}
#endif`,Ap=`#ifdef USE_MORPHTARGETS
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
#endif`,Cp=`#ifdef USE_MORPHTARGETS
	transformed *= morphTargetBaseInfluence;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		if ( morphTargetInfluences[ i ] != 0.0 ) transformed += getMorph( gl_VertexID, i, 0 ).xyz * morphTargetInfluences[ i ];
	}
#endif`,Rp=`float faceDirection = gl_FrontFacing ? 1.0 : - 1.0;
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
vec3 nonPerturbedNormal = normal;`,Ip=`#ifdef USE_NORMALMAP_OBJECTSPACE
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
#endif`,Pp=`#ifndef FLAT_SHADED
	varying vec3 vNormal;
	#ifdef USE_TANGENT
		varying vec3 vTangent;
		varying vec3 vBitangent;
	#endif
#endif`,Lp=`#ifndef FLAT_SHADED
	varying vec3 vNormal;
	#ifdef USE_TANGENT
		varying vec3 vTangent;
		varying vec3 vBitangent;
	#endif
#endif`,Np=`#ifndef FLAT_SHADED
	vNormal = normalize( transformedNormal );
	#ifdef USE_TANGENT
		vTangent = normalize( transformedTangent );
		vBitangent = normalize( cross( vNormal, vTangent ) * tangent.w );
		#ifdef FLIP_SIDED
			vBitangent = - vBitangent;
		#endif
	#endif
#endif`,Dp=`#ifdef USE_NORMALMAP
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
#endif`,Up=`#ifdef USE_CLEARCOAT
	vec3 clearcoatNormal = nonPerturbedNormal;
#endif`,Fp=`#ifdef USE_CLEARCOAT_NORMALMAP
	vec3 clearcoatMapN = texture2D( clearcoatNormalMap, vClearcoatNormalMapUv ).xyz * 2.0 - 1.0;
	clearcoatMapN.xy *= clearcoatNormalScale;
	clearcoatNormal = normalize( tbn2 * clearcoatMapN );
#endif`,kp=`#ifdef USE_CLEARCOATMAP
	uniform sampler2D clearcoatMap;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	uniform sampler2D clearcoatNormalMap;
	uniform vec2 clearcoatNormalScale;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	uniform sampler2D clearcoatRoughnessMap;
#endif`,Op=`#ifdef USE_IRIDESCENCEMAP
	uniform sampler2D iridescenceMap;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	uniform sampler2D iridescenceThicknessMap;
#endif`,Bp=`#ifdef OPAQUE
diffuseColor.a = 1.0;
#endif
#ifdef USE_TRANSMISSION
diffuseColor.a *= material.transmissionAlpha;
#endif
gl_FragColor = vec4( outgoingLight, diffuseColor.a );`,zp=`vec3 packNormalToRGB( const in vec3 normal ) {
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
}`,Vp=`#ifdef PREMULTIPLIED_ALPHA
	gl_FragColor.rgb *= gl_FragColor.a;
#endif`,Hp=`vec4 mvPosition = vec4( transformed, 1.0 );
#ifdef USE_BATCHING
	mvPosition = batchingMatrix * mvPosition;
#endif
#ifdef USE_INSTANCING
	mvPosition = instanceMatrix * mvPosition;
#endif
mvPosition = modelViewMatrix * mvPosition;
gl_Position = projectionMatrix * mvPosition;`,Gp=`#ifdef DITHERING
	gl_FragColor.rgb = dithering( gl_FragColor.rgb );
#endif`,Wp=`#ifdef DITHERING
	vec3 dithering( vec3 color ) {
		float grid_position = rand( gl_FragCoord.xy );
		vec3 dither_shift_RGB = vec3( 0.25 / 255.0, -0.25 / 255.0, 0.25 / 255.0 );
		dither_shift_RGB = mix( 2.0 * dither_shift_RGB, -2.0 * dither_shift_RGB, grid_position );
		return color + dither_shift_RGB;
	}
#endif`,$p=`float roughnessFactor = roughness;
#ifdef USE_ROUGHNESSMAP
	vec4 texelRoughness = texture2D( roughnessMap, vRoughnessMapUv );
	roughnessFactor *= texelRoughness.g;
#endif`,qp=`#ifdef USE_ROUGHNESSMAP
	uniform sampler2D roughnessMap;
#endif`,Xp=`#if NUM_SPOT_LIGHT_COORDS > 0
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
#endif`,Yp=`#if NUM_SPOT_LIGHT_COORDS > 0
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
#endif`,Zp=`#if ( defined( USE_SHADOWMAP ) && ( NUM_DIR_LIGHT_SHADOWS > 0 || NUM_SUN_LIGHT_SHADOWS > 0 || NUM_POINT_LIGHT_SHADOWS > 0 ) ) || ( NUM_SPOT_LIGHT_COORDS > 0 )
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
#endif`,jp=`float getShadowMask() {
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
}`,Jp=`#ifdef USE_SKINNING
	mat4 boneMatX = getBoneMatrix( skinIndex.x );
	mat4 boneMatY = getBoneMatrix( skinIndex.y );
	mat4 boneMatZ = getBoneMatrix( skinIndex.z );
	mat4 boneMatW = getBoneMatrix( skinIndex.w );
#endif`,Kp=`#ifdef USE_SKINNING
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
#endif`,Qp=`#ifdef USE_SKINNING
	vec4 skinVertex = bindMatrix * vec4( transformed, 1.0 );
	vec4 skinned = vec4( 0.0 );
	skinned += boneMatX * skinVertex * skinWeight.x;
	skinned += boneMatY * skinVertex * skinWeight.y;
	skinned += boneMatZ * skinVertex * skinWeight.z;
	skinned += boneMatW * skinVertex * skinWeight.w;
	transformed = ( bindMatrixInverse * skinned ).xyz;
#endif`,em=`#ifdef USE_SKINNING
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
#endif`,tm=`float specularStrength;
#ifdef USE_SPECULARMAP
	vec4 texelSpecular = texture2D( specularMap, vSpecularMapUv );
	specularStrength = texelSpecular.r;
#else
	specularStrength = 1.0;
#endif`,nm=`#ifdef USE_SPECULARMAP
	uniform sampler2D specularMap;
#endif`,im=`#if defined( TONE_MAPPING )
	gl_FragColor.rgb = toneMapping( gl_FragColor.rgb );
#endif`,sm=`#ifndef saturate
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
vec3 CustomToneMapping( vec3 color ) { return color; }`,rm=`#ifdef USE_TRANSMISSION
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
#endif`,am=`#ifdef USE_TRANSMISSION
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
#endif`,om=`#if defined( USE_UV ) || defined( USE_ANISOTROPY )
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
#endif`,lm=`#if defined( USE_UV ) || defined( USE_ANISOTROPY )
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
#endif`,cm=`#if defined( USE_UV ) || defined( USE_ANISOTROPY )
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
#endif`,um=`#if defined( USE_ENVMAP ) || defined( DISTANCE ) || defined ( USE_SHADOWMAP ) || defined ( USE_TRANSMISSION ) || NUM_SPOT_LIGHT_COORDS > 0
	vec4 worldPosition = vec4( transformed, 1.0 );
	#ifdef USE_BATCHING
		worldPosition = batchingMatrix * worldPosition;
	#endif
	#ifdef USE_INSTANCING
		worldPosition = instanceMatrix * worldPosition;
	#endif
	worldPosition = modelMatrix * worldPosition;
#endif`,hm=`varying vec2 vUv;
uniform mat3 uvTransform;
void main() {
	vUv = ( uvTransform * vec3( uv, 1 ) ).xy;
	gl_Position = vec4( position.xy, 1.0, 1.0 );
}`,dm=`uniform sampler2D t2D;
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
}`,fm=`varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
	gl_Position.z = gl_Position.w;
}`,pm=`#ifdef ENVMAP_TYPE_CUBE
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
}`,mm=`varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
	gl_Position.z = gl_Position.w;
}`,gm=`uniform samplerCube tCube;
uniform float tFlip;
uniform float opacity;
varying vec3 vWorldDirection;
void main() {
	vec4 texColor = textureCube( tCube, vec3( tFlip * vWorldDirection.x, vWorldDirection.yz ) );
	gl_FragColor = texColor;
	gl_FragColor.a *= opacity;
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,_m=`#include <common>
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
}`,xm=`#if DEPTH_PACKING == 3200
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
}`,vm=`#define DISTANCE
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
}`,ym=`#define DISTANCE
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
}`,bm=`varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
}`,Mm=`uniform sampler2D tEquirect;
varying vec3 vWorldDirection;
#include <common>
void main() {
	vec3 direction = normalize( vWorldDirection );
	vec2 sampleUV = equirectUv( direction );
	gl_FragColor = texture2D( tEquirect, sampleUV );
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,Sm=`uniform float scale;
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
}`,Tm=`uniform vec3 diffuse;
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
}`,Em=`#include <common>
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
}`,wm=`uniform vec3 diffuse;
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
}`,Am=`#define LAMBERT
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
}`,Cm=`#define LAMBERT
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
}`,Rm=`#define MATCAP
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
}`,Im=`#define MATCAP
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
}`,Pm=`#define NORMAL
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
}`,Lm=`#define NORMAL
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
}`,Nm=`#define PHONG
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
}`,Dm=`#define PHONG
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
}`,Um=`#define STANDARD
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
}`,Fm=`#define STANDARD
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
}`,km=`#define TOON
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
}`,Om=`#define TOON
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
}`,Bm=`uniform float size;
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
}`,zm=`uniform vec3 diffuse;
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
}`,Vm=`#include <common>
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
}`,Hm=`uniform vec3 color;
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
}`,Gm=`uniform float rotation;
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
}`,Wm=`uniform vec3 diffuse;
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
}`,nt={alphahash_fragment:hf,alphahash_pars_fragment:df,alphamap_fragment:ff,alphamap_pars_fragment:pf,alphatest_fragment:mf,alphatest_pars_fragment:gf,aomap_fragment:_f,aomap_pars_fragment:xf,batching_pars_vertex:vf,batching_vertex:yf,begin_vertex:bf,beginnormal_vertex:Mf,bsdfs:Sf,iridescence_fragment:Tf,bumpmap_pars_fragment:Ef,clipping_planes_fragment:wf,clipping_planes_pars_fragment:Af,clipping_planes_pars_vertex:Cf,clipping_planes_vertex:Rf,color_fragment:If,color_pars_fragment:Pf,color_pars_vertex:Lf,color_vertex:Nf,common:Df,cube_uv_reflection_fragment:Uf,defaultnormal_vertex:Ff,displacementmap_pars_vertex:kf,displacementmap_vertex:Of,emissivemap_fragment:Bf,emissivemap_pars_fragment:zf,colorspace_fragment:Vf,colorspace_pars_fragment:Hf,envmap_fragment:Gf,envmap_common_pars_fragment:Wf,envmap_pars_fragment:$f,envmap_pars_vertex:qf,envmap_physical_pars_fragment:ip,envmap_vertex:Xf,fog_vertex:Yf,fog_pars_vertex:Zf,fog_fragment:jf,fog_pars_fragment:Jf,gradientmap_pars_fragment:Kf,lightmap_pars_fragment:Qf,lights_lambert_fragment:ep,lights_lambert_pars_fragment:tp,lights_pars_begin:np,lights_toon_fragment:sp,lights_toon_pars_fragment:rp,lights_phong_fragment:ap,lights_phong_pars_fragment:op,lights_physical_fragment:lp,lights_physical_pars_fragment:cp,lights_fragment_begin:up,lights_fragment_maps:hp,lights_fragment_end:dp,lightprobes_pars_fragment:fp,logdepthbuf_fragment:pp,logdepthbuf_pars_fragment:mp,logdepthbuf_pars_vertex:gp,logdepthbuf_vertex:_p,map_fragment:xp,map_pars_fragment:vp,map_particle_fragment:yp,map_particle_pars_fragment:bp,metalnessmap_fragment:Mp,metalnessmap_pars_fragment:Sp,morphinstance_vertex:Tp,morphcolor_vertex:Ep,morphnormal_vertex:wp,morphtarget_pars_vertex:Ap,morphtarget_vertex:Cp,normal_fragment_begin:Rp,normal_fragment_maps:Ip,normal_pars_fragment:Pp,normal_pars_vertex:Lp,normal_vertex:Np,normalmap_pars_fragment:Dp,clearcoat_normal_fragment_begin:Up,clearcoat_normal_fragment_maps:Fp,clearcoat_pars_fragment:kp,iridescence_pars_fragment:Op,opaque_fragment:Bp,packing:zp,premultiplied_alpha_fragment:Vp,project_vertex:Hp,dithering_fragment:Gp,dithering_pars_fragment:Wp,roughnessmap_fragment:$p,roughnessmap_pars_fragment:qp,shadowmap_pars_fragment:Xp,shadowmap_pars_vertex:Yp,shadowmap_vertex:Zp,shadowmask_pars_fragment:jp,skinbase_vertex:Jp,skinning_pars_vertex:Kp,skinning_vertex:Qp,skinnormal_vertex:em,specularmap_fragment:tm,specularmap_pars_fragment:nm,tonemapping_fragment:im,tonemapping_pars_fragment:sm,transmission_fragment:rm,transmission_pars_fragment:am,uv_pars_fragment:om,uv_pars_vertex:lm,uv_vertex:cm,worldpos_vertex:um,background_vert:hm,background_frag:dm,backgroundCube_vert:fm,backgroundCube_frag:pm,cube_vert:mm,cube_frag:gm,depth_vert:_m,depth_frag:xm,distance_vert:vm,distance_frag:ym,equirect_vert:bm,equirect_frag:Mm,linedashed_vert:Sm,linedashed_frag:Tm,meshbasic_vert:Em,meshbasic_frag:wm,meshlambert_vert:Am,meshlambert_frag:Cm,meshmatcap_vert:Rm,meshmatcap_frag:Im,meshnormal_vert:Pm,meshnormal_frag:Lm,meshphong_vert:Nm,meshphong_frag:Dm,meshphysical_vert:Um,meshphysical_frag:Fm,meshtoon_vert:km,meshtoon_frag:Om,points_vert:Bm,points_frag:zm,shadow_vert:Vm,shadow_frag:Hm,sprite_vert:Gm,sprite_frag:Wm},Le={common:{diffuse:{value:new qe(16777215)},opacity:{value:1},map:{value:null},mapTransform:{value:new Ye},alphaMap:{value:null},alphaMapTransform:{value:new Ye},alphaTest:{value:0}},specularmap:{specularMap:{value:null},specularMapTransform:{value:new Ye}},envmap:{envMap:{value:null},envMapRotation:{value:new Ye},reflectivity:{value:1},ior:{value:1.5},refractionRatio:{value:.98},dfgLUT:{value:null}},aomap:{aoMap:{value:null},aoMapIntensity:{value:1},aoMapTransform:{value:new Ye}},lightmap:{lightMap:{value:null},lightMapIntensity:{value:1},lightMapTransform:{value:new Ye}},bumpmap:{bumpMap:{value:null},bumpMapTransform:{value:new Ye},bumpScale:{value:1}},normalmap:{normalMap:{value:null},normalMapTransform:{value:new Ye},normalScale:{value:new De(1,1)}},displacementmap:{displacementMap:{value:null},displacementMapTransform:{value:new Ye},displacementScale:{value:1},displacementBias:{value:0}},emissivemap:{emissiveMap:{value:null},emissiveMapTransform:{value:new Ye}},metalnessmap:{metalnessMap:{value:null},metalnessMapTransform:{value:new Ye}},roughnessmap:{roughnessMap:{value:null},roughnessMapTransform:{value:new Ye}},gradientmap:{gradientMap:{value:null}},fog:{fogDensity:{value:25e-5},fogNear:{value:1},fogFar:{value:2e3},fogColor:{value:new qe(16777215)}},lights:{ambientLightColor:{value:[]},lightProbe:{value:[]},sunLights:{value:[],properties:{direction:{},color:{}}},sunLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{}}},sunShadowMatrix:{value:[]},sunShadowCascade:{value:[]},directionalLights:{value:[],properties:{direction:{},color:{}}},directionalLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{}}},directionalShadowMatrix:{value:[]},spotLights:{value:[],properties:{color:{},position:{},direction:{},distance:{},coneCos:{},penumbraCos:{},decay:{}}},spotLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{}}},spotLightMap:{value:[]},spotLightMatrix:{value:[]},pointLights:{value:[],properties:{color:{},position:{},decay:{},distance:{}}},pointLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{},shadowCameraNear:{},shadowCameraFar:{}}},pointShadowMatrix:{value:[]},hemisphereLights:{value:[],properties:{direction:{},skyColor:{},groundColor:{}}},rectAreaLights:{value:[],properties:{color:{},position:{},width:{},height:{}}},ltc_1:{value:null},ltc_2:{value:null},probesSH:{value:null},probesMin:{value:new B},probesMax:{value:new B},probesResolution:{value:new B}},points:{diffuse:{value:new qe(16777215)},opacity:{value:1},size:{value:1},scale:{value:1},map:{value:null},alphaMap:{value:null},alphaMapTransform:{value:new Ye},alphaTest:{value:0},uvTransform:{value:new Ye}},sprite:{diffuse:{value:new qe(16777215)},opacity:{value:1},center:{value:new De(.5,.5)},rotation:{value:0},map:{value:null},mapTransform:{value:new Ye},alphaMap:{value:null},alphaMapTransform:{value:new Ye},alphaTest:{value:0}}},qn={basic:{uniforms:Qt([Le.common,Le.specularmap,Le.envmap,Le.aomap,Le.lightmap,Le.fog]),vertexShader:nt.meshbasic_vert,fragmentShader:nt.meshbasic_frag},lambert:{uniforms:Qt([Le.common,Le.specularmap,Le.envmap,Le.aomap,Le.lightmap,Le.emissivemap,Le.bumpmap,Le.normalmap,Le.displacementmap,Le.fog,Le.lights,{emissive:{value:new qe(0)},envMapIntensity:{value:1}}]),vertexShader:nt.meshlambert_vert,fragmentShader:nt.meshlambert_frag},phong:{uniforms:Qt([Le.common,Le.specularmap,Le.envmap,Le.aomap,Le.lightmap,Le.emissivemap,Le.bumpmap,Le.normalmap,Le.displacementmap,Le.fog,Le.lights,{emissive:{value:new qe(0)},specular:{value:new qe(1118481)},shininess:{value:30},envMapIntensity:{value:1}}]),vertexShader:nt.meshphong_vert,fragmentShader:nt.meshphong_frag},standard:{uniforms:Qt([Le.common,Le.envmap,Le.aomap,Le.lightmap,Le.emissivemap,Le.bumpmap,Le.normalmap,Le.displacementmap,Le.roughnessmap,Le.metalnessmap,Le.fog,Le.lights,{emissive:{value:new qe(0)},roughness:{value:1},metalness:{value:0},envMapIntensity:{value:1}}]),vertexShader:nt.meshphysical_vert,fragmentShader:nt.meshphysical_frag},toon:{uniforms:Qt([Le.common,Le.aomap,Le.lightmap,Le.emissivemap,Le.bumpmap,Le.normalmap,Le.displacementmap,Le.gradientmap,Le.fog,Le.lights,{emissive:{value:new qe(0)}}]),vertexShader:nt.meshtoon_vert,fragmentShader:nt.meshtoon_frag},matcap:{uniforms:Qt([Le.common,Le.bumpmap,Le.normalmap,Le.displacementmap,Le.fog,{matcap:{value:null}}]),vertexShader:nt.meshmatcap_vert,fragmentShader:nt.meshmatcap_frag},points:{uniforms:Qt([Le.points,Le.fog]),vertexShader:nt.points_vert,fragmentShader:nt.points_frag},dashed:{uniforms:Qt([Le.common,Le.fog,{scale:{value:1},dashSize:{value:1},totalSize:{value:2}}]),vertexShader:nt.linedashed_vert,fragmentShader:nt.linedashed_frag},depth:{uniforms:Qt([Le.common,Le.displacementmap]),vertexShader:nt.depth_vert,fragmentShader:nt.depth_frag},normal:{uniforms:Qt([Le.common,Le.bumpmap,Le.normalmap,Le.displacementmap,{opacity:{value:1}}]),vertexShader:nt.meshnormal_vert,fragmentShader:nt.meshnormal_frag},sprite:{uniforms:Qt([Le.sprite,Le.fog]),vertexShader:nt.sprite_vert,fragmentShader:nt.sprite_frag},background:{uniforms:{uvTransform:{value:new Ye},t2D:{value:null},backgroundIntensity:{value:1}},vertexShader:nt.background_vert,fragmentShader:nt.background_frag},backgroundCube:{uniforms:{envMap:{value:null},backgroundBlurriness:{value:0},backgroundIntensity:{value:1},backgroundRotation:{value:new Ye}},vertexShader:nt.backgroundCube_vert,fragmentShader:nt.backgroundCube_frag},cube:{uniforms:{tCube:{value:null},tFlip:{value:-1},opacity:{value:1}},vertexShader:nt.cube_vert,fragmentShader:nt.cube_frag},equirect:{uniforms:{tEquirect:{value:null}},vertexShader:nt.equirect_vert,fragmentShader:nt.equirect_frag},distance:{uniforms:Qt([Le.common,Le.displacementmap,{referencePosition:{value:new B},nearDistance:{value:1},farDistance:{value:1e3}}]),vertexShader:nt.distance_vert,fragmentShader:nt.distance_frag},shadow:{uniforms:Qt([Le.lights,Le.fog,{color:{value:new qe(0)},opacity:{value:1}}]),vertexShader:nt.shadow_vert,fragmentShader:nt.shadow_frag}};qn.physical={uniforms:Qt([qn.standard.uniforms,{clearcoat:{value:0},clearcoatMap:{value:null},clearcoatMapTransform:{value:new Ye},clearcoatNormalMap:{value:null},clearcoatNormalMapTransform:{value:new Ye},clearcoatNormalScale:{value:new De(1,1)},clearcoatRoughness:{value:0},clearcoatRoughnessMap:{value:null},clearcoatRoughnessMapTransform:{value:new Ye},dispersion:{value:0},retroreflectivity:{value:0},iridescence:{value:0},iridescenceMap:{value:null},iridescenceMapTransform:{value:new Ye},iridescenceIOR:{value:1.3},iridescenceThicknessMinimum:{value:100},iridescenceThicknessMaximum:{value:400},iridescenceThicknessMap:{value:null},iridescenceThicknessMapTransform:{value:new Ye},sheen:{value:0},sheenColor:{value:new qe(0)},sheenColorMap:{value:null},sheenColorMapTransform:{value:new Ye},sheenRoughness:{value:1},sheenRoughnessMap:{value:null},sheenRoughnessMapTransform:{value:new Ye},transmission:{value:0},transmissionMap:{value:null},transmissionMapTransform:{value:new Ye},transmissionSamplerSize:{value:new De},transmissionSamplerMap:{value:null},thickness:{value:0},thicknessMap:{value:null},thicknessMapTransform:{value:new Ye},attenuationDistance:{value:0},attenuationColor:{value:new qe(0)},specularColor:{value:new qe(1,1,1)},specularColorMap:{value:null},specularColorMapTransform:{value:new Ye},specularIntensity:{value:1},specularIntensityMap:{value:null},specularIntensityMapTransform:{value:new Ye},anisotropyVector:{value:new De},anisotropyMap:{value:null},anisotropyMapTransform:{value:new Ye}}]),vertexShader:nt.meshphysical_vert,fragmentShader:nt.meshphysical_frag};var nl={r:0,b:0,g:0},$m=new ut,Lh=new Ye;Lh.set(-1,0,0,0,1,0,0,0,1);function qm(i,e,t,n,s,r){let a=new qe(0),o=s===!0?0:1,l,c,h=null,f=0,u=null;function d(w){let I=w.isScene===!0?w.background:null;if(I&&I.isTexture){let y=w.backgroundBlurriness>0;I=e.get(I,y)}return I}function _(w){let I=!1,y=d(w);y===null?g(a,o):y&&y.isColor&&(g(y,1),I=!0);let A=i.xr.getEnvironmentBlendMode();A==="additive"?t.buffers.color.setClear(0,0,0,1,r):A==="alpha-blend"&&t.buffers.color.setClear(0,0,0,0,r),(i.autoClear||I)&&(t.buffers.depth.setTest(!0),t.buffers.depth.setMask(!0),t.buffers.color.setMask(!0),i.clear(i.autoClearColor,i.autoClearDepth,i.autoClearStencil))}function S(w,I){let y=d(I);y&&(y.isCubeTexture||y.mapping===Dr)?(c===void 0&&(c=new mt(new Nn(1,1,1),new Nt({name:"BackgroundCubeMaterial",uniforms:Gi(qn.backgroundCube.uniforms),vertexShader:qn.backgroundCube.vertexShader,fragmentShader:qn.backgroundCube.fragmentShader,side:Zt,depthTest:!1,depthWrite:!1,fog:!1,allowOverride:!1})),c.geometry.deleteAttribute("normal"),c.geometry.deleteAttribute("uv"),c.onBeforeRender=function(A,E,D){this.matrixWorld.copyPosition(D.matrixWorld)},Object.defineProperty(c.material,"envMap",{get:function(){return this.uniforms.envMap.value}}),n.update(c)),c.material.uniforms.envMap.value=y,c.material.uniforms.backgroundBlurriness.value=I.backgroundBlurriness,c.material.uniforms.backgroundIntensity.value=I.backgroundIntensity,c.material.uniforms.backgroundRotation.value.setFromMatrix4($m.makeRotationFromEuler(I.backgroundRotation)).transpose(),y.isCubeTexture&&y.isRenderTargetTexture===!1&&c.material.uniforms.backgroundRotation.value.premultiply(Lh),c.material.toneMapped=at.getTransfer(y.colorSpace)!==yt,(h!==y||f!==y.version||u!==i.toneMapping)&&(c.material.needsUpdate=!0,h=y,f=y.version,u=i.toneMapping),c.layers.enableAll(),w.unshift(c,c.geometry,c.material,0,0,null)):y&&y.isTexture&&(l===void 0&&(l=new mt(new xr(2,2),new Nt({name:"BackgroundMaterial",uniforms:Gi(qn.background.uniforms),vertexShader:qn.background.vertexShader,fragmentShader:qn.background.fragmentShader,side:yi,depthTest:!1,depthWrite:!1,fog:!1,allowOverride:!1})),l.geometry.deleteAttribute("normal"),Object.defineProperty(l.material,"map",{get:function(){return this.uniforms.t2D.value}}),n.update(l)),l.material.uniforms.t2D.value=y,l.material.uniforms.backgroundIntensity.value=I.backgroundIntensity,l.material.toneMapped=at.getTransfer(y.colorSpace)!==yt,y.matrixAutoUpdate===!0&&y.updateMatrix(),l.material.uniforms.uvTransform.value.copy(y.matrix),(h!==y||f!==y.version||u!==i.toneMapping)&&(l.material.needsUpdate=!0,h=y,f=y.version,u=i.toneMapping),l.layers.enableAll(),w.unshift(l,l.geometry,l.material,0,0,null))}function g(w,I){w.getRGB(nl,vc(i)),t.buffers.color.setClear(nl.r,nl.g,nl.b,I,r)}function p(){c!==void 0&&(c.geometry.dispose(),c.material.dispose(),c=void 0),l!==void 0&&(l.geometry.dispose(),l.material.dispose(),l=void 0)}return{getClearColor:function(){return a},setClearColor:function(w,I=1){a.set(w),o=I,g(a,o)},getClearAlpha:function(){return o},setClearAlpha:function(w){o=w,g(a,o)},render:_,addToRenderList:S,dispose:p}}function Xm(i,e){let t=i.getParameter(i.MAX_VERTEX_ATTRIBS),n={},s=u(null),r=s,a=!1;function o(V,q,j,z,Y){let te=!1,re=f(V,z,j,q);r!==re&&(r=re,c(r.object)),te=d(V,z,j,Y),te&&_(V,z,j,Y),Y!==null&&e.update(Y,i.ELEMENT_ARRAY_BUFFER),(te||a)&&(a=!1,y(V,q,j,z),Y!==null&&i.bindBuffer(i.ELEMENT_ARRAY_BUFFER,e.get(Y).buffer))}function l(){return i.createVertexArray()}function c(V){return i.bindVertexArray(V)}function h(V){return i.deleteVertexArray(V)}function f(V,q,j,z){let Y=z.wireframe===!0,te=n[q.id];te===void 0&&(te={},n[q.id]=te);let re=V.isInstancedMesh===!0?V.id:0,Z=te[re];Z===void 0&&(Z={},te[re]=Z);let Q=Z[j.id];Q===void 0&&(Q={},Z[j.id]=Q);let le=Q[Y];return le===void 0&&(le=u(l()),Q[Y]=le),le}function u(V){let q=[],j=[],z=[];for(let Y=0;Y<t;Y++)q[Y]=0,j[Y]=0,z[Y]=0;return{geometry:null,program:null,wireframe:!1,newAttributes:q,enabledAttributes:j,attributeDivisors:z,object:V,attributes:{},index:null}}function d(V,q,j,z){let Y=r.attributes,te=q.attributes,re=0,Z=j.getAttributes();for(let Q in Z)if(Z[Q].location>=0){let se=Y[Q],Oe=te[Q];if(Oe===void 0&&(Q==="instanceMatrix"&&V.instanceMatrix&&(Oe=V.instanceMatrix),Q==="instanceColor"&&V.instanceColor&&(Oe=V.instanceColor)),se===void 0||se.attribute!==Oe||Oe&&se.data!==Oe.data)return!0;re++}return r.attributesNum!==re||r.index!==z}function _(V,q,j,z){let Y={},te=q.attributes,re=0,Z=j.getAttributes();for(let Q in Z)if(Z[Q].location>=0){let se=te[Q];se===void 0&&(Q==="instanceMatrix"&&V.instanceMatrix&&(se=V.instanceMatrix),Q==="instanceColor"&&V.instanceColor&&(se=V.instanceColor));let Oe={};Oe.attribute=se,se&&se.data&&(Oe.data=se.data),Y[Q]=Oe,re++}r.attributes=Y,r.attributesNum=re,r.index=z}function S(){let V=r.newAttributes;for(let q=0,j=V.length;q<j;q++)V[q]=0}function g(V){p(V,0)}function p(V,q){let j=r.newAttributes,z=r.enabledAttributes,Y=r.attributeDivisors;j[V]=1,z[V]===0&&(i.enableVertexAttribArray(V),z[V]=1),Y[V]!==q&&(i.vertexAttribDivisor(V,q),Y[V]=q)}function w(){let V=r.newAttributes,q=r.enabledAttributes;for(let j=0,z=q.length;j<z;j++)q[j]!==V[j]&&(i.disableVertexAttribArray(j),q[j]=0)}function I(V,q,j,z,Y,te,re){re===!0?i.vertexAttribIPointer(V,q,j,Y,te):i.vertexAttribPointer(V,q,j,z,Y,te)}function y(V,q,j,z){S();let Y=z.attributes,te=j.getAttributes(),re=q.defaultAttributeValues;for(let Z in te){let Q=te[Z];if(Q.location>=0){let le=Y[Z];if(le===void 0&&(Z==="instanceMatrix"&&V.instanceMatrix&&(le=V.instanceMatrix),Z==="instanceColor"&&V.instanceColor&&(le=V.instanceColor)),le!==void 0){let se=le.normalized,Oe=le.itemSize,Ie=e.get(le);if(Ie===void 0)continue;let it=Ie.buffer,Ve=Ie.type,He=Ie.bytesPerElement,ee=Ve===i.INT||Ve===i.UNSIGNED_INT||le.gpuType===go;if(le.isInterleavedBufferAttribute){let ae=le.data,Me=ae.stride,Pe=le.offset;if(ae.isInstancedInterleavedBuffer){for(let we=0;we<Q.locationSize;we++)p(Q.location+we,ae.meshPerAttribute);V.isInstancedMesh!==!0&&z._maxInstanceCount===void 0&&(z._maxInstanceCount=ae.meshPerAttribute*ae.count)}else for(let we=0;we<Q.locationSize;we++)g(Q.location+we);i.bindBuffer(i.ARRAY_BUFFER,it);for(let we=0;we<Q.locationSize;we++)I(Q.location+we,Oe/Q.locationSize,Ve,se,Me*He,(Pe+Oe/Q.locationSize*we)*He,ee)}else{if(le.isInstancedBufferAttribute){for(let ae=0;ae<Q.locationSize;ae++)p(Q.location+ae,le.meshPerAttribute);V.isInstancedMesh!==!0&&z._maxInstanceCount===void 0&&(z._maxInstanceCount=le.meshPerAttribute*le.count)}else for(let ae=0;ae<Q.locationSize;ae++)g(Q.location+ae);i.bindBuffer(i.ARRAY_BUFFER,it);for(let ae=0;ae<Q.locationSize;ae++)I(Q.location+ae,Oe/Q.locationSize,Ve,se,Oe*He,Oe/Q.locationSize*ae*He,ee)}}else if(re!==void 0){let se=re[Z];if(se!==void 0)switch(se.length){case 2:i.vertexAttrib2fv(Q.location,se);break;case 3:i.vertexAttrib3fv(Q.location,se);break;case 4:i.vertexAttrib4fv(Q.location,se);break;default:i.vertexAttrib1fv(Q.location,se)}}}}w()}function A(){C();for(let V in n){let q=n[V];for(let j in q){let z=q[j];for(let Y in z){let te=z[Y];for(let re in te)h(te[re].object),delete te[re];delete z[Y]}}delete n[V]}}function E(V){if(n[V.id]===void 0)return;let q=n[V.id];for(let j in q){let z=q[j];for(let Y in z){let te=z[Y];for(let re in te)h(te[re].object),delete te[re];delete z[Y]}}delete n[V.id]}function D(V){for(let q in n){let j=n[q];for(let z in j){let Y=j[z];if(Y[V.id]===void 0)continue;let te=Y[V.id];for(let re in te)h(te[re].object),delete te[re];delete Y[V.id]}}}function v(V){for(let q in n){let j=n[q],z=V.isInstancedMesh===!0?V.id:0,Y=j[z];if(Y!==void 0){for(let te in Y){let re=Y[te];for(let Z in re)h(re[Z].object),delete re[Z];delete Y[te]}delete j[z],Object.keys(j).length===0&&delete n[q]}}}function C(){O(),a=!0,r!==s&&(r=s,c(r.object))}function O(){s.geometry=null,s.program=null,s.wireframe=!1}return{setup:o,reset:C,resetDefaultState:O,dispose:A,releaseStatesOfGeometry:E,releaseStatesOfObject:v,releaseStatesOfProgram:D,initAttributes:S,enableAttribute:g,disableUnusedAttributes:w}}function Ym(i,e,t){let n;function s(l){n=l}function r(l,c){i.drawArrays(n,l,c),t.update(c,n,1)}function a(l,c,h){h!==0&&(i.drawArraysInstanced(n,l,c,h),t.update(c,n,h))}function o(l,c,h){if(h===0)return;e.get("WEBGL_multi_draw").multiDrawArraysWEBGL(n,l,0,c,0,h);let u=0;for(let d=0;d<h;d++)u+=c[d];t.update(u,n,1)}this.setMode=s,this.render=r,this.renderInstances=a,this.renderMultiDraw=o}function Zm(i,e,t,n){let s;function r(){if(s!==void 0)return s;if(e.has("EXT_texture_filter_anisotropic")===!0){let D=e.get("EXT_texture_filter_anisotropic");s=i.getParameter(D.MAX_TEXTURE_MAX_ANISOTROPY_EXT)}else s=0;return s}function a(D){return!(D!==Tn&&n.convert(D)!==i.getParameter(i.IMPLEMENTATION_COLOR_READ_FORMAT))}function o(D){let v=D===jt&&(e.has("EXT_color_buffer_half_float")||e.has("EXT_color_buffer_float"));return!(D!==un&&D!==Sn&&!v&&n.convert(D)!==i.getParameter(i.IMPLEMENTATION_COLOR_READ_TYPE))}function l(D){if(D==="highp"){if(i.getShaderPrecisionFormat(i.VERTEX_SHADER,i.HIGH_FLOAT).precision>0&&i.getShaderPrecisionFormat(i.FRAGMENT_SHADER,i.HIGH_FLOAT).precision>0)return"highp";D="mediump"}return D==="mediump"&&i.getShaderPrecisionFormat(i.VERTEX_SHADER,i.MEDIUM_FLOAT).precision>0&&i.getShaderPrecisionFormat(i.FRAGMENT_SHADER,i.MEDIUM_FLOAT).precision>0?"mediump":"lowp"}let c=t.precision!==void 0?t.precision:"highp",h=l(c);h!==c&&($e("WebGLRenderer:",c,"not supported, using",h,"instead."),c=h);let f=t.logarithmicDepthBuffer===!0,u=t.reversedDepthBuffer===!0&&e.has("EXT_clip_control");t.reversedDepthBuffer===!0&&u===!1&&$e("WebGLRenderer: Unable to use reversed depth buffer due to missing EXT_clip_control extension. Fallback to default depth buffer.");let d=i.getParameter(i.MAX_TEXTURE_IMAGE_UNITS),_=i.getParameter(i.MAX_VERTEX_TEXTURE_IMAGE_UNITS),S=i.getParameter(i.MAX_TEXTURE_SIZE),g=i.getParameter(i.MAX_CUBE_MAP_TEXTURE_SIZE),p=i.getParameter(i.MAX_VERTEX_ATTRIBS),w=i.getParameter(i.MAX_VERTEX_UNIFORM_VECTORS),I=i.getParameter(i.MAX_VARYING_VECTORS),y=i.getParameter(i.MAX_FRAGMENT_UNIFORM_VECTORS),A=i.getParameter(i.MAX_SAMPLES),E=i.getParameter(i.SAMPLES);return{isWebGL2:!0,getMaxAnisotropy:r,getMaxPrecision:l,textureFormatReadable:a,textureTypeReadable:o,precision:c,logarithmicDepthBuffer:f,reversedDepthBuffer:u,maxTextures:d,maxVertexTextures:_,maxTextureSize:S,maxCubemapSize:g,maxAttributes:p,maxVertexUniforms:w,maxVaryings:I,maxFragmentUniforms:y,maxSamples:A,samples:E}}function jm(i){let e=this,t=null,n=0,s=!1,r=!1,a=new In,o=new Ye,l={value:null,needsUpdate:!1};this.uniform=l,this.numPlanes=0,this.numIntersection=0,this.init=function(f,u){let d=f.length!==0||u||n!==0||s;return s=u,n=f.length,d},this.beginShadows=function(){r=!0,h(null)},this.endShadows=function(){r=!1},this.setGlobalState=function(f,u){t=h(f,u,0)},this.setState=function(f,u,d){let _=f.clippingPlanes,S=f.clipIntersection,g=f.clipShadows,p=i.get(f);if(!s||_===null||_.length===0||r&&!g)r?h(null):c();else{let w=r?0:n,I=w*4,y=p.clippingState||null;l.value=y,y=h(_,u,I,d);for(let A=0;A!==I;++A)y[A]=t[A];p.clippingState=y,this.numIntersection=S?this.numPlanes:0,this.numPlanes+=w}};function c(){l.value!==t&&(l.value=t,l.needsUpdate=n>0),e.numPlanes=n,e.numIntersection=0}function h(f,u,d,_){let S=f!==null?f.length:0,g=null;if(S!==0){if(g=l.value,_!==!0||g===null){let p=d+S*4,w=u.matrixWorldInverse;o.getNormalMatrix(w),(g===null||g.length<p)&&(g=new Float32Array(p));for(let I=0,y=d;I!==S;++I,y+=4)a.copy(f[I]).applyMatrix4(w,o),a.normal.toArray(g,y),g[y+3]=a.constant}l.value=g,l.needsUpdate=!0}return e.numPlanes=S,e.numIntersection=0,g}}var Ns=4,Jm=6,Km=20,Qm=256,Gr=new vi,uh=new qe,Sc=null,Tc=0,Ec=0,wc=!1,eg=new B,Wi=new B,Us=class{constructor(e){this._renderer=e,this._pingPongRenderTarget=null,this._lodMax=0,this._cubeSize=0,this._sizeLods=[],this._lodMeshes=[],this._backgroundBox=null,this._cubemapMaterial=null,this._equirectMaterial=null,this._blurMaterial=null,this._ggxMaterial=null}fromScene(e,t=0,n=.1,s=100,r={}){let{size:a=256,position:o=eg}=r;Sc=this._renderer.getRenderTarget(),Tc=this._renderer.getActiveCubeFace(),Ec=this._renderer.getActiveMipmapLevel(),wc=this._renderer.xr.enabled,this._renderer.xr.enabled=!1,this._setSize(a);let l=this._allocateTargets();return l.depthBuffer=!0,this._sceneToCubeUV(e,n,s,l,o),t>0&&this._blur(l,0,0,t),this._applyPMREM(l),this._cleanup(l),l}fromEquirectangular(e,t=null){return this._fromTexture(e,t)}fromCubemap(e,t=null){return this._fromTexture(e,t)}compileCubemapShader(){this._cubemapMaterial===null&&(this._cubemapMaterial=fh(),this._compileMaterial(this._cubemapMaterial))}compileEquirectangularShader(){this._equirectMaterial===null&&(this._equirectMaterial=dh(),this._compileMaterial(this._equirectMaterial))}dispose(){this._dispose(),this._cubemapMaterial!==null&&this._cubemapMaterial.dispose(),this._equirectMaterial!==null&&this._equirectMaterial.dispose(),this._backgroundBox!==null&&(this._backgroundBox.geometry.dispose(),this._backgroundBox.material.dispose())}_setSize(e){this._lodMax=Math.floor(Math.log2(e)),this._cubeSize=Math.pow(2,this._lodMax)}_dispose(){this._blurMaterial!==null&&this._blurMaterial.dispose(),this._ggxMaterial!==null&&this._ggxMaterial.dispose(),this._pingPongRenderTarget!==null&&this._pingPongRenderTarget.dispose();for(let e=0;e<this._lodMeshes.length;e++)this._lodMeshes[e].geometry.dispose()}_cleanup(e){this._renderer.setRenderTarget(Sc,Tc,Ec),this._renderer.xr.enabled=wc,e.scissorTest=!1,Ls(e,0,0,e.width,e.height)}_fromTexture(e,t){e.mapping===bi||e.mapping===Hi?this._setSize(e.image.length===0?16:e.image[0].width||e.image[0].image.width):this._setSize(e.image.width/4),Sc=this._renderer.getRenderTarget(),Tc=this._renderer.getActiveCubeFace(),Ec=this._renderer.getActiveMipmapLevel(),wc=this._renderer.xr.enabled,this._renderer.xr.enabled=!1;let n=t||this._allocateTargets();return this._textureToCubeUV(e,n),this._applyPMREM(n),this._cleanup(n),n}_allocateTargets(){let e=3*Math.max(this._cubeSize,112),t=4*this._cubeSize,n={magFilter:Yt,minFilter:Yt,generateMipmaps:!1,type:jt,format:Tn,colorSpace:tr,depthBuffer:!1},s=hh(e,t,n);if(this._pingPongRenderTarget===null||this._pingPongRenderTarget.width!==e||this._pingPongRenderTarget.height!==t){this._pingPongRenderTarget!==null&&this._dispose(),this._pingPongRenderTarget=hh(e,t,n);let{_lodMax:r}=this;({lodMeshes:this._lodMeshes,sizeLods:this._sizeLods}=tg(r)),this._blurMaterial=ig(r,e,t),this._ggxMaterial=ng(r,e,t)}return s}_compileMaterial(e){let t=new mt(new St,e);this._renderer.compile(t,Gr)}_sceneToCubeUV(e,t,n,s,r){let l=new qt(90,1,t,n),c=[1,-1,1,1,1,1],h=[1,1,1,-1,-1,-1],f=this._renderer,u=f.autoClear,d=f.toneMapping;f.getClearColor(uh),f.toneMapping=Dn,f.autoClear=!1,f.state.buffers.depth.getReversed()&&(f.setRenderTarget(s),f.clearDepth(),f.setRenderTarget(null)),this._backgroundBox===null&&(this._backgroundBox=new mt(new Nn,new sn({name:"PMREM.Background",side:Zt,depthWrite:!1,depthTest:!1})));let S=this._backgroundBox,g=S.material,p=!1,w=e.background;w?w.isColor&&(g.color.copy(w),e.background=null,p=!0):(g.color.copy(uh),p=!0);for(let I=0;I<6;I++){let y=I%3;y===0?(l.up.set(0,c[I],0),l.position.set(r.x,r.y,r.z),l.lookAt(r.x+h[I],r.y,r.z)):y===1?(l.up.set(0,0,c[I]),l.position.set(r.x,r.y,r.z),l.lookAt(r.x,r.y+h[I],r.z)):(l.up.set(0,c[I],0),l.position.set(r.x,r.y,r.z),l.lookAt(r.x,r.y,r.z+h[I]));let A=this._cubeSize;Ls(s,y*A,I>2?A:0,A,A),f.setRenderTarget(s),p&&f.render(S,l),f.render(e,l)}f.toneMapping=d,f.autoClear=u,e.background=w}_textureToCubeUV(e,t){let n=this._renderer,s=e.mapping===bi||e.mapping===Hi;s?(this._cubemapMaterial===null&&(this._cubemapMaterial=fh()),this._cubemapMaterial.uniforms.flipEnvMap.value=e.isRenderTargetTexture===!1?-1:1):this._equirectMaterial===null&&(this._equirectMaterial=dh());let r=s?this._cubemapMaterial:this._equirectMaterial,a=this._lodMeshes[0];a.material=r;let o=r.uniforms;o.envMap.value=e;let l=this._cubeSize;Ls(t,0,0,3*l,2*l),n.setRenderTarget(t),n.render(a,Gr)}_applyPMREM(e){let t=this._renderer,n=t.autoClear;t.autoClear=!1;let s=this._lodMeshes.length;for(let r=1;r<s;r++)this._applyGGXFilter(e,r-1,r);t.autoClear=n}_applyGGXFilter(e,t,n){let s=this._renderer,r=this._pingPongRenderTarget,a=this._ggxMaterial,o=this._lodMeshes[n];o.material=a;let l=a.uniforms,c=n/(this._lodMeshes.length-1),h=t/(this._lodMeshes.length-1),f=Math.sqrt(c*c-h*h),u=c*1.25,d=f*u,{_lodMax:_}=this,S=this._sizeLods[n],g=3*S*(n>_-Ns?n-_+Ns:0),p=4*(this._cubeSize-S);l.envMap.value=e.texture,l.roughness.value=d,l.mipInt.value=_-t,Ls(r,g,p,3*S,2*S),s.setRenderTarget(r),s.render(o,Gr),l.envMap.value=r.texture,l.roughness.value=0,l.mipInt.value=_-n,Ls(e,g,p,3*S,2*S),s.setRenderTarget(e),s.render(o,Gr)}_blur(e,t,n,s){let r=this._pingPongRenderTarget,a=Math.min(s,Math.PI)/Math.SQRT2;this._blurPass(e,r,t,n,a),this._blurPass(r,e,n,n,a)}_blurPass(e,t,n,s,r){let a=this._renderer,o=this._blurMaterial,l=this._lodMeshes[s];l.material=o;let c=o.uniforms;c.envMap.value=e.texture,c.sigma.value=r,c.mipInt.value=this._lodMax-n;let h=this._sizeLods[s],f=3*h*(s>this._lodMax-Ns?s-this._lodMax+Ns:0),u=4*(this._cubeSize-h);Ls(t,f,u,3*h,2*h),a.setRenderTarget(t),a.render(l,Gr)}};function tg(i){let e=[],t=[],n=i,s=i-Ns+1+Jm;for(let r=0;r<s;r++){let a=Math.pow(2,n);e.push(a);let o=1/(a-2),l=-o,c=1+o,h=[l,l,c,l,c,c,l,l,c,c,l,c],f=6,u=6,d=3,_=new Float32Array(d*u*f),S=new Float32Array(d*u*f);for(let p=0;p<f;p++){let w=p%3*2/3-1,I=p>2?0:-1,y=[w,I,0,w+2/3,I,0,w+2/3,I+1,0,w,I,0,w+2/3,I+1,0,w,I+1,0];_.set(y,d*u*p);for(let A=0;A<u;A++){let E=h[A*2]*2-1,D=h[A*2+1]*2-1;p===0?Wi.set(1,D,E):p===1?Wi.set(-E,1,-D):p===2?Wi.set(-E,D,1):p===3?Wi.set(-1,D,-E):p===4?Wi.set(-E,-1,D):Wi.set(E,D,-1),Wi.toArray(S,(p*u+A)*d)}}let g=new St;g.setAttribute("position",new Xt(_,d)),g.setAttribute("outputDirection",new Xt(S,d)),t.push(new mt(g,null)),n>Ns&&n--}return{lodMeshes:t,sizeLods:e}}function hh(i,e,t){let n=new Ft(i,e,t);return n.texture.mapping=Dr,n.texture.name="PMREM.cubeUv",n.scissorTest=!0,n}function Ls(i,e,t,n,s){i.viewport.set(e,t,n,s),i.scissor.set(e,t,n,s)}function ng(i,e,t){return new Nt({name:"PMREMGGXConvolution",defines:{GGX_SAMPLES:Qm,CUBEUV_TEXEL_WIDTH:1/e,CUBEUV_TEXEL_HEIGHT:1/t,CUBEUV_MAX_MIP:`${i}.0`},uniforms:{envMap:{value:null},roughness:{value:0},mipInt:{value:0}},vertexShader:al(),fragmentShader:`

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
		`,blending:Mn,depthTest:!1,depthWrite:!1})}function ig(i,e,t){return new Nt({name:"SphericalGaussianBlur",defines:{SAMPLES:Km,CUBEUV_TEXEL_WIDTH:1/e,CUBEUV_TEXEL_HEIGHT:1/t,CUBEUV_MAX_MIP:`${i}.0`},uniforms:{envMap:{value:null},sigma:{value:0},mipInt:{value:0}},vertexShader:al(),fragmentShader:`

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
		`,blending:Mn,depthTest:!1,depthWrite:!1})}function dh(){return new Nt({name:"EquirectangularToCubeUV",uniforms:{envMap:{value:null}},vertexShader:al(),fragmentShader:`

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
		`,blending:Mn,depthTest:!1,depthWrite:!1})}function fh(){return new Nt({name:"CubemapToCubeUV",uniforms:{envMap:{value:null},flipEnvMap:{value:-1}},vertexShader:al(),fragmentShader:`

			precision mediump float;
			precision mediump int;

			uniform float flipEnvMap;

			varying vec3 vOutputDirection;

			uniform samplerCube envMap;

			void main() {

				gl_FragColor = textureCube( envMap, vec3( flipEnvMap * vOutputDirection.x, vOutputDirection.yz ) );

			}
		`,blending:Mn,depthTest:!1,depthWrite:!1})}function al(){return`

		precision mediump float;
		precision mediump int;

		attribute vec3 outputDirection;

		varying vec3 vOutputDirection;

		void main() {

			vOutputDirection = outputDirection;
			gl_Position = vec4( position, 1.0 );

		}
	`}var sl=class extends Ft{constructor(e=1,t={}){super(e,e,t),this.isWebGLCubeRenderTarget=!0;let n={width:e,height:e,depth:1},s=[n,n,n,n,n,n];this.texture=new dr(s),this._setTextureOptions(t),this.texture.isRenderTargetTexture=!0}fromEquirectangularTexture(e,t){this.texture.type=t.type,this.texture.colorSpace=t.colorSpace,this.texture.generateMipmaps=t.generateMipmaps,this.texture.minFilter=t.minFilter,this.texture.magFilter=t.magFilter;let n={uniforms:{tEquirect:{value:null}},vertexShader:`

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
			`},s=new Nn(5,5,5),r=new Nt({name:"CubemapFromEquirect",uniforms:Gi(n.uniforms),vertexShader:n.vertexShader,fragmentShader:n.fragmentShader,side:Zt,blending:Mn});r.uniforms.tEquirect.value=t;let a=new mt(s,r),o=t.minFilter;return t.minFilter===Mi&&(t.minFilter=Yt),new co(1,10,this).update(e,a),t.minFilter=o,a.geometry.dispose(),a.material.dispose(),this}clear(e,t=!0,n=!0,s=!0){let r=e.getRenderTarget();for(let a=0;a<6;a++)e.setRenderTarget(this,a),e.clear(t,n,s);e.setRenderTarget(r)}};function sg(i){let e=new WeakMap,t=new WeakMap,n=null;function s(u,d=!1){return u==null?null:d?a(u):r(u)}function r(u){if(u&&u.isTexture){let d=u.mapping;if(d===fo||d===po)if(e.has(u)){let _=e.get(u).texture;return o(_,u.mapping)}else{let _=u.image;if(_&&_.height>0){let S=new sl(_.height);return S.fromEquirectangularTexture(i,u),e.set(u,S),u.addEventListener("dispose",c),o(S.texture,u.mapping)}else return null}}return u}function a(u){if(u&&u.isTexture){let d=u.mapping,_=d===fo||d===po,S=d===bi||d===Hi;if(_||S){let g=t.get(u),p=g!==void 0?g.texture.pmremVersion:0;if(u.isRenderTargetTexture&&u.pmremVersion!==p)return n===null&&(n=new Us(i)),g=_?n.fromEquirectangular(u,g):n.fromCubemap(u,g),g.texture.pmremVersion=u.pmremVersion,t.set(u,g),g.texture;if(g!==void 0)return g.texture;{let w=u.image;return _&&w&&w.height>0||S&&w&&l(w)?(n===null&&(n=new Us(i)),g=_?n.fromEquirectangular(u):n.fromCubemap(u),g.texture.pmremVersion=u.pmremVersion,t.set(u,g),u.addEventListener("dispose",h),g.texture):null}}}return u}function o(u,d){return d===fo?u.mapping=bi:d===po&&(u.mapping=Hi),u}function l(u){let d=0,_=6;for(let S=0;S<_;S++)u[S]!==void 0&&d++;return d===_}function c(u){let d=u.target;d.removeEventListener("dispose",c);let _=e.get(d);_!==void 0&&(e.delete(d),_.dispose())}function h(u){let d=u.target;d.removeEventListener("dispose",h);let _=t.get(d);_!==void 0&&(t.delete(d),_.dispose())}function f(){e=new WeakMap,t=new WeakMap,n!==null&&(n.dispose(),n=null)}return{get:s,dispose:f}}function rg(i){let e={};function t(n){if(e[n]!==void 0)return e[n];let s=i.getExtension(n);return e[n]=s,s}return{has:function(n){return t(n)!==null},init:function(){t("EXT_color_buffer_float"),t("WEBGL_clip_cull_distance"),t("OES_texture_float_linear"),t("EXT_color_buffer_half_float"),t("WEBGL_multisampled_render_to_texture"),t("WEBGL_render_shared_exponent")},get:function(n){let s=t(n);return s===null&&Ni("WebGLRenderer: "+n+" extension not supported."),s}}}function ag(i,e,t,n){let s={},r=new WeakMap;function a(f){let u=f.target;u.index!==null&&e.remove(u.index);for(let _ in u.attributes)e.remove(u.attributes[_]);u.removeEventListener("dispose",a),delete s[u.id];let d=r.get(u);d&&(e.remove(d),r.delete(u)),n.releaseStatesOfGeometry(u),u.isInstancedBufferGeometry===!0&&delete u._maxInstanceCount,t.memory.geometries--}function o(f,u){return s[u.id]===!0||(u.addEventListener("dispose",a),s[u.id]=!0,t.memory.geometries++),u}function l(f){let u=f.attributes;for(let d in u)e.update(u[d],i.ARRAY_BUFFER)}function c(f){let u=[],d=f.index,_=f.attributes.position,S=0;if(_===void 0)return;if(d!==null){let w=d.array;S=d.version;for(let I=0,y=w.length;I<y;I+=3){let A=w[I+0],E=w[I+1],D=w[I+2];u.push(A,E,E,D,D,A)}}else{let w=_.array;S=_.version;for(let I=0,y=w.length/3-1;I<y;I+=3){let A=I+0,E=I+1,D=I+2;u.push(A,E,E,D,D,A)}}let g=new(_.count>=65535?or:ar)(u,1);g.version=S;let p=r.get(f);p&&e.remove(p),r.set(f,g)}function h(f){let u=r.get(f);if(u){let d=f.index;d!==null&&u.version<d.version&&c(f)}else c(f);return r.get(f)}return{get:o,update:l,getWireframeAttribute:h}}function og(i,e,t){let n;function s(f){n=f}let r,a;function o(f){r=f.type,a=f.bytesPerElement}function l(f,u){i.drawElements(n,u,r,f*a),t.update(u,n,1)}function c(f,u,d){d!==0&&(i.drawElementsInstanced(n,u,r,f*a,d),t.update(u,n,d))}function h(f,u,d){if(d===0)return;e.get("WEBGL_multi_draw").multiDrawElementsWEBGL(n,u,0,r,f,0,d);let S=0;for(let g=0;g<d;g++)S+=u[g];t.update(S,n,1)}this.setMode=s,this.setIndex=o,this.render=l,this.renderInstances=c,this.renderMultiDraw=h}function lg(i){let e={geometries:0,textures:0},t={frame:0,calls:0,triangles:0,points:0,lines:0};function n(r,a,o){switch(t.calls++,a){case i.TRIANGLES:t.triangles+=o*(r/3);break;case i.LINES:t.lines+=o*(r/2);break;case i.LINE_STRIP:t.lines+=o*(r-1);break;case i.LINE_LOOP:t.lines+=o*r;break;case i.POINTS:t.points+=o*r;break;default:Xe("WebGLInfo: Unknown draw mode:",a);break}}function s(){t.calls=0,t.triangles=0,t.points=0,t.lines=0}return{memory:e,render:t,programs:null,autoReset:!0,reset:s,update:n}}function cg(i,e,t){let n=new WeakMap,s=new It;function r(a,o,l){let c=a.morphTargetInfluences,h=o.morphAttributes.position||o.morphAttributes.normal||o.morphAttributes.color,f=h!==void 0?h.length:0,u=n.get(o);if(u===void 0||u.count!==f){let C=function(){D.dispose(),n.delete(o),o.removeEventListener("dispose",C)};u!==void 0&&u.texture.dispose();let d=o.morphAttributes.position!==void 0,_=o.morphAttributes.normal!==void 0,S=o.morphAttributes.color!==void 0,g=o.morphAttributes.position||[],p=o.morphAttributes.normal||[],w=o.morphAttributes.color||[],I=0;d===!0&&(I=1),_===!0&&(I=2),S===!0&&(I=3);let y=o.attributes.position.count*I,A=1;y>e.maxTextureSize&&(A=Math.ceil(y/e.maxTextureSize),y=e.maxTextureSize);let E=new Float32Array(y*A*4*f),D=new sr(E,y,A,f);D.type=Sn,D.needsUpdate=!0;let v=I*4;for(let O=0;O<f;O++){let V=g[O],q=p[O],j=w[O],z=y*A*4*O;for(let Y=0;Y<V.count;Y++){let te=Y*v;d===!0&&(s.fromBufferAttribute(V,Y),E[z+te+0]=s.x,E[z+te+1]=s.y,E[z+te+2]=s.z,E[z+te+3]=0),_===!0&&(s.fromBufferAttribute(q,Y),E[z+te+4]=s.x,E[z+te+5]=s.y,E[z+te+6]=s.z,E[z+te+7]=0),S===!0&&(s.fromBufferAttribute(j,Y),E[z+te+8]=s.x,E[z+te+9]=s.y,E[z+te+10]=s.z,E[z+te+11]=j.itemSize===4?s.w:1)}}u={count:f,texture:D,size:new De(y,A)},n.set(o,u),o.addEventListener("dispose",C)}if(a.isInstancedMesh===!0&&a.morphTexture!==null)l.getUniforms().setValue(i,"morphTexture",a.morphTexture,t);else{let d=0;for(let S=0;S<c.length;S++)d+=c[S];let _=o.morphTargetsRelative?1:1-d;l.getUniforms().setValue(i,"morphTargetBaseInfluence",_),l.getUniforms().setValue(i,"morphTargetInfluences",c)}l.getUniforms().setValue(i,"morphTargetsTexture",u.texture,t),l.getUniforms().setValue(i,"morphTargetsTextureSize",u.size)}return{update:r}}function ug(i,e,t,n,s){let r=new WeakMap;function a(c){let h=s.render.frame,f=c.geometry,u=e.get(c,f);if(r.get(u)!==h&&(e.update(u),r.set(u,h)),c.isInstancedMesh&&(c.hasEventListener("dispose",l)===!1&&c.addEventListener("dispose",l),r.get(c)!==h&&(t.update(c.instanceMatrix,i.ARRAY_BUFFER),c.instanceColor!==null&&t.update(c.instanceColor,i.ARRAY_BUFFER),r.set(c,h))),c.isSkinnedMesh){let d=c.skeleton;r.get(d)!==h&&(d.update(),r.set(d,h))}return u}function o(){r=new WeakMap}function l(c){let h=c.target;h.removeEventListener("dispose",l),n.releaseStatesOfObject(h),t.remove(h.instanceMatrix),h.instanceColor!==null&&t.remove(h.instanceColor)}return{update:a,dispose:o}}var hg={[Cr]:"LINEAR_TONE_MAPPING",[Rr]:"REINHARD_TONE_MAPPING",[Ir]:"CINEON_TONE_MAPPING",[Vi]:"ACES_FILMIC_TONE_MAPPING",[Lr]:"AGX_TONE_MAPPING",[Nr]:"NEUTRAL_TONE_MAPPING",[Pr]:"CUSTOM_TONE_MAPPING"};function dg(i,e,t,n,s,r){let a=new Ft(e,t,{type:i,depthBuffer:s,stencilBuffer:r,samples:n?4:0,storeMultisampledDepthBuffer:!1,storeMultisampledStencilBuffer:!1,resolveDepthBuffer:!1,resolveStencilBuffer:!1}),o=null,l=null,c=new St;c.setAttribute("position",new pt([-1,3,0,-1,-1,0,3,-1,0],3)),c.setAttribute("uv",new pt([0,2,0,0,2,0],2));let h=new Es({uniforms:{tDiffuse:{value:null}},vertexShader:`
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
			}`,depthTest:!1,depthWrite:!1}),f=new mt(c,h),u=new vi(-1,1,1,-1,0,1),d=null,_=null,S=!1,g,p=null,w=[],I=!1;this.setSize=function(y,A){a.setSize(y,A),o!==null&&o.setSize(y,A),l!==null&&l.setSize(y,A);for(let E=0;E<w.length;E++){let D=w[E];D.setSize&&D.setSize(y,A)}},this.setEffects=function(y){w=y,I=w.length>0&&w[0].isRenderPass===!0;let A=a.width,E=a.height;w.length>0&&o===null&&(o=new Ft(A,E,{type:jt,depthBuffer:!1,stencilBuffer:!1}),l=new Ft(A,E,{type:jt,depthBuffer:!1,stencilBuffer:!1}));for(let D=0;D<w.length;D++){let v=w[D];v.setSize&&v.setSize(A,E)}},this.begin=function(y,A){if(S||y.toneMapping===Dn&&w.length===0)return!1;if(p=A,A!==null){let E=A.width,D=A.height;(a.width!==E||a.height!==D)&&this.setSize(E,D)}return I===!1&&y.setRenderTarget(a),g=y.toneMapping,y.toneMapping=Dn,!0},this.hasRenderPass=function(){return I},this.end=function(y,A){y.toneMapping=g,S=!0;let E=a,D=o;for(let v=0;v<w.length;v++){let C=w[v];C.enabled!==!1&&(C.render(y,D,E,A),C.needsSwap!==!1&&(E=D,D=D===o?l:o))}if(d!==y.outputColorSpace||_!==y.toneMapping){d=y.outputColorSpace,_=y.toneMapping,h.defines={},at.getTransfer(d)===yt&&(h.defines.SRGB_TRANSFER="");let v=hg[_];v&&(h.defines[v]=""),h.needsUpdate=!0}h.uniforms.tDiffuse.value=E.texture,y.setRenderTarget(p),y.render(f,u),p=null,S=!1},this.isCompositing=function(){return S},this.dispose=function(){a.dispose(),o!==null&&o.dispose(),l!==null&&l.dispose(),c.dispose(),h.dispose()}}var Nh=new on,Rc=new mi(1,1),Dh=new sr,Uh=new za,Fh=new dr,ph=[],mh=[],gh=new Float32Array(16),_h=new Float32Array(9),xh=new Float32Array(4);function Fs(i,e,t){let n=i[0];if(n<=0||n>0)return i;let s=e*t,r=ph[s];if(r===void 0&&(r=new Float32Array(s),ph[s]=r),e!==0){n.toArray(r,0);for(let a=1,o=0;a!==e;++a)o+=t,i[a].toArray(r,o)}return r}function Bt(i,e){if(i.length!==e.length)return!1;for(let t=0,n=i.length;t<n;t++)if(i[t]!==e[t])return!1;return!0}function zt(i,e){for(let t=0,n=e.length;t<n;t++)i[t]=e[t]}function ol(i,e){let t=mh[e];t===void 0&&(t=new Int32Array(e),mh[e]=t);for(let n=0;n!==e;++n)t[n]=i.allocateTextureUnit();return t}function fg(i,e){let t=this.cache;t[0]!==e&&(i.uniform1f(this.addr,e),t[0]=e)}function pg(i,e){let t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y)&&(i.uniform2f(this.addr,e.x,e.y),t[0]=e.x,t[1]=e.y);else{if(Bt(t,e))return;i.uniform2fv(this.addr,e),zt(t,e)}}function mg(i,e){let t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z)&&(i.uniform3f(this.addr,e.x,e.y,e.z),t[0]=e.x,t[1]=e.y,t[2]=e.z);else if(e.r!==void 0)(t[0]!==e.r||t[1]!==e.g||t[2]!==e.b)&&(i.uniform3f(this.addr,e.r,e.g,e.b),t[0]=e.r,t[1]=e.g,t[2]=e.b);else{if(Bt(t,e))return;i.uniform3fv(this.addr,e),zt(t,e)}}function gg(i,e){let t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z||t[3]!==e.w)&&(i.uniform4f(this.addr,e.x,e.y,e.z,e.w),t[0]=e.x,t[1]=e.y,t[2]=e.z,t[3]=e.w);else{if(Bt(t,e))return;i.uniform4fv(this.addr,e),zt(t,e)}}function _g(i,e){let t=this.cache,n=e.elements;if(n===void 0){if(Bt(t,e))return;i.uniformMatrix2fv(this.addr,!1,e),zt(t,e)}else{if(Bt(t,n))return;xh.set(n),i.uniformMatrix2fv(this.addr,!1,xh),zt(t,n)}}function xg(i,e){let t=this.cache,n=e.elements;if(n===void 0){if(Bt(t,e))return;i.uniformMatrix3fv(this.addr,!1,e),zt(t,e)}else{if(Bt(t,n))return;_h.set(n),i.uniformMatrix3fv(this.addr,!1,_h),zt(t,n)}}function vg(i,e){let t=this.cache,n=e.elements;if(n===void 0){if(Bt(t,e))return;i.uniformMatrix4fv(this.addr,!1,e),zt(t,e)}else{if(Bt(t,n))return;gh.set(n),i.uniformMatrix4fv(this.addr,!1,gh),zt(t,n)}}function yg(i,e){let t=this.cache;t[0]!==e&&(i.uniform1i(this.addr,e),t[0]=e)}function bg(i,e){let t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y)&&(i.uniform2i(this.addr,e.x,e.y),t[0]=e.x,t[1]=e.y);else{if(Bt(t,e))return;i.uniform2iv(this.addr,e),zt(t,e)}}function Mg(i,e){let t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z)&&(i.uniform3i(this.addr,e.x,e.y,e.z),t[0]=e.x,t[1]=e.y,t[2]=e.z);else{if(Bt(t,e))return;i.uniform3iv(this.addr,e),zt(t,e)}}function Sg(i,e){let t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z||t[3]!==e.w)&&(i.uniform4i(this.addr,e.x,e.y,e.z,e.w),t[0]=e.x,t[1]=e.y,t[2]=e.z,t[3]=e.w);else{if(Bt(t,e))return;i.uniform4iv(this.addr,e),zt(t,e)}}function Tg(i,e){let t=this.cache;t[0]!==e&&(i.uniform1ui(this.addr,e),t[0]=e)}function Eg(i,e){let t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y)&&(i.uniform2ui(this.addr,e.x,e.y),t[0]=e.x,t[1]=e.y);else{if(Bt(t,e))return;i.uniform2uiv(this.addr,e),zt(t,e)}}function wg(i,e){let t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z)&&(i.uniform3ui(this.addr,e.x,e.y,e.z),t[0]=e.x,t[1]=e.y,t[2]=e.z);else{if(Bt(t,e))return;i.uniform3uiv(this.addr,e),zt(t,e)}}function Ag(i,e){let t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z||t[3]!==e.w)&&(i.uniform4ui(this.addr,e.x,e.y,e.z,e.w),t[0]=e.x,t[1]=e.y,t[2]=e.z,t[3]=e.w);else{if(Bt(t,e))return;i.uniform4uiv(this.addr,e),zt(t,e)}}function Cg(i,e,t){let n=this.cache,s=t.allocateTextureUnit();n[0]!==s&&(i.uniform1i(this.addr,s),n[0]=s);let r;this.type===i.SAMPLER_2D_SHADOW?(Rc.compareFunction=t.isReversedDepthBuffer()?el:Qo,r=Rc):r=Nh,t.setTexture2D(e||r,s)}function Rg(i,e,t){let n=this.cache,s=t.allocateTextureUnit();n[0]!==s&&(i.uniform1i(this.addr,s),n[0]=s),t.setTexture3D(e||Uh,s)}function Ig(i,e,t){let n=this.cache,s=t.allocateTextureUnit();n[0]!==s&&(i.uniform1i(this.addr,s),n[0]=s),t.setTextureCube(e||Fh,s)}function Pg(i,e,t){let n=this.cache,s=t.allocateTextureUnit();n[0]!==s&&(i.uniform1i(this.addr,s),n[0]=s),t.setTexture2DArray(e||Dh,s)}function Lg(i){switch(i){case 5126:return fg;case 35664:return pg;case 35665:return mg;case 35666:return gg;case 35674:return _g;case 35675:return xg;case 35676:return vg;case 5124:case 35670:return yg;case 35667:case 35671:return bg;case 35668:case 35672:return Mg;case 35669:case 35673:return Sg;case 5125:return Tg;case 36294:return Eg;case 36295:return wg;case 36296:return Ag;case 35678:case 36198:case 36298:case 36306:case 35682:return Cg;case 35679:case 36299:case 36307:return Rg;case 35680:case 36300:case 36308:case 36293:return Ig;case 36289:case 36303:case 36311:case 36292:return Pg}}function Ng(i,e){i.uniform1fv(this.addr,e)}function Dg(i,e){let t=Fs(e,this.size,2);i.uniform2fv(this.addr,t)}function Ug(i,e){let t=Fs(e,this.size,3);i.uniform3fv(this.addr,t)}function Fg(i,e){let t=Fs(e,this.size,4);i.uniform4fv(this.addr,t)}function kg(i,e){let t=Fs(e,this.size,4);i.uniformMatrix2fv(this.addr,!1,t)}function Og(i,e){let t=Fs(e,this.size,9);i.uniformMatrix3fv(this.addr,!1,t)}function Bg(i,e){let t=Fs(e,this.size,16);i.uniformMatrix4fv(this.addr,!1,t)}function zg(i,e){i.uniform1iv(this.addr,e)}function Vg(i,e){i.uniform2iv(this.addr,e)}function Hg(i,e){i.uniform3iv(this.addr,e)}function Gg(i,e){i.uniform4iv(this.addr,e)}function Wg(i,e){i.uniform1uiv(this.addr,e)}function $g(i,e){i.uniform2uiv(this.addr,e)}function qg(i,e){i.uniform3uiv(this.addr,e)}function Xg(i,e){i.uniform4uiv(this.addr,e)}function Yg(i,e,t){let n=this.cache,s=e.length,r=ol(t,s);Bt(n,r)||(i.uniform1iv(this.addr,r),zt(n,r));let a;this.type===i.SAMPLER_2D_SHADOW?a=Rc:a=Nh;for(let o=0;o!==s;++o)t.setTexture2D(e[o]||a,r[o])}function Zg(i,e,t){let n=this.cache,s=e.length,r=ol(t,s);Bt(n,r)||(i.uniform1iv(this.addr,r),zt(n,r));for(let a=0;a!==s;++a)t.setTexture3D(e[a]||Uh,r[a])}function jg(i,e,t){let n=this.cache,s=e.length,r=ol(t,s);Bt(n,r)||(i.uniform1iv(this.addr,r),zt(n,r));for(let a=0;a!==s;++a)t.setTextureCube(e[a]||Fh,r[a])}function Jg(i,e,t){let n=this.cache,s=e.length,r=ol(t,s);Bt(n,r)||(i.uniform1iv(this.addr,r),zt(n,r));for(let a=0;a!==s;++a)t.setTexture2DArray(e[a]||Dh,r[a])}function Kg(i){switch(i){case 5126:return Ng;case 35664:return Dg;case 35665:return Ug;case 35666:return Fg;case 35674:return kg;case 35675:return Og;case 35676:return Bg;case 5124:case 35670:return zg;case 35667:case 35671:return Vg;case 35668:case 35672:return Hg;case 35669:case 35673:return Gg;case 5125:return Wg;case 36294:return $g;case 36295:return qg;case 36296:return Xg;case 35678:case 36198:case 36298:case 36306:case 35682:return Yg;case 35679:case 36299:case 36307:return Zg;case 35680:case 36300:case 36308:case 36293:return jg;case 36289:case 36303:case 36311:case 36292:return Jg}}var Ic=class{constructor(e,t,n){this.id=e,this.addr=n,this.cache=[],this.type=t.type,this.setValue=Lg(t.type)}},Pc=class{constructor(e,t,n){this.id=e,this.addr=n,this.cache=[],this.type=t.type,this.size=t.size,this.setValue=Kg(t.type)}},Lc=class{constructor(e){this.id=e,this.seq=[],this.map={}}setValue(e,t,n){let s=this.seq;for(let r=0,a=s.length;r!==a;++r){let o=s[r];o.setValue(e,t[o.id],n)}}},Ac=/(\w+)(\])?(\[|\.)?/g;function vh(i,e){i.seq.push(e),i.map[e.id]=e}function Qg(i,e,t){let n=i.name,s=n.length;for(Ac.lastIndex=0;;){let r=Ac.exec(n),a=Ac.lastIndex,o=r[1],l=r[2]==="]",c=r[3];if(l&&(o=o|0),c===void 0||c==="["&&a+2===s){vh(t,c===void 0?new Ic(o,i,e):new Pc(o,i,e));break}else{let f=t.map[o];f===void 0&&(f=new Lc(o),vh(t,f)),t=f}}}var Ds=class{constructor(e,t){this.seq=[],this.map={};let n=e.getProgramParameter(t,e.ACTIVE_UNIFORMS);for(let a=0;a<n;++a){let o=e.getActiveUniform(t,a),l=e.getUniformLocation(t,o.name);Qg(o,l,this)}let s=[],r=[];for(let a of this.seq)a.type===e.SAMPLER_2D_SHADOW||a.type===e.SAMPLER_CUBE_SHADOW||a.type===e.SAMPLER_2D_ARRAY_SHADOW?s.push(a):r.push(a);s.length>0&&(this.seq=s.concat(r))}setValue(e,t,n,s){let r=this.map[t];r!==void 0&&r.setValue(e,n,s)}setOptional(e,t,n){let s=t[n];s!==void 0&&this.setValue(e,n,s)}static upload(e,t,n,s){for(let r=0,a=t.length;r!==a;++r){let o=t[r],l=n[o.id];l.needsUpdate!==!1&&o.setValue(e,l.value,s)}}static seqWithValue(e,t){let n=[];for(let s=0,r=e.length;s!==r;++s){let a=e[s];a.id in t&&n.push(a)}return n}};function yh(i,e,t){let n=i.createShader(e);return i.shaderSource(n,t),i.compileShader(n),n}var e0=37297,t0=0;function n0(i,e){let t=i.split(`
`),n=[],s=Math.max(e-6,0),r=Math.min(e+6,t.length);for(let a=s;a<r;a++){let o=a+1;n.push(`${o===e?">":" "} ${o}: ${t[a]}`)}return n.join(`
`)}var bh=new Ye;function i0(i){at._getMatrix(bh,at.workingColorSpace,i);let e=`mat3( ${bh.elements.map(t=>t.toFixed(4))} )`;switch(at.getTransfer(i)){case nr:return[e,"LinearTransferOETF"];case yt:return[e,"sRGBTransferOETF"];default:return $e("WebGLProgram: Unsupported color space: ",i),[e,"LinearTransferOETF"]}}function Mh(i,e,t){let n=i.getShaderParameter(e,i.COMPILE_STATUS),r=(i.getShaderInfoLog(e)||"").trim();if(n&&r==="")return"";let a=/ERROR: 0:(\d+)/.exec(r);if(a){let o=parseInt(a[1]);return t.toUpperCase()+`

`+r+`

`+n0(i.getShaderSource(e),o)}else return r}function s0(i,e){let t=i0(e);return[`vec4 ${i}( vec4 value ) {`,`	return ${t[1]}( vec4( value.rgb * ${t[0]}, value.a ) );`,"}"].join(`
`)}var r0={[Cr]:"Linear",[Rr]:"Reinhard",[Ir]:"Cineon",[Vi]:"ACESFilmic",[Lr]:"AgX",[Nr]:"Neutral",[Pr]:"Custom"};function a0(i,e){let t=r0[e];return t===void 0?($e("WebGLProgram: Unsupported toneMapping:",e),"vec3 "+i+"( vec3 color ) { return LinearToneMapping( color ); }"):"vec3 "+i+"( vec3 color ) { return "+t+"ToneMapping( color ); }"}var il=new B;function o0(){at.getLuminanceCoefficients(il);let i=il.x.toFixed(4),e=il.y.toFixed(4),t=il.z.toFixed(4);return["float luminance( const in vec3 rgb ) {",`	const vec3 weights = vec3( ${i}, ${e}, ${t} );`,"	return dot( weights, rgb );","}"].join(`
`)}function l0(i){return[i.extensionClipCullDistance?"#extension GL_ANGLE_clip_cull_distance : require":"",i.extensionMultiDraw?"#extension GL_ANGLE_multi_draw : require":""].filter($r).join(`
`)}function c0(i){let e=[];for(let t in i){let n=i[t];n!==!1&&e.push("#define "+t+" "+n)}return e.join(`
`)}function u0(i,e){let t={},n=i.getProgramParameter(e,i.ACTIVE_ATTRIBUTES);for(let s=0;s<n;s++){let r=i.getActiveAttrib(e,s),a=r.name,o=1;r.type===i.FLOAT_MAT2&&(o=2),r.type===i.FLOAT_MAT3&&(o=3),r.type===i.FLOAT_MAT4&&(o=4),t[a]={type:r.type,location:i.getAttribLocation(e,a),locationSize:o}}return t}function $r(i){return i!==""}function Sh(i,e){let t=e.numSpotLightShadows+e.numSpotLightMaps-e.numSpotLightShadowsWithMaps;return i.replace(/NUM_SUN_LIGHTS/g,e.numSunLights).replace(/NUM_DIR_LIGHTS/g,e.numDirLights).replace(/NUM_SPOT_LIGHTS/g,e.numSpotLights).replace(/NUM_SPOT_LIGHT_MAPS/g,e.numSpotLightMaps).replace(/NUM_SPOT_LIGHT_COORDS/g,t).replace(/NUM_RECT_AREA_LIGHTS/g,e.numRectAreaLights).replace(/NUM_POINT_LIGHTS/g,e.numPointLights).replace(/NUM_HEMI_LIGHTS/g,e.numHemiLights).replace(/NUM_SUN_LIGHT_SHADOWS/g,e.numSunLightShadows).replace(/NUM_DIR_LIGHT_SHADOWS/g,e.numDirLightShadows).replace(/NUM_SPOT_LIGHT_SHADOWS_WITH_MAPS/g,e.numSpotLightShadowsWithMaps).replace(/NUM_SPOT_LIGHT_SHADOWS/g,e.numSpotLightShadows).replace(/NUM_POINT_LIGHT_SHADOWS/g,e.numPointLightShadows)}function Th(i,e){return i.replace(/NUM_CLIPPING_PLANES/g,e.numClippingPlanes).replace(/UNION_CLIPPING_PLANES/g,e.numClippingPlanes-e.numClipIntersection)}var h0=/^[ \t]*#include +<([\w\d./]+)>/gm;function Nc(i){return i.replace(h0,f0)}var d0=new Map;function f0(i,e){let t=nt[e];if(t===void 0){let n=d0.get(e);if(n!==void 0)t=nt[n],$e('WebGLRenderer: Shader chunk "%s" has been deprecated. Use "%s" instead.',e,n);else throw new Error("THREE.WebGLProgram: Can not resolve #include <"+e+">")}return Nc(t)}var p0=/#pragma unroll_loop_start\s+for\s*\(\s*int\s+i\s*=\s*(\d+)\s*;\s*i\s*<\s*(\d+)\s*;\s*i\s*\+\+\s*\)\s*{([\s\S]+?)}\s+#pragma unroll_loop_end/g;function Eh(i){return i.replace(p0,m0)}function m0(i,e,t,n){let s="";for(let r=parseInt(e);r<parseInt(t);r++)s+=n.replace(/\[\s*i\s*\]/g,"[ "+r+" ]").replace(/UNROLLED_LOOP_INDEX/g,r);return s}function wh(i){let e=`precision ${i.precision} float;
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
#define LOW_PRECISION`),e}var g0={[Ar]:"SHADOWMAP_TYPE_PCF",[As]:"SHADOWMAP_TYPE_VSM"};function _0(i){return g0[i.shadowMapType]||"SHADOWMAP_TYPE_BASIC"}var x0={[bi]:"ENVMAP_TYPE_CUBE",[Hi]:"ENVMAP_TYPE_CUBE",[Dr]:"ENVMAP_TYPE_CUBE_UV"};function v0(i){return i.envMap===!1?"ENVMAP_TYPE_CUBE":x0[i.envMapMode]||"ENVMAP_TYPE_CUBE"}var y0={[Hi]:"ENVMAP_MODE_REFRACTION"};function b0(i){return i.envMap===!1?"ENVMAP_MODE_REFLECTION":y0[i.envMapMode]||"ENVMAP_MODE_REFLECTION"}var M0={[ho]:"ENVMAP_BLENDING_MULTIPLY",[Wu]:"ENVMAP_BLENDING_MIX",[$u]:"ENVMAP_BLENDING_ADD"};function S0(i){return i.envMap===!1?"ENVMAP_BLENDING_NONE":M0[i.combine]||"ENVMAP_BLENDING_NONE"}function T0(i){let e=i.envMapCubeUVHeight;if(e===null)return null;let t=Math.log2(e)-2,n=1/e;return{texelWidth:1/(3*Math.max(Math.pow(2,t),112)),texelHeight:n,maxMip:t}}function E0(i,e,t,n){let s=i.getContext(),r=t.defines,a=t.vertexShader,o=t.fragmentShader,l=_0(t),c=v0(t),h=b0(t),f=S0(t),u=T0(t),d=l0(t),_=c0(r),S=s.createProgram(),g,p,w=t.glslVersion?"#version "+t.glslVersion+`
`:"";t.isRawShaderMaterial?(g=["#define SHADER_TYPE "+t.shaderType,"#define SHADER_NAME "+t.shaderName,_].filter($r).join(`
`),g.length>0&&(g+=`
`),p=["#define SHADER_TYPE "+t.shaderType,"#define SHADER_NAME "+t.shaderName,_].filter($r).join(`
`),p.length>0&&(p+=`
`)):(g=[wh(t),"#define SHADER_TYPE "+t.shaderType,"#define SHADER_NAME "+t.shaderName,_,t.extensionClipCullDistance?"#define USE_CLIP_DISTANCE":"",t.batching?"#define USE_BATCHING":"",t.batchingColor?"#define USE_BATCHING_COLOR":"",t.instancing?"#define USE_INSTANCING":"",t.instancingColor?"#define USE_INSTANCING_COLOR":"",t.instancingMorph?"#define USE_INSTANCING_MORPH":"",t.useFog&&t.fog?"#define USE_FOG":"",t.useFog&&t.fogExp2?"#define FOG_EXP2":"",t.map?"#define USE_MAP":"",t.envMap?"#define USE_ENVMAP":"",t.envMap?"#define "+h:"",t.lightMap?"#define USE_LIGHTMAP":"",t.aoMap?"#define USE_AOMAP":"",t.bumpMap?"#define USE_BUMPMAP":"",t.normalMap?"#define USE_NORMALMAP":"",t.normalMapObjectSpace?"#define USE_NORMALMAP_OBJECTSPACE":"",t.normalMapTangentSpace?"#define USE_NORMALMAP_TANGENTSPACE":"",t.displacementMap?"#define USE_DISPLACEMENTMAP":"",t.emissiveMap?"#define USE_EMISSIVEMAP":"",t.anisotropy?"#define USE_ANISOTROPY":"",t.anisotropyMap?"#define USE_ANISOTROPYMAP":"",t.clearcoatMap?"#define USE_CLEARCOATMAP":"",t.clearcoatRoughnessMap?"#define USE_CLEARCOAT_ROUGHNESSMAP":"",t.clearcoatNormalMap?"#define USE_CLEARCOAT_NORMALMAP":"",t.iridescenceMap?"#define USE_IRIDESCENCEMAP":"",t.iridescenceThicknessMap?"#define USE_IRIDESCENCE_THICKNESSMAP":"",t.specularMap?"#define USE_SPECULARMAP":"",t.specularColorMap?"#define USE_SPECULAR_COLORMAP":"",t.specularIntensityMap?"#define USE_SPECULAR_INTENSITYMAP":"",t.roughnessMap?"#define USE_ROUGHNESSMAP":"",t.metalnessMap?"#define USE_METALNESSMAP":"",t.alphaMap?"#define USE_ALPHAMAP":"",t.alphaHash?"#define USE_ALPHAHASH":"",t.transmission?"#define USE_TRANSMISSION":"",t.transmissionMap?"#define USE_TRANSMISSIONMAP":"",t.thicknessMap?"#define USE_THICKNESSMAP":"",t.sheenColorMap?"#define USE_SHEEN_COLORMAP":"",t.sheenRoughnessMap?"#define USE_SHEEN_ROUGHNESSMAP":"",t.mapUv?"#define MAP_UV "+t.mapUv:"",t.alphaMapUv?"#define ALPHAMAP_UV "+t.alphaMapUv:"",t.lightMapUv?"#define LIGHTMAP_UV "+t.lightMapUv:"",t.aoMapUv?"#define AOMAP_UV "+t.aoMapUv:"",t.emissiveMapUv?"#define EMISSIVEMAP_UV "+t.emissiveMapUv:"",t.bumpMapUv?"#define BUMPMAP_UV "+t.bumpMapUv:"",t.normalMapUv?"#define NORMALMAP_UV "+t.normalMapUv:"",t.displacementMapUv?"#define DISPLACEMENTMAP_UV "+t.displacementMapUv:"",t.metalnessMapUv?"#define METALNESSMAP_UV "+t.metalnessMapUv:"",t.roughnessMapUv?"#define ROUGHNESSMAP_UV "+t.roughnessMapUv:"",t.anisotropyMapUv?"#define ANISOTROPYMAP_UV "+t.anisotropyMapUv:"",t.clearcoatMapUv?"#define CLEARCOATMAP_UV "+t.clearcoatMapUv:"",t.clearcoatNormalMapUv?"#define CLEARCOAT_NORMALMAP_UV "+t.clearcoatNormalMapUv:"",t.clearcoatRoughnessMapUv?"#define CLEARCOAT_ROUGHNESSMAP_UV "+t.clearcoatRoughnessMapUv:"",t.iridescenceMapUv?"#define IRIDESCENCEMAP_UV "+t.iridescenceMapUv:"",t.iridescenceThicknessMapUv?"#define IRIDESCENCE_THICKNESSMAP_UV "+t.iridescenceThicknessMapUv:"",t.sheenColorMapUv?"#define SHEEN_COLORMAP_UV "+t.sheenColorMapUv:"",t.sheenRoughnessMapUv?"#define SHEEN_ROUGHNESSMAP_UV "+t.sheenRoughnessMapUv:"",t.specularMapUv?"#define SPECULARMAP_UV "+t.specularMapUv:"",t.specularColorMapUv?"#define SPECULAR_COLORMAP_UV "+t.specularColorMapUv:"",t.specularIntensityMapUv?"#define SPECULAR_INTENSITYMAP_UV "+t.specularIntensityMapUv:"",t.transmissionMapUv?"#define TRANSMISSIONMAP_UV "+t.transmissionMapUv:"",t.thicknessMapUv?"#define THICKNESSMAP_UV "+t.thicknessMapUv:"",t.vertexTangents&&t.flatShading===!1?"#define USE_TANGENT":"",t.vertexNormals?"#define HAS_NORMAL":"",t.vertexColors?"#define USE_COLOR":"",t.vertexAlphas?"#define USE_COLOR_ALPHA":"",t.vertexUv1s?"#define USE_UV1":"",t.vertexUv2s?"#define USE_UV2":"",t.vertexUv3s?"#define USE_UV3":"",t.pointsUvs?"#define USE_POINTS_UV":"",t.flatShading?"#define FLAT_SHADED":"",t.skinning?"#define USE_SKINNING":"",t.morphTargets?"#define USE_MORPHTARGETS":"",t.morphNormals&&t.flatShading===!1?"#define USE_MORPHNORMALS":"",t.morphColors?"#define USE_MORPHCOLORS":"",t.morphTargetsCount>0?"#define MORPHTARGETS_TEXTURE_STRIDE "+t.morphTextureStride:"",t.morphTargetsCount>0?"#define MORPHTARGETS_COUNT "+t.morphTargetsCount:"",t.doubleSided?"#define DOUBLE_SIDED":"",t.flipSided?"#define FLIP_SIDED":"",t.shadowMapEnabled?"#define USE_SHADOWMAP":"",t.shadowMapEnabled?"#define "+l:"",t.sizeAttenuation?"#define USE_SIZEATTENUATION":"",t.numLightProbes>0?"#define USE_LIGHT_PROBES":"",t.logarithmicDepthBuffer?"#define USE_LOGARITHMIC_DEPTH_BUFFER":"",t.reversedDepthBuffer?"#define USE_REVERSED_DEPTH_BUFFER":"","uniform mat4 modelMatrix;","uniform mat4 modelViewMatrix;","uniform mat4 projectionMatrix;","uniform mat4 viewMatrix;","uniform mat3 normalMatrix;","uniform vec3 cameraPosition;","uniform bool isOrthographic;","#ifdef USE_INSTANCING","	attribute mat4 instanceMatrix;","#endif","#ifdef USE_INSTANCING_COLOR","	attribute vec3 instanceColor;","#endif","#ifdef USE_INSTANCING_MORPH","	uniform sampler2D morphTexture;","#endif","attribute vec3 position;","attribute vec3 normal;","attribute vec2 uv;","#ifdef USE_UV1","	attribute vec2 uv1;","#endif","#ifdef USE_UV2","	attribute vec2 uv2;","#endif","#ifdef USE_UV3","	attribute vec2 uv3;","#endif","#ifdef USE_TANGENT","	attribute vec4 tangent;","#endif","#if defined( USE_COLOR_ALPHA )","	attribute vec4 color;","#elif defined( USE_COLOR )","	attribute vec3 color;","#endif","#ifdef USE_SKINNING","	attribute vec4 skinIndex;","	attribute vec4 skinWeight;","#endif",`
`].filter($r).join(`
`),p=[wh(t),"#define SHADER_TYPE "+t.shaderType,"#define SHADER_NAME "+t.shaderName,_,t.useFog&&t.fog?"#define USE_FOG":"",t.useFog&&t.fogExp2?"#define FOG_EXP2":"",t.alphaToCoverage?"#define ALPHA_TO_COVERAGE":"",t.map?"#define USE_MAP":"",t.matcap?"#define USE_MATCAP":"",t.envMap?"#define USE_ENVMAP":"",t.envMap?"#define "+c:"",t.envMap?"#define "+h:"",t.envMap?"#define "+f:"",u?"#define CUBEUV_TEXEL_WIDTH "+u.texelWidth:"",u?"#define CUBEUV_TEXEL_HEIGHT "+u.texelHeight:"",u?"#define CUBEUV_MAX_MIP "+u.maxMip+".0":"",t.lightMap?"#define USE_LIGHTMAP":"",t.aoMap?"#define USE_AOMAP":"",t.bumpMap?"#define USE_BUMPMAP":"",t.normalMap?"#define USE_NORMALMAP":"",t.normalMapObjectSpace?"#define USE_NORMALMAP_OBJECTSPACE":"",t.normalMapTangentSpace?"#define USE_NORMALMAP_TANGENTSPACE":"",t.packedNormalMap?"#define USE_PACKED_NORMALMAP":"",t.emissiveMap?"#define USE_EMISSIVEMAP":"",t.anisotropy?"#define USE_ANISOTROPY":"",t.anisotropyMap?"#define USE_ANISOTROPYMAP":"",t.clearcoat?"#define USE_CLEARCOAT":"",t.clearcoatMap?"#define USE_CLEARCOATMAP":"",t.clearcoatRoughnessMap?"#define USE_CLEARCOAT_ROUGHNESSMAP":"",t.clearcoatNormalMap?"#define USE_CLEARCOAT_NORMALMAP":"",t.dispersion?"#define USE_DISPERSION":"",t.retroreflection?"#define USE_RETROREFLECTION":"",t.iridescence?"#define USE_IRIDESCENCE":"",t.iridescenceMap?"#define USE_IRIDESCENCEMAP":"",t.iridescenceThicknessMap?"#define USE_IRIDESCENCE_THICKNESSMAP":"",t.specularMap?"#define USE_SPECULARMAP":"",t.specularColorMap?"#define USE_SPECULAR_COLORMAP":"",t.specularIntensityMap?"#define USE_SPECULAR_INTENSITYMAP":"",t.roughnessMap?"#define USE_ROUGHNESSMAP":"",t.metalnessMap?"#define USE_METALNESSMAP":"",t.alphaMap?"#define USE_ALPHAMAP":"",t.alphaTest?"#define USE_ALPHATEST":"",t.alphaHash?"#define USE_ALPHAHASH":"",t.sheen?"#define USE_SHEEN":"",t.sheenColorMap?"#define USE_SHEEN_COLORMAP":"",t.sheenRoughnessMap?"#define USE_SHEEN_ROUGHNESSMAP":"",t.transmission?"#define USE_TRANSMISSION":"",t.transmissionMap?"#define USE_TRANSMISSIONMAP":"",t.thicknessMap?"#define USE_THICKNESSMAP":"",t.vertexTangents&&t.flatShading===!1?"#define USE_TANGENT":"",t.vertexColors||t.instancingColor?"#define USE_COLOR":"",t.vertexAlphas||t.batchingColor?"#define USE_COLOR_ALPHA":"",t.vertexUv1s?"#define USE_UV1":"",t.vertexUv2s?"#define USE_UV2":"",t.vertexUv3s?"#define USE_UV3":"",t.pointsUvs?"#define USE_POINTS_UV":"",t.gradientMap?"#define USE_GRADIENTMAP":"",t.flatShading?"#define FLAT_SHADED":"",t.doubleSided?"#define DOUBLE_SIDED":"",t.flipSided?"#define FLIP_SIDED":"",t.shadowMapEnabled?"#define USE_SHADOWMAP":"",t.shadowMapEnabled?"#define "+l:"",t.premultipliedAlpha?"#define PREMULTIPLIED_ALPHA":"",t.numLightProbes>0?"#define USE_LIGHT_PROBES":"",t.numLightProbeGrids>0?"#define USE_LIGHT_PROBES_GRID":"",t.decodeVideoTexture?"#define DECODE_VIDEO_TEXTURE":"",t.decodeVideoTextureEmissive?"#define DECODE_VIDEO_TEXTURE_EMISSIVE":"",t.logarithmicDepthBuffer?"#define USE_LOGARITHMIC_DEPTH_BUFFER":"",t.reversedDepthBuffer?"#define USE_REVERSED_DEPTH_BUFFER":"","uniform mat4 viewMatrix;","uniform vec3 cameraPosition;","uniform bool isOrthographic;",t.toneMapping!==Dn?"#define TONE_MAPPING":"",t.toneMapping!==Dn?nt.tonemapping_pars_fragment:"",t.toneMapping!==Dn?a0("toneMapping",t.toneMapping):"",t.dithering?"#define DITHERING":"",t.opaque?"#define OPAQUE":"",nt.colorspace_pars_fragment,s0("linearToOutputTexel",t.outputColorSpace),o0(),t.useDepthPacking?"#define DEPTH_PACKING "+t.depthPacking:"",`
`].filter($r).join(`
`)),a=Nc(a),a=Sh(a,t),a=Th(a,t),o=Nc(o),o=Sh(o,t),o=Th(o,t),a=Eh(a),o=Eh(o),t.isRawShaderMaterial!==!0&&(w=`#version 300 es
`,g=[d,"#define attribute in","#define varying out","#define texture2D texture"].join(`
`)+`
`+g,p=["#define varying in",t.glslVersion===mc?"":"layout(location = 0) out highp vec4 pc_fragColor;",t.glslVersion===mc?"":"#define gl_FragColor pc_fragColor","#define gl_FragDepthEXT gl_FragDepth","#define texture2D texture","#define textureCube texture","#define texture2DProj textureProj","#define texture2DLodEXT textureLod","#define texture2DProjLodEXT textureProjLod","#define textureCubeLodEXT textureLod","#define texture2DGradEXT textureGrad","#define texture2DProjGradEXT textureProjGrad","#define textureCubeGradEXT textureGrad"].join(`
`)+`
`+p);let I=w+g+a,y=w+p+o,A=yh(s,s.VERTEX_SHADER,I),E=yh(s,s.FRAGMENT_SHADER,y);s.attachShader(S,A),s.attachShader(S,E),t.index0AttributeName!==void 0?s.bindAttribLocation(S,0,t.index0AttributeName):t.hasPositionAttribute===!0&&s.bindAttribLocation(S,0,"position"),s.linkProgram(S);function D(V){if(i.debug.checkShaderErrors){let q=s.getProgramInfoLog(S)||"",j=s.getShaderInfoLog(A)||"",z=s.getShaderInfoLog(E)||"",Y=q.trim(),te=j.trim(),re=z.trim(),Z=!0,Q=!0;if(s.getProgramParameter(S,s.LINK_STATUS)===!1)if(Z=!1,typeof i.debug.onShaderError=="function")i.debug.onShaderError(s,S,A,E);else{let le=Mh(s,A,"vertex"),se=Mh(s,E,"fragment");Xe("WebGLProgram: Shader Error "+s.getError()+" - VALIDATE_STATUS "+s.getProgramParameter(S,s.VALIDATE_STATUS)+`

Material Name: `+V.name+`
Material Type: `+V.type+`

Program Info Log: `+Y+`
`+le+`
`+se)}else Y!==""?$e("WebGLProgram: Program Info Log:",Y):(te===""||re==="")&&(Q=!1);Q&&(V.diagnostics={runnable:Z,programLog:Y,vertexShader:{log:te,prefix:g},fragmentShader:{log:re,prefix:p}})}s.deleteShader(A),s.deleteShader(E),v=new Ds(s,S),C=u0(s,S)}let v;this.getUniforms=function(){return v===void 0&&D(this),v};let C;this.getAttributes=function(){return C===void 0&&D(this),C};let O=t.rendererExtensionParallelShaderCompile===!1;return this.isReady=function(){return O===!1&&(O=s.getProgramParameter(S,e0)),O},this.destroy=function(){n.releaseStatesOfProgram(this),s.deleteProgram(S),this.program=void 0},this.type=t.shaderType,this.name=t.shaderName,this.id=t0++,this.cacheKey=e,this.usedTimes=1,this.program=S,this.vertexShader=A,this.fragmentShader=E,this}var w0=0,Dc=class{constructor(){this.shaderCache=new Map,this.materialCache=new Map}update(e,t,n){let s=this._getShaderCacheForMaterial(e);return s.has(t)===!1&&(s.add(t),t.usedTimes++),s.has(n)===!1&&(s.add(n),n.usedTimes++),this}remove(e){let t=this.materialCache.get(e);for(let n of t)n.usedTimes--,n.usedTimes===0&&this.shaderCache.delete(n.code);return this.materialCache.delete(e),this}getVertexShaderStage(e){return this._getShaderStage(e.vertexShader)}getFragmentShaderStage(e){return this._getShaderStage(e.fragmentShader)}dispose(){this.shaderCache.clear(),this.materialCache.clear()}_getShaderCacheForMaterial(e){let t=this.materialCache,n=t.get(e);return n===void 0&&(n=new Set,t.set(e,n)),n}_getShaderStage(e){let t=this.shaderCache,n=t.get(e);return n===void 0&&(n=new Uc(e),t.set(e,n)),n}},Uc=class{constructor(e){this.id=w0++,this.code=e,this.usedTimes=0}};function A0(i){return i===Ti||i===zr||i===Vr}function C0(i,e,t,n,s,r){let a=new xs,o=new Dc,l=new Set,c=[],h=new Map,f=n.logarithmicDepthBuffer,u=n.precision,d={MeshDepthMaterial:"depth",MeshDistanceMaterial:"distance",MeshNormalMaterial:"normal",MeshBasicMaterial:"basic",MeshLambertMaterial:"lambert",MeshPhongMaterial:"phong",MeshToonMaterial:"toon",MeshStandardMaterial:"physical",MeshPhysicalMaterial:"physical",MeshMatcapMaterial:"matcap",LineBasicMaterial:"basic",LineDashedMaterial:"dashed",PointsMaterial:"points",ShadowMaterial:"shadow",SpriteMaterial:"sprite"};function _(v){return l.add(v),v===0?"uv":`uv${v}`}function S(v,C,O,V,q,j){let z=V.fog,Y=q.geometry,te=v.isMeshStandardMaterial||v.isMeshLambertMaterial||v.isMeshPhongMaterial?V.environment:null,re=v.isMeshStandardMaterial||v.isMeshLambertMaterial&&!v.envMap||v.isMeshPhongMaterial&&!v.envMap,Z=e.get(v.envMap||te,re),Q=Z&&Z.mapping===Dr?Z.image.height:null,le=d[v.type];v.precision!==null&&(u=n.getMaxPrecision(v.precision),u!==v.precision&&$e("WebGLProgram.getParameters:",v.precision,"not supported, using",u,"instead."));let se=Y.morphAttributes.position||Y.morphAttributes.normal||Y.morphAttributes.color,Oe=se!==void 0?se.length:0,Ie=0;Y.morphAttributes.position!==void 0&&(Ie=1),Y.morphAttributes.normal!==void 0&&(Ie=2),Y.morphAttributes.color!==void 0&&(Ie=3);let it,Ve,He,ee;if(le){let bt=qn[le];it=bt.vertexShader,Ve=bt.fragmentShader}else{it=v.vertexShader,Ve=v.fragmentShader;let bt=o.getVertexShaderStage(v),xt=o.getFragmentShaderStage(v);o.update(v,bt,xt),He=bt.id,ee=xt.id}let ae=i.getRenderTarget(),Me=i.state.buffers.depth.getReversed(),Pe=q.isInstancedMesh===!0,we=q.isBatchedMesh===!0,Ge=!!v.map,je=!!v.matcap,Ze=!!Z,Qe=!!v.aoMap,ht=!!v.lightMap,Je=!!v.bumpMap&&v.wireframe===!1,ft=!!v.normalMap,Et=!!v.displacementMap,Lt=!!v.emissiveMap,lt=!!v.metalnessMap,tt=!!v.roughnessMap,W=v.anisotropy>0,gt=v.clearcoat>0,et=v.dispersion>0,L=v.retroreflectivity>0,x=v.iridescence>0,X=v.sheen>0,K=v.transmission>0,oe=W&&!!v.anisotropyMap,be=gt&&!!v.clearcoatMap,Ae=gt&&!!v.clearcoatNormalMap,F=gt&&!!v.clearcoatRoughnessMap,$=x&&!!v.iridescenceMap,ie=x&&!!v.iridescenceThicknessMap,me=X&&!!v.sheenColorMap,ce=X&&!!v.sheenRoughnessMap,fe=!!v.specularMap,ye=!!v.specularColorMap,Ee=!!v.specularIntensityMap,Fe=K&&!!v.transmissionMap,H=K&&!!v.thicknessMap,Se=!!v.gradientMap,J=!!v.alphaMap,ve=v.alphaTest>0,Ce=!!v.alphaHash,de=!!v.extensions,Be=Dn;v.toneMapped&&(ae===null||ae.isXRRenderTarget===!0)&&(Be=i.toneMapping);let Ue={shaderID:le,shaderType:v.type,shaderName:v.name,vertexShader:it,fragmentShader:Ve,defines:v.defines,customVertexShaderID:He,customFragmentShaderID:ee,isRawShaderMaterial:v.isRawShaderMaterial===!0,glslVersion:v.glslVersion,precision:u,batching:we,batchingColor:we&&q._colorsTexture!==null,instancing:Pe,instancingColor:Pe&&q.instanceColor!==null,instancingMorph:Pe&&q.morphTexture!==null,outputColorSpace:ae===null?i.outputColorSpace:ae.isXRRenderTarget===!0?ae.texture.colorSpace:at.workingColorSpace,alphaToCoverage:!!v.alphaToCoverage,map:Ge,matcap:je,envMap:Ze,envMapMode:Ze&&Z.mapping,envMapCubeUVHeight:Q,aoMap:Qe,lightMap:ht,bumpMap:Je,normalMap:ft,displacementMap:Et,emissiveMap:Lt,normalMapObjectSpace:ft&&v.normalMapType===Yu,normalMapTangentSpace:ft&&v.normalMapType===Hr,packedNormalMap:ft&&v.normalMapType===Hr&&A0(v.normalMap.format),metalnessMap:lt,roughnessMap:tt,anisotropy:W,anisotropyMap:oe,clearcoat:gt,clearcoatMap:be,clearcoatNormalMap:Ae,clearcoatRoughnessMap:F,dispersion:et,retroreflection:L,iridescence:x,iridescenceMap:$,iridescenceThicknessMap:ie,sheen:X,sheenColorMap:me,sheenRoughnessMap:ce,specularMap:fe,specularColorMap:ye,specularIntensityMap:Ee,transmission:K,transmissionMap:Fe,thicknessMap:H,gradientMap:Se,opaque:v.transparent===!1&&v.blending===Cs&&v.alphaToCoverage===!1,alphaMap:J,alphaTest:ve,alphaHash:Ce,combine:v.combine,mapUv:Ge&&_(v.map.channel),aoMapUv:Qe&&_(v.aoMap.channel),lightMapUv:ht&&_(v.lightMap.channel),bumpMapUv:Je&&_(v.bumpMap.channel),normalMapUv:ft&&_(v.normalMap.channel),displacementMapUv:Et&&_(v.displacementMap.channel),emissiveMapUv:Lt&&_(v.emissiveMap.channel),metalnessMapUv:lt&&_(v.metalnessMap.channel),roughnessMapUv:tt&&_(v.roughnessMap.channel),anisotropyMapUv:oe&&_(v.anisotropyMap.channel),clearcoatMapUv:be&&_(v.clearcoatMap.channel),clearcoatNormalMapUv:Ae&&_(v.clearcoatNormalMap.channel),clearcoatRoughnessMapUv:F&&_(v.clearcoatRoughnessMap.channel),iridescenceMapUv:$&&_(v.iridescenceMap.channel),iridescenceThicknessMapUv:ie&&_(v.iridescenceThicknessMap.channel),sheenColorMapUv:me&&_(v.sheenColorMap.channel),sheenRoughnessMapUv:ce&&_(v.sheenRoughnessMap.channel),specularMapUv:fe&&_(v.specularMap.channel),specularColorMapUv:ye&&_(v.specularColorMap.channel),specularIntensityMapUv:Ee&&_(v.specularIntensityMap.channel),transmissionMapUv:Fe&&_(v.transmissionMap.channel),thicknessMapUv:H&&_(v.thicknessMap.channel),alphaMapUv:J&&_(v.alphaMap.channel),vertexTangents:!!Y.attributes.tangent&&(ft||W),vertexNormals:!!Y.attributes.normal,vertexColors:v.vertexColors,vertexAlphas:v.vertexColors===!0&&!!Y.attributes.color&&Y.attributes.color.itemSize===4,pointsUvs:q.isPoints===!0&&!!Y.attributes.uv&&(Ge||J),fog:!!z,useFog:v.fog===!0,fogExp2:!!z&&z.isFogExp2,flatShading:v.wireframe===!1&&(v.flatShading===!0||Y.attributes.normal===void 0&&ft===!1&&(v.isMeshLambertMaterial||v.isMeshPhongMaterial||v.isMeshStandardMaterial||v.isMeshPhysicalMaterial)),sizeAttenuation:v.sizeAttenuation===!0,logarithmicDepthBuffer:f,reversedDepthBuffer:Me,skinning:q.isSkinnedMesh===!0,hasPositionAttribute:Y.attributes.position!==void 0,morphTargets:Y.morphAttributes.position!==void 0,morphNormals:Y.morphAttributes.normal!==void 0,morphColors:Y.morphAttributes.color!==void 0,morphTargetsCount:Oe,morphTextureStride:Ie,numSunLights:C.sun.length,numDirLights:C.directional.length,numPointLights:C.point.length,numSpotLights:C.spot.length,numSpotLightMaps:C.spotLightMap.length,numRectAreaLights:C.rectArea.length,numHemiLights:C.hemi.length,numSunLightShadows:C.sunShadowMap.length,numDirLightShadows:C.directionalShadowMap.length,numPointLightShadows:C.pointShadowMap.length,numSpotLightShadows:C.spotShadowMap.length,numSpotLightShadowsWithMaps:C.numSpotLightShadowsWithMaps,numLightProbes:C.numLightProbes,numLightProbeGrids:j.length,numClippingPlanes:r.numPlanes,numClipIntersection:r.numIntersection,dithering:v.dithering,shadowMapEnabled:i.shadowMap.enabled&&O.length>0,shadowMapType:i.shadowMap.type,toneMapping:Be,decodeVideoTexture:Ge&&v.map.isVideoTexture===!0&&at.getTransfer(v.map.colorSpace)===yt,decodeVideoTextureEmissive:Lt&&v.emissiveMap.isVideoTexture===!0&&at.getTransfer(v.emissiveMap.colorSpace)===yt,premultipliedAlpha:v.premultipliedAlpha,doubleSided:v.side===Wn,flipSided:v.side===Zt,useDepthPacking:v.depthPacking>=0,depthPacking:v.depthPacking||0,index0AttributeName:v.index0AttributeName,extensionClipCullDistance:de&&v.extensions.clipCullDistance===!0&&t.has("WEBGL_clip_cull_distance"),extensionMultiDraw:(de&&v.extensions.multiDraw===!0||we)&&t.has("WEBGL_multi_draw"),rendererExtensionParallelShaderCompile:t.has("KHR_parallel_shader_compile"),customProgramCacheKey:v.customProgramCacheKey()};return Ue.vertexUv1s=l.has(1),Ue.vertexUv2s=l.has(2),Ue.vertexUv3s=l.has(3),l.clear(),Ue}function g(v){let C=[];if(v.shaderID?C.push(v.shaderID):(C.push(v.customVertexShaderID),C.push(v.customFragmentShaderID)),v.defines!==void 0)for(let O in v.defines)C.push(O),C.push(v.defines[O]);return v.isRawShaderMaterial===!1&&(p(C,v),w(C,v),C.push(i.outputColorSpace)),C.push(v.customProgramCacheKey),C.join()}function p(v,C){v.push(C.precision),v.push(C.outputColorSpace),v.push(C.envMapMode),v.push(C.envMapCubeUVHeight),v.push(C.mapUv),v.push(C.alphaMapUv),v.push(C.lightMapUv),v.push(C.aoMapUv),v.push(C.bumpMapUv),v.push(C.normalMapUv),v.push(C.displacementMapUv),v.push(C.emissiveMapUv),v.push(C.metalnessMapUv),v.push(C.roughnessMapUv),v.push(C.anisotropyMapUv),v.push(C.clearcoatMapUv),v.push(C.clearcoatNormalMapUv),v.push(C.clearcoatRoughnessMapUv),v.push(C.iridescenceMapUv),v.push(C.iridescenceThicknessMapUv),v.push(C.sheenColorMapUv),v.push(C.sheenRoughnessMapUv),v.push(C.specularMapUv),v.push(C.specularColorMapUv),v.push(C.specularIntensityMapUv),v.push(C.transmissionMapUv),v.push(C.thicknessMapUv),v.push(C.combine),v.push(C.fogExp2),v.push(C.sizeAttenuation),v.push(C.morphTargetsCount),v.push(C.morphAttributeCount),v.push(C.numSunLights),v.push(C.numDirLights),v.push(C.numPointLights),v.push(C.numSpotLights),v.push(C.numSpotLightMaps),v.push(C.numHemiLights),v.push(C.numRectAreaLights),v.push(C.numSunLightShadows),v.push(C.numDirLightShadows),v.push(C.numPointLightShadows),v.push(C.numSpotLightShadows),v.push(C.numSpotLightShadowsWithMaps),v.push(C.numLightProbes),v.push(C.shadowMapType),v.push(C.toneMapping),v.push(C.numClippingPlanes),v.push(C.numClipIntersection),v.push(C.depthPacking)}function w(v,C){a.disableAll(),C.instancing&&a.enable(0),C.instancingColor&&a.enable(1),C.instancingMorph&&a.enable(2),C.matcap&&a.enable(3),C.envMap&&a.enable(4),C.normalMapObjectSpace&&a.enable(5),C.normalMapTangentSpace&&a.enable(6),C.clearcoat&&a.enable(7),C.iridescence&&a.enable(8),C.alphaTest&&a.enable(9),C.vertexColors&&a.enable(10),C.vertexAlphas&&a.enable(11),C.vertexUv1s&&a.enable(12),C.vertexUv2s&&a.enable(13),C.vertexUv3s&&a.enable(14),C.vertexTangents&&a.enable(15),C.anisotropy&&a.enable(16),C.alphaHash&&a.enable(17),C.batching&&a.enable(18),C.dispersion&&a.enable(19),C.retroreflection&&a.enable(24),C.batchingColor&&a.enable(20),C.gradientMap&&a.enable(21),C.packedNormalMap&&a.enable(22),C.vertexNormals&&a.enable(23),v.push(a.mask),a.disableAll(),C.fog&&a.enable(0),C.useFog&&a.enable(1),C.flatShading&&a.enable(2),C.logarithmicDepthBuffer&&a.enable(3),C.reversedDepthBuffer&&a.enable(4),C.skinning&&a.enable(5),C.morphTargets&&a.enable(6),C.morphNormals&&a.enable(7),C.morphColors&&a.enable(8),C.premultipliedAlpha&&a.enable(9),C.shadowMapEnabled&&a.enable(10),C.doubleSided&&a.enable(11),C.flipSided&&a.enable(12),C.useDepthPacking&&a.enable(13),C.dithering&&a.enable(14),C.transmission&&a.enable(15),C.sheen&&a.enable(16),C.opaque&&a.enable(17),C.pointsUvs&&a.enable(18),C.decodeVideoTexture&&a.enable(19),C.decodeVideoTextureEmissive&&a.enable(20),C.alphaToCoverage&&a.enable(21),C.numLightProbeGrids>0&&a.enable(22),C.hasPositionAttribute&&a.enable(23),v.push(a.mask)}function I(v){let C=d[v.type],O;if(C){let V=qn[C];O=ni.clone(V.uniforms)}else O=v.uniforms;return O}function y(v,C){let O=h.get(C);return O!==void 0?++O.usedTimes:(O=new E0(i,C,v,s),c.push(O),h.set(C,O)),O}function A(v){if(--v.usedTimes===0){let C=c.indexOf(v);c[C]=c[c.length-1],c.pop(),h.delete(v.cacheKey),v.destroy()}}function E(v){o.remove(v)}function D(){o.dispose()}return{getParameters:S,getProgramCacheKey:g,getUniforms:I,acquireProgram:y,releaseProgram:A,releaseShaderCache:E,programs:c,dispose:D}}function R0(){let i=new WeakMap;function e(a){return i.has(a)}function t(a){let o=i.get(a);return o===void 0&&(o={},i.set(a,o)),o}function n(a){i.delete(a)}function s(a,o,l){i.get(a)[o]=l}function r(){i=new WeakMap}return{has:e,get:t,remove:n,update:s,dispose:r}}function I0(i,e){return i.groupOrder!==e.groupOrder?i.groupOrder-e.groupOrder:i.renderOrder!==e.renderOrder?i.renderOrder-e.renderOrder:i.material.id!==e.material.id?i.material.id-e.material.id:i.materialVariant!==e.materialVariant?i.materialVariant-e.materialVariant:i.z!==e.z?i.z-e.z:i.id-e.id}function Ah(i,e){return i.groupOrder!==e.groupOrder?i.groupOrder-e.groupOrder:i.renderOrder!==e.renderOrder?i.renderOrder-e.renderOrder:i.z!==e.z?e.z-i.z:i.id-e.id}function Ch(){let i=[],e=0,t=[],n=[],s=[];function r(){e=0,t.length=0,n.length=0,s.length=0}function a(u){let d=0;return u.isInstancedMesh&&(d+=2),u.isSkinnedMesh&&(d+=1),d}function o(u,d,_,S,g,p){let w=i[e];return w===void 0?(w={id:u.id,object:u,geometry:d,material:_,materialVariant:a(u),groupOrder:S,renderOrder:u.renderOrder,z:g,group:p},i[e]=w):(w.id=u.id,w.object=u,w.geometry=d,w.material=_,w.materialVariant=a(u),w.groupOrder=S,w.renderOrder=u.renderOrder,w.z=g,w.group=p),e++,w}function l(u,d,_,S,g,p,w){w.reversedDepth===!0&&(g=-g);let I=o(u,d,_,S,g,p);_.transmission>0?n.push(I):_.transparent===!0?s.push(I):t.push(I)}function c(u,d,_,S,g,p){let w=o(u,d,_,S,g,p);_.transmission>0?n.unshift(w):_.transparent===!0?s.unshift(w):t.unshift(w)}function h(u,d){t.length>1&&t.sort(u||I0),n.length>1&&n.sort(d||Ah),s.length>1&&s.sort(d||Ah)}function f(){for(let u=e,d=i.length;u<d;u++){let _=i[u];if(_.id===null)break;_.id=null,_.object=null,_.geometry=null,_.material=null,_.group=null}}return{opaque:t,transmissive:n,transparent:s,init:r,push:l,unshift:c,finish:f,sort:h}}function P0(){let i=new WeakMap;function e(n,s){let r=i.get(n),a;return r===void 0?(a=new Ch,i.set(n,[a])):s>=r.length?(a=new Ch,r.push(a)):a=r[s],a}function t(){i=new WeakMap}return{get:e,dispose:t}}function L0(){let i={};return{get:function(e){if(i[e.id]!==void 0)return i[e.id];let t;switch(e.type){case"SunLight":case"DirectionalLight":t={direction:new B,color:new qe};break;case"SpotLight":t={position:new B,direction:new B,color:new qe,distance:0,coneCos:0,penumbraCos:0,decay:0};break;case"PointLight":t={position:new B,color:new qe,distance:0,decay:0};break;case"HemisphereLight":t={direction:new B,skyColor:new qe,groundColor:new qe};break;case"RectAreaLight":t={color:new qe,position:new B,halfWidth:new B,halfHeight:new B};break}return i[e.id]=t,t}}}function N0(){let i={};return{get:function(e){if(i[e.id]!==void 0)return i[e.id];let t;switch(e.type){case"SunLight":case"DirectionalLight":t={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new De};break;case"SpotLight":t={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new De};break;case"PointLight":t={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new De,shadowCameraNear:1,shadowCameraFar:1e3};break}return i[e.id]=t,t}}}var D0=0;function U0(i,e){return(e.castShadow?2:0)-(i.castShadow?2:0)+(e.map?1:0)-(i.map?1:0)}function F0(i){let e=new L0,t=N0(),n={version:0,hash:{sunLength:-1,directionalLength:-1,pointLength:-1,spotLength:-1,rectAreaLength:-1,hemiLength:-1,numSunShadows:-1,numDirectionalShadows:-1,numPointShadows:-1,numSpotShadows:-1,numSpotMaps:-1,numLightProbes:-1},ambient:[0,0,0],probe:[],sun:[],sunShadow:[],sunShadowMap:[],sunShadowMatrix:[],sunShadowCascade:[],directional:[],directionalShadow:[],directionalShadowMap:[],directionalShadowMatrix:[],spot:[],spotLightMap:[],spotShadow:[],spotShadowMap:[],spotLightMatrix:[],rectArea:[],rectAreaLTC1:null,rectAreaLTC2:null,point:[],pointShadow:[],pointShadowMap:[],pointShadowMatrix:[],hemi:[],numSpotLightShadowsWithMaps:0,numLightProbes:0};for(let c=0;c<9;c++)n.probe.push(new B);let s=new B,r=new ut,a=new ut;function o(c){let h=0,f=0,u=0;for(let q=0;q<9;q++)n.probe[q].set(0,0,0);let d=0,_=0,S=0,g=0,p=0,w=0,I=0,y=0,A=0,E=0,D=0,v=0,C=0,O=0;c.sort(U0);for(let q=0,j=c.length;q<j;q++){let z=c[q],Y=z.color,te=z.intensity,re=z.distance,Z=null;if(z.shadow&&z.shadow.map&&(z.shadow.map.texture.format===Ti?Z=z.shadow.map.texture:Z=z.shadow.map.depthTexture||z.shadow.map.texture),z.isAmbientLight)h+=Y.r*te,f+=Y.g*te,u+=Y.b*te;else if(z.isLightProbe){for(let Q=0;Q<9;Q++)n.probe[Q].addScaledVector(z.sh.coefficients[Q],te);O++}else if(z.isSunLight){let Q=e.get(z);if(Q.color.copy(z.color).multiplyScalar(z.intensity),z.castShadow){let le=z.shadow,se=t.get(z);se.shadowIntensity=le.intensity,se.shadowBias=le.bias,se.shadowNormalBias=le.normalBias,se.shadowRadius=le.radius,se.shadowMapSize.copy(le.mapSize).multiply(le.getFrameExtents()),n.sunShadow[_]=se,n.sunShadowMap[_]=Z;let Oe=le.getViewportCount();for(let Ie=0;Ie<Oe;Ie++)n.sunShadowMatrix[S+Ie]=le.getMatrix(Ie),n.sunShadowCascade[S+Ie]=le._cascadeData[Ie];S+=Oe,_++}n.sun[d]=Q,d++}else if(z.isDirectionalLight){let Q=e.get(z);if(Q.color.copy(z.color).multiplyScalar(z.intensity),z.castShadow){let le=z.shadow,se=t.get(z);se.shadowIntensity=le.intensity,se.shadowBias=le.bias,se.shadowNormalBias=le.normalBias,se.shadowRadius=le.radius,se.shadowMapSize=le.mapSize,n.directionalShadow[g]=se,n.directionalShadowMap[g]=Z,n.directionalShadowMatrix[g]=z.shadow.matrix,A++}n.directional[g]=Q,g++}else if(z.isSpotLight){let Q=e.get(z);Q.position.setFromMatrixPosition(z.matrixWorld),Q.color.copy(Y).multiplyScalar(te),Q.distance=re,Q.coneCos=Math.cos(z.angle),Q.penumbraCos=Math.cos(z.angle*(1-z.penumbra)),Q.decay=z.decay,n.spot[w]=Q;let le=z.shadow;if(z.map&&(n.spotLightMap[v]=z.map,v++,le.updateMatrices(z),z.castShadow&&C++),n.spotLightMatrix[w]=le.matrix,z.castShadow){let se=t.get(z);se.shadowIntensity=le.intensity,se.shadowBias=le.bias,se.shadowNormalBias=le.normalBias,se.shadowRadius=le.radius,se.shadowMapSize=le.mapSize,n.spotShadow[w]=se,n.spotShadowMap[w]=Z,D++}w++}else if(z.isRectAreaLight){let Q=e.get(z);Q.color.copy(Y).multiplyScalar(te),Q.halfWidth.set(z.width*.5,0,0),Q.halfHeight.set(0,z.height*.5,0),n.rectArea[I]=Q,I++}else if(z.isPointLight){let Q=e.get(z);if(Q.color.copy(z.color).multiplyScalar(z.intensity),Q.distance=z.distance,Q.decay=z.decay,z.castShadow){let le=z.shadow,se=t.get(z);se.shadowIntensity=le.intensity,se.shadowBias=le.bias,se.shadowNormalBias=le.normalBias,se.shadowRadius=le.radius,se.shadowMapSize=le.mapSize,se.shadowCameraNear=le.camera.near,se.shadowCameraFar=le.camera.far,n.pointShadow[p]=se,n.pointShadowMap[p]=Z,n.pointShadowMatrix[p]=z.shadow.matrix,E++}n.point[p]=Q,p++}else if(z.isHemisphereLight){let Q=e.get(z);Q.skyColor.copy(z.color).multiplyScalar(te),Q.groundColor.copy(z.groundColor).multiplyScalar(te),n.hemi[y]=Q,y++}}I>0&&(i.has("OES_texture_float_linear")===!0?(n.rectAreaLTC1=Le.LTC_FLOAT_1,n.rectAreaLTC2=Le.LTC_FLOAT_2):(n.rectAreaLTC1=Le.LTC_HALF_1,n.rectAreaLTC2=Le.LTC_HALF_2)),n.ambient[0]=h,n.ambient[1]=f,n.ambient[2]=u;let V=n.hash;(V.sunLength!==d||V.directionalLength!==g||V.pointLength!==p||V.spotLength!==w||V.rectAreaLength!==I||V.hemiLength!==y||V.numSunShadows!==_||V.numDirectionalShadows!==A||V.numPointShadows!==E||V.numSpotShadows!==D||V.numSpotMaps!==v||V.numLightProbes!==O)&&(n.sun.length=d,n.directional.length=g,n.spot.length=w,n.rectArea.length=I,n.point.length=p,n.hemi.length=y,n.sunShadow.length=_,n.sunShadowMap.length=_,n.sunShadowMatrix.length=S,n.sunShadowCascade.length=S,n.directionalShadow.length=A,n.directionalShadowMap.length=A,n.directionalShadowMatrix.length=A,n.pointShadow.length=E,n.pointShadowMap.length=E,n.pointShadowMatrix.length=E,n.spotShadow.length=D,n.spotShadowMap.length=D,n.spotLightMatrix.length=D+v-C,n.spotLightMap.length=v,n.numSpotLightShadowsWithMaps=C,n.numLightProbes=O,V.sunLength=d,V.directionalLength=g,V.pointLength=p,V.spotLength=w,V.rectAreaLength=I,V.hemiLength=y,V.numSunShadows=_,V.numDirectionalShadows=A,V.numPointShadows=E,V.numSpotShadows=D,V.numSpotMaps=v,V.numLightProbes=O,n.version=D0++)}function l(c,h){let f=0,u=0,d=0,_=0,S=0,g=0,p=h.matrixWorldInverse;for(let w=0,I=c.length;w<I;w++){let y=c[w];if(y.isSunLight){let A=n.sun[f];A.direction.setFromMatrixPosition(y.matrixWorld),A.direction.transformDirection(p),f++}else if(y.isDirectionalLight){let A=n.directional[u];A.direction.setFromMatrixPosition(y.matrixWorld),s.setFromMatrixPosition(y.target.matrixWorld),A.direction.sub(s),A.direction.transformDirection(p),u++}else if(y.isSpotLight){let A=n.spot[_];A.position.setFromMatrixPosition(y.matrixWorld),A.position.applyMatrix4(p),A.direction.setFromMatrixPosition(y.matrixWorld),s.setFromMatrixPosition(y.target.matrixWorld),A.direction.sub(s),A.direction.transformDirection(p),_++}else if(y.isRectAreaLight){let A=n.rectArea[S];A.position.setFromMatrixPosition(y.matrixWorld),A.position.applyMatrix4(p),a.identity(),r.copy(y.matrixWorld),r.premultiply(p),a.extractRotation(r),A.halfWidth.set(y.width*.5,0,0),A.halfHeight.set(0,y.height*.5,0),A.halfWidth.applyMatrix4(a),A.halfHeight.applyMatrix4(a),S++}else if(y.isPointLight){let A=n.point[d];A.position.setFromMatrixPosition(y.matrixWorld),A.position.applyMatrix4(p),d++}else if(y.isHemisphereLight){let A=n.hemi[g];A.direction.setFromMatrixPosition(y.matrixWorld),A.direction.transformDirection(p),g++}}}return{setup:o,setupView:l,state:n}}function Rh(i){let e=new F0(i),t=[],n=[],s=[];function r(u){f.camera=u,t.length=0,n.length=0,s.length=0}function a(u){t.push(u)}function o(u){n.push(u)}function l(u){s.push(u)}function c(){e.setup(t)}function h(u){e.setupView(t,u)}let f={lightsArray:t,shadowsArray:n,lightProbeGridArray:s,camera:null,lights:e,transmissionRenderTarget:{},textureUnits:0};return{init:r,state:f,setupLights:c,setupLightsView:h,pushLight:a,pushShadow:o,pushLightProbeGrid:l}}function k0(i){let e=new WeakMap;function t(s,r=0){let a=e.get(s),o;return a===void 0?(o=new Rh(i),e.set(s,[o])):r>=a.length?(o=new Rh(i),a.push(o)):o=a[r],o}function n(){e=new WeakMap}return{get:t,dispose:n}}var O0=`void main() {
	gl_Position = vec4( position, 1.0 );
}`,B0=`uniform sampler2D shadow_pass;
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
}`,z0=[new B(1,0,0),new B(-1,0,0),new B(0,1,0),new B(0,-1,0),new B(0,0,1),new B(0,0,-1)],V0=[new B(0,-1,0),new B(0,-1,0),new B(0,0,1),new B(0,0,-1),new B(0,-1,0),new B(0,-1,0)],Ih=new ut,Wr=new B,Cc=new B;function H0(i,e,t){let n=new ys,s=new De,r=new De,a=new It,o=new Ja,l=new Ka,c={},h=t.maxTextureSize,f={[yi]:Zt,[Zt]:yi,[Wn]:Wn},u=new Nt({defines:{VSM_SAMPLES:8},uniforms:{shadow_pass:{value:null},resolution:{value:new De},radius:{value:4}},vertexShader:O0,fragmentShader:B0}),d=u.clone();d.defines.HORIZONTAL_PASS=1;let _=new St;_.setAttribute("position",new Xt(new Float32Array([-1,-1,.5,3,-1,.5,-1,3,.5]),3));let S=new mt(_,u),g=this;this.enabled=!1,this.autoUpdate=!0,this.needsUpdate=!1,this.type=Ar;let p=this.type;this.render=function(E,D,v){if(g.enabled===!1||g.autoUpdate===!1&&g.needsUpdate===!1||E.length===0)return;this.type===Eu&&($e("WebGLShadowMap: PCFSoftShadowMap has been removed. Using PCFShadowMap instead."),this.type=Ar);let C=i.getRenderTarget(),O=i.getActiveCubeFace(),V=i.getActiveMipmapLevel(),q=i.state;q.setBlending(Mn),q.buffers.depth.getReversed()===!0?q.buffers.color.setClear(0,0,0,0):q.buffers.color.setClear(1,1,1,1),q.buffers.depth.setTest(!0),q.setScissorTest(!1);let j=p!==this.type;j&&D.traverse(function(z){z.material&&(Array.isArray(z.material)?z.material.forEach(Y=>Y.needsUpdate=!0):z.material.needsUpdate=!0)});for(let z=0,Y=E.length;z<Y;z++){let te=E[z],re=te.shadow;if(re===void 0){$e("WebGLShadowMap:",te,"has no shadow.");continue}if(re.autoUpdate===!1&&re.needsUpdate===!1)continue;s.copy(re.mapSize);let Z=re.getFrameExtents();s.multiply(Z),r.copy(re.mapSize),(s.x>h||s.y>h)&&(s.x>h&&(r.x=Math.floor(h/Z.x),s.x=r.x*Z.x,re.mapSize.x=r.x),s.y>h&&(r.y=Math.floor(h/Z.y),s.y=r.y*Z.y,re.mapSize.y=r.y));let Q=i.state.buffers.depth.getReversed();if(re.camera._reversedDepth=Q,re.map===null||j===!0){if(re.map!==null&&(re.map.depthTexture!==null&&(re.map.depthTexture.dispose(),re.map.depthTexture=null),re.map.dispose()),this.type===As){if(te.isPointLight){$e("WebGLShadowMap: VSM shadow maps are not supported for PointLights. Use PCF or BasicShadowMap instead.");continue}re.map=new Ft(s.x,s.y,{format:Ti,type:jt,minFilter:Yt,magFilter:Yt,generateMipmaps:!1}),re.map.texture.name=te.name+".shadowMap",re.map.depthTexture=new mi(s.x,s.y,Sn),re.map.depthTexture.name=te.name+".shadowMapDepth",re.map.depthTexture.format=Bn,re.map.depthTexture.compareFunction=null,re.map.depthTexture.minFilter=Gt,re.map.depthTexture.magFilter=Gt}else te.isPointLight?(re.map=new sl(s.x),re.map.depthTexture=new Ga(s.x,Un)):(re.map=new Ft(s.x,s.y),re.map.depthTexture=new mi(s.x,s.y,Un)),re.map.depthTexture.name=te.name+".shadowMap",re.map.depthTexture.format=Bn,this.type===Ar?(re.map.depthTexture.compareFunction=Q?el:Qo,re.map.depthTexture.minFilter=Yt,re.map.depthTexture.magFilter=Yt):(re.map.depthTexture.compareFunction=null,re.map.depthTexture.minFilter=Gt,re.map.depthTexture.magFilter=Gt);re.camera.updateProjectionMatrix()}re.map.isWebGLCubeRenderTarget!==!0&&(re.map.width!==s.x||re.map.height!==s.y)&&re.map.setSize(s.x,s.y);let le=re.map.isWebGLCubeRenderTarget?6:re.getViewportCount();te.isPointLight!==!0&&re.updateMatrices(te,v);for(let se=0;se<le;se++){let Oe=re.getCamera(se);if(te.isPointLight){let Ie=re.camera,it=re.matrix,Ve=te.distance||Ie.far;Ve!==Ie.far&&(Ie.far=Ve,Ie.updateProjectionMatrix()),Wr.setFromMatrixPosition(te.matrixWorld),Ie.position.copy(Wr),Cc.copy(Ie.position),Cc.add(z0[se]),Ie.up.copy(V0[se]),Ie.lookAt(Cc),Ie.updateMatrixWorld(),it.makeTranslation(-Wr.x,-Wr.y,-Wr.z),Ih.multiplyMatrices(Ie.projectionMatrix,Ie.matrixWorldInverse),re._frustum.setFromProjectionMatrix(Ih,Ie.coordinateSystem,Ie.reversedDepth)}if(re.map.isWebGLCubeRenderTarget)i.setRenderTarget(re.map,se),i.clear();else{se===0&&(i.setRenderTarget(re.map),i.clear());let Ie=re.getViewport(se);a.set(r.x*Ie.x,r.y*Ie.y,r.x*Ie.z,r.y*Ie.w),q.viewport(a)}n=re.getFrustum(se),y(D,v,Oe,te,this.type)}re.isPointLightShadow!==!0&&this.type===As&&w(re,v),re.needsUpdate=!1}p=this.type,g.needsUpdate=!1,i.setRenderTarget(C,O,V)};function w(E,D){let v=e.update(S);u.defines.VSM_SAMPLES!==E.blurSamples&&(u.defines.VSM_SAMPLES=E.blurSamples,d.defines.VSM_SAMPLES=E.blurSamples,u.needsUpdate=!0,d.needsUpdate=!0),E.mapPass===null?E.mapPass=new Ft(s.x,s.y,{format:Ti,type:jt}):(E.mapPass.width!==E.map.width||E.mapPass.height!==E.map.height)&&E.mapPass.setSize(E.map.width,E.map.height),u.uniforms.shadow_pass.value=E.map.depthTexture,u.uniforms.resolution.value.set(E.map.width,E.map.height),u.uniforms.radius.value=E.radius,i.setRenderTarget(E.mapPass),i.clear(),i.renderBufferDirect(D,null,v,u,S,null),d.uniforms.shadow_pass.value=E.mapPass.texture,d.uniforms.resolution.value.set(E.map.width,E.map.height),d.uniforms.radius.value=E.radius,i.setRenderTarget(E.map),i.clear(),i.renderBufferDirect(D,null,v,d,S,null)}function I(E,D,v,C){let O=null,V=v.isPointLight===!0?E.customDistanceMaterial:E.customDepthMaterial;if(V!==void 0)O=V;else if(O=v.isPointLight===!0?l:o,i.localClippingEnabled&&D.clipShadows===!0&&Array.isArray(D.clippingPlanes)&&D.clippingPlanes.length!==0||D.displacementMap&&D.displacementScale!==0||D.alphaMap&&D.alphaTest>0||D.map&&D.alphaTest>0||D.alphaToCoverage===!0){let q=O.uuid,j=D.uuid,z=c[q];z===void 0&&(z={},c[q]=z);let Y=z[j];Y===void 0&&(Y=O.clone(),z[j]=Y,D.addEventListener("dispose",A)),O=Y}if(O.visible=D.visible,O.wireframe=D.wireframe,C===As?O.side=D.shadowSide!==null?D.shadowSide:D.side:O.side=D.shadowSide!==null?D.shadowSide:f[D.side],O.alphaMap=D.alphaMap,O.alphaTest=D.alphaToCoverage===!0?.5:D.alphaTest,O.map=D.map,O.clipShadows=D.clipShadows,O.clippingPlanes=D.clippingPlanes,O.clipIntersection=D.clipIntersection,O.displacementMap=D.displacementMap,O.displacementScale=D.displacementScale,O.displacementBias=D.displacementBias,O.wireframeLinewidth=D.wireframeLinewidth,O.linewidth=D.linewidth,v.isPointLight===!0&&O.isMeshDistanceMaterial===!0){let q=i.properties.get(O);q.light=v}return O}function y(E,D,v,C,O){if(E.visible===!1)return;if(E.layers.test(D.layers)&&(E.isMesh||E.isLine||E.isPoints)&&(E.castShadow||E.receiveShadow&&O===As)&&(!E.frustumCulled||E.intersectsFrustum(n))){E.modelViewMatrix.multiplyMatrices(v.matrixWorldInverse,E.matrixWorld);let j=e.update(E),z=E.material;if(Array.isArray(z)){let Y=j.groups;for(let te=0,re=Y.length;te<re;te++){let Z=Y[te],Q=z[Z.materialIndex];if(Q&&Q.visible){let le=I(E,Q,C,O);E.onBeforeShadow(i,E,D,v,j,le,Z),i.renderBufferDirect(v,null,j,le,E,Z),E.onAfterShadow(i,E,D,v,j,le,Z)}}}else if(z.visible){let Y=I(E,z,C,O);E.onBeforeShadow(i,E,D,v,j,Y,null),i.renderBufferDirect(v,null,j,Y,E,null),E.onAfterShadow(i,E,D,v,j,Y,null)}}let q=E.children;for(let j=0,z=q.length;j<z;j++)y(q[j],D,v,C,O)}function A(E){E.target.removeEventListener("dispose",A);for(let v in c){let C=c[v],O=E.target.uuid;O in C&&(C[O].dispose(),delete C[O])}}}function G0(i,e){function t(){let H=!1,Se=new It,J=null,ve=new It(0,0,0,0);return{setMask:function(Ce){J!==Ce&&!H&&(i.colorMask(Ce,Ce,Ce,Ce),J=Ce)},setLocked:function(Ce){H=Ce},setClear:function(Ce,de,Be,Ue,bt){bt===!0&&(Ce*=Ue,de*=Ue,Be*=Ue),Se.set(Ce,de,Be,Ue),ve.equals(Se)===!1&&(i.clearColor(Ce,de,Be,Ue),ve.copy(Se))},reset:function(){H=!1,J=null,ve.set(-1,0,0,0)}}}function n(){let H=!1,Se=!1,J=null,ve=null,Ce=null;return{setReversed:function(de){if(Se!==de){let Be=e.get("EXT_clip_control");de?Be.clipControlEXT(Be.LOWER_LEFT_EXT,Be.ZERO_TO_ONE_EXT):Be.clipControlEXT(Be.LOWER_LEFT_EXT,Be.NEGATIVE_ONE_TO_ONE_EXT),Se=de;let Ue=Ce;Ce=null,this.setClear(Ue)}},getReversed:function(){return Se},setTest:function(de){de?ae(i.DEPTH_TEST):Me(i.DEPTH_TEST)},setMask:function(de){J!==de&&!H&&(i.depthMask(de),J=de)},setFunc:function(de){if(Se&&(de=ah[de]),ve!==de){switch(de){case Ca:i.depthFunc(i.NEVER);break;case Ra:i.depthFunc(i.ALWAYS);break;case Ia:i.depthFunc(i.LESS);break;case fs:i.depthFunc(i.LEQUAL);break;case Pa:i.depthFunc(i.EQUAL);break;case La:i.depthFunc(i.GEQUAL);break;case Na:i.depthFunc(i.GREATER);break;case Da:i.depthFunc(i.NOTEQUAL);break;default:i.depthFunc(i.LEQUAL)}ve=de}},setLocked:function(de){H=de},setClear:function(de){Ce!==de&&(Ce=de,Se&&(de=1-de),i.clearDepth(de))},reset:function(){H=!1,J=null,ve=null,Ce=null,Se=!1}}}function s(){let H=!1,Se=null,J=null,ve=null,Ce=null,de=null,Be=null,Ue=null,bt=null;return{setTest:function(xt){H||(xt?ae(i.STENCIL_TEST):Me(i.STENCIL_TEST))},setMask:function(xt){Se!==xt&&!H&&(i.stencilMask(xt),Se=xt)},setFunc:function(xt,hn,gn){(J!==xt||ve!==hn||Ce!==gn)&&(i.stencilFunc(xt,hn,gn),J=xt,ve=hn,Ce=gn)},setOp:function(xt,hn,gn){(de!==xt||Be!==hn||Ue!==gn)&&(i.stencilOp(xt,hn,gn),de=xt,Be=hn,Ue=gn)},setLocked:function(xt){H=xt},setClear:function(xt){bt!==xt&&(i.clearStencil(xt),bt=xt)},reset:function(){H=!1,Se=null,J=null,ve=null,Ce=null,de=null,Be=null,Ue=null,bt=null}}}let r=new t,a=new n,o=new s,l=new WeakMap,c=new WeakMap,h={},f={},u={},d=new WeakMap,_=[],S=null,g=!1,p=null,w=null,I=null,y=null,A=null,E=null,D=null,v=new qe(0,0,0),C=0,O=!1,V=null,q=null,j=null,z=null,Y=null,te=i.getParameter(i.MAX_COMBINED_TEXTURE_IMAGE_UNITS),re=!1,Z=0,Q=i.getParameter(i.VERSION);Q.indexOf("WebGL")!==-1?(Z=parseFloat(/^WebGL (\d)/.exec(Q)[1]),re=Z>=1):Q.indexOf("OpenGL ES")!==-1&&(Z=parseFloat(/^OpenGL ES (\d)/.exec(Q)[1]),re=Z>=2);let le=null,se={},Oe=i.getParameter(i.SCISSOR_BOX),Ie=i.getParameter(i.VIEWPORT),it=new It().fromArray(Oe),Ve=new It().fromArray(Ie);function He(H,Se,J,ve){let Ce=new Uint8Array(4),de=i.createTexture();i.bindTexture(H,de),i.texParameteri(H,i.TEXTURE_MIN_FILTER,i.NEAREST),i.texParameteri(H,i.TEXTURE_MAG_FILTER,i.NEAREST);for(let Be=0;Be<J;Be++)H===i.TEXTURE_3D||H===i.TEXTURE_2D_ARRAY?i.texImage3D(Se,0,i.RGBA,1,1,ve,0,i.RGBA,i.UNSIGNED_BYTE,Ce):i.texImage2D(Se+Be,0,i.RGBA,1,1,0,i.RGBA,i.UNSIGNED_BYTE,Ce);return de}let ee={};ee[i.TEXTURE_2D]=He(i.TEXTURE_2D,i.TEXTURE_2D,1),ee[i.TEXTURE_CUBE_MAP]=He(i.TEXTURE_CUBE_MAP,i.TEXTURE_CUBE_MAP_POSITIVE_X,6),ee[i.TEXTURE_2D_ARRAY]=He(i.TEXTURE_2D_ARRAY,i.TEXTURE_2D_ARRAY,1,1),ee[i.TEXTURE_3D]=He(i.TEXTURE_3D,i.TEXTURE_3D,1,1),r.setClear(0,0,0,1),a.setClear(1),o.setClear(0),ae(i.DEPTH_TEST),a.setFunc(fs),Je(!1),ft(nc),ae(i.CULL_FACE),Qe(Mn);function ae(H){h[H]!==!0&&(i.enable(H),h[H]=!0)}function Me(H){h[H]!==!1&&(i.disable(H),h[H]=!1)}function Pe(H,Se){return u[H]!==Se?(i.bindFramebuffer(H,Se),u[H]=Se,H===i.DRAW_FRAMEBUFFER&&(u[i.FRAMEBUFFER]=Se),H===i.FRAMEBUFFER&&(u[i.DRAW_FRAMEBUFFER]=Se),!0):!1}function we(H,Se){let J=_,ve=!1;if(H){J=d.get(Se),J===void 0&&(J=[],d.set(Se,J));let Ce=H.textures;if(J.length!==Ce.length||J[0]!==i.COLOR_ATTACHMENT0){for(let de=0,Be=Ce.length;de<Be;de++)J[de]=i.COLOR_ATTACHMENT0+de;J.length=Ce.length,ve=!0}}else J[0]!==i.BACK&&(J[0]=i.BACK,ve=!0);ve&&i.drawBuffers(J)}function Ge(H){return S!==H?(i.useProgram(H),S=H,!0):!1}let je={[zi]:i.FUNC_ADD,[Au]:i.FUNC_SUBTRACT,[Cu]:i.FUNC_REVERSE_SUBTRACT};je[Ru]=i.MIN,je[Iu]=i.MAX;let Ze={[Pu]:i.ZERO,[Lu]:i.ONE,[Nu]:i.SRC_COLOR,[rc]:i.SRC_ALPHA,[Bu]:i.SRC_ALPHA_SATURATE,[ku]:i.DST_COLOR,[Uu]:i.DST_ALPHA,[Du]:i.ONE_MINUS_SRC_COLOR,[ac]:i.ONE_MINUS_SRC_ALPHA,[Ou]:i.ONE_MINUS_DST_COLOR,[Fu]:i.ONE_MINUS_DST_ALPHA,[zu]:i.CONSTANT_COLOR,[Vu]:i.ONE_MINUS_CONSTANT_COLOR,[Hu]:i.CONSTANT_ALPHA,[Gu]:i.ONE_MINUS_CONSTANT_ALPHA};function Qe(H,Se,J,ve,Ce,de,Be,Ue,bt,xt){if(H===Mn){g===!0&&(Me(i.BLEND),g=!1);return}if(g===!1&&(ae(i.BLEND),g=!0),H!==wu){if(H!==p||xt!==O){if((w!==zi||A!==zi)&&(i.blendEquation(i.FUNC_ADD),w=zi,A=zi),xt)switch(H){case Cs:i.blendFuncSeparate(i.ONE,i.ONE_MINUS_SRC_ALPHA,i.ONE,i.ONE_MINUS_SRC_ALPHA);break;case Bi:i.blendFunc(i.ONE,i.ONE);break;case ic:i.blendFuncSeparate(i.ZERO,i.ONE_MINUS_SRC_COLOR,i.ZERO,i.ONE);break;case sc:i.blendFuncSeparate(i.DST_COLOR,i.ONE_MINUS_SRC_ALPHA,i.ZERO,i.ONE);break;default:Xe("WebGLState: Invalid blending: ",H);break}else switch(H){case Cs:i.blendFuncSeparate(i.SRC_ALPHA,i.ONE_MINUS_SRC_ALPHA,i.ONE,i.ONE_MINUS_SRC_ALPHA);break;case Bi:i.blendFuncSeparate(i.SRC_ALPHA,i.ONE,i.ONE,i.ONE);break;case ic:Xe("WebGLState: SubtractiveBlending requires material.premultipliedAlpha = true");break;case sc:Xe("WebGLState: MultiplyBlending requires material.premultipliedAlpha = true");break;default:Xe("WebGLState: Invalid blending: ",H);break}I=null,y=null,E=null,D=null,v.set(0,0,0),C=0,p=H,O=xt}return}Ce=Ce||Se,de=de||J,Be=Be||ve,(Se!==w||Ce!==A)&&(i.blendEquationSeparate(je[Se],je[Ce]),w=Se,A=Ce),(J!==I||ve!==y||de!==E||Be!==D)&&(i.blendFuncSeparate(Ze[J],Ze[ve],Ze[de],Ze[Be]),I=J,y=ve,E=de,D=Be),(Ue.equals(v)===!1||bt!==C)&&(i.blendColor(Ue.r,Ue.g,Ue.b,bt),v.copy(Ue),C=bt),p=H,O=!1}function ht(H,Se){H.side===Wn?Me(i.CULL_FACE):ae(i.CULL_FACE);let J=H.side===Zt;Se&&(J=!J),Je(J),H.blending===Cs&&H.transparent===!1?Qe(Mn):Qe(H.blending,H.blendEquation,H.blendSrc,H.blendDst,H.blendEquationAlpha,H.blendSrcAlpha,H.blendDstAlpha,H.blendColor,H.blendAlpha,H.premultipliedAlpha),a.setFunc(H.depthFunc),a.setTest(H.depthTest),a.setMask(H.depthWrite),r.setMask(H.colorWrite);let ve=H.stencilWrite;o.setTest(ve),ve&&(o.setMask(H.stencilWriteMask),o.setFunc(H.stencilFunc,H.stencilRef,H.stencilFuncMask),o.setOp(H.stencilFail,H.stencilZFail,H.stencilZPass)),Lt(H.polygonOffset,H.polygonOffsetFactor,H.polygonOffsetUnits),H.alphaToCoverage===!0?ae(i.SAMPLE_ALPHA_TO_COVERAGE):Me(i.SAMPLE_ALPHA_TO_COVERAGE)}function Je(H){V!==H&&(H?i.frontFace(i.CW):i.frontFace(i.CCW),V=H)}function ft(H){H!==Su?(ae(i.CULL_FACE),H!==q&&(H===nc?i.cullFace(i.BACK):H===Tu?i.cullFace(i.FRONT):i.cullFace(i.FRONT_AND_BACK))):Me(i.CULL_FACE),q=H}function Et(H){H!==j&&(re&&i.lineWidth(H),j=H)}function Lt(H,Se,J){H?(ae(i.POLYGON_OFFSET_FILL),(z!==Se||Y!==J)&&(z=Se,Y=J,a.getReversed()&&(Se=-Se),i.polygonOffset(Se,J))):Me(i.POLYGON_OFFSET_FILL)}function lt(H){H?ae(i.SCISSOR_TEST):Me(i.SCISSOR_TEST)}function tt(H){H===void 0&&(H=i.TEXTURE0+te-1),le!==H&&(i.activeTexture(H),le=H)}function W(H,Se,J){J===void 0&&(le===null?J=i.TEXTURE0+te-1:J=le);let ve=se[J];ve===void 0&&(ve={type:void 0,texture:void 0},se[J]=ve),(ve.type!==H||ve.texture!==Se)&&(le!==J&&(i.activeTexture(J),le=J),i.bindTexture(H,Se||ee[H]),ve.type=H,ve.texture=Se)}function gt(){let H=se[le];H!==void 0&&H.type!==void 0&&(i.bindTexture(H.type,null),H.type=void 0,H.texture=void 0)}function et(){try{i.compressedTexImage2D(...arguments)}catch(H){Xe("WebGLState:",H)}}function L(){try{i.compressedTexImage3D(...arguments)}catch(H){Xe("WebGLState:",H)}}function x(){try{i.texSubImage2D(...arguments)}catch(H){Xe("WebGLState:",H)}}function X(){try{i.texSubImage3D(...arguments)}catch(H){Xe("WebGLState:",H)}}function K(){try{i.compressedTexSubImage2D(...arguments)}catch(H){Xe("WebGLState:",H)}}function oe(){try{i.compressedTexSubImage3D(...arguments)}catch(H){Xe("WebGLState:",H)}}function be(){try{i.texStorage2D(...arguments)}catch(H){Xe("WebGLState:",H)}}function Ae(){try{i.texStorage3D(...arguments)}catch(H){Xe("WebGLState:",H)}}function F(){try{i.texImage2D(...arguments)}catch(H){Xe("WebGLState:",H)}}function $(){try{i.texImage3D(...arguments)}catch(H){Xe("WebGLState:",H)}}function ie(H){return f[H]!==void 0?f[H]:i.getParameter(H)}function me(H,Se){f[H]!==Se&&(i.pixelStorei(H,Se),f[H]=Se)}function ce(H){it.equals(H)===!1&&(i.scissor(H.x,H.y,H.z,H.w),it.copy(H))}function fe(H){Ve.equals(H)===!1&&(i.viewport(H.x,H.y,H.z,H.w),Ve.copy(H))}function ye(H,Se){let J=c.get(Se);J===void 0&&(J=new WeakMap,c.set(Se,J));let ve=J.get(H);ve===void 0&&(ve=i.getUniformBlockIndex(Se,H.name),J.set(H,ve))}function Ee(H,Se){let ve=c.get(Se).get(H);l.get(Se)!==ve&&(i.uniformBlockBinding(Se,ve,H.__bindingPointIndex),l.set(Se,ve))}function Fe(){i.disable(i.BLEND),i.disable(i.CULL_FACE),i.disable(i.DEPTH_TEST),i.disable(i.POLYGON_OFFSET_FILL),i.disable(i.SCISSOR_TEST),i.disable(i.STENCIL_TEST),i.disable(i.SAMPLE_ALPHA_TO_COVERAGE),i.blendEquation(i.FUNC_ADD),i.blendFunc(i.ONE,i.ZERO),i.blendFuncSeparate(i.ONE,i.ZERO,i.ONE,i.ZERO),i.blendColor(0,0,0,0),i.colorMask(!0,!0,!0,!0),i.clearColor(0,0,0,0),i.depthMask(!0),i.depthFunc(i.LESS),a.setReversed(!1),i.clearDepth(1),i.stencilMask(4294967295),i.stencilFunc(i.ALWAYS,0,4294967295),i.stencilOp(i.KEEP,i.KEEP,i.KEEP),i.clearStencil(0),i.cullFace(i.BACK),i.frontFace(i.CCW),i.polygonOffset(0,0),i.activeTexture(i.TEXTURE0),i.bindFramebuffer(i.FRAMEBUFFER,null),i.bindFramebuffer(i.DRAW_FRAMEBUFFER,null),i.bindFramebuffer(i.READ_FRAMEBUFFER,null),i.useProgram(null),i.lineWidth(1),i.scissor(0,0,i.canvas.width,i.canvas.height),i.viewport(0,0,i.canvas.width,i.canvas.height),i.pixelStorei(i.PACK_ALIGNMENT,4),i.pixelStorei(i.UNPACK_ALIGNMENT,4),i.pixelStorei(i.UNPACK_FLIP_Y_WEBGL,!1),i.pixelStorei(i.UNPACK_PREMULTIPLY_ALPHA_WEBGL,!1),i.pixelStorei(i.UNPACK_COLORSPACE_CONVERSION_WEBGL,i.BROWSER_DEFAULT_WEBGL),i.pixelStorei(i.PACK_ROW_LENGTH,0),i.pixelStorei(i.PACK_SKIP_PIXELS,0),i.pixelStorei(i.PACK_SKIP_ROWS,0),i.pixelStorei(i.UNPACK_ROW_LENGTH,0),i.pixelStorei(i.UNPACK_IMAGE_HEIGHT,0),i.pixelStorei(i.UNPACK_SKIP_PIXELS,0),i.pixelStorei(i.UNPACK_SKIP_ROWS,0),i.pixelStorei(i.UNPACK_SKIP_IMAGES,0),h={},f={},le=null,se={},u={},d=new WeakMap,_=[],S=null,g=!1,p=null,w=null,I=null,y=null,A=null,E=null,D=null,v=new qe(0,0,0),C=0,O=!1,V=null,q=null,j=null,z=null,Y=null,it.set(0,0,i.canvas.width,i.canvas.height),Ve.set(0,0,i.canvas.width,i.canvas.height),r.reset(),a.reset(),o.reset()}return{buffers:{color:r,depth:a,stencil:o},enable:ae,disable:Me,bindFramebuffer:Pe,drawBuffers:we,useProgram:Ge,setBlending:Qe,setMaterial:ht,setFlipSided:Je,setCullFace:ft,setLineWidth:Et,setPolygonOffset:Lt,setScissorTest:lt,activeTexture:tt,bindTexture:W,unbindTexture:gt,compressedTexImage2D:et,compressedTexImage3D:L,texImage2D:F,texImage3D:$,pixelStorei:me,getParameter:ie,updateUBOMapping:ye,uniformBlockBinding:Ee,texStorage2D:be,texStorage3D:Ae,texSubImage2D:x,texSubImage3D:X,compressedTexSubImage2D:K,compressedTexSubImage3D:oe,scissor:ce,viewport:fe,reset:Fe}}function W0(i,e,t,n,s,r,a){let o=e.has("WEBGL_multisampled_render_to_texture")?e.get("WEBGL_multisampled_render_to_texture"):null,l=typeof navigator>"u"?!1:/OculusBrowser/g.test(navigator.userAgent),c=new De,h=new WeakMap,f=new Set,u,d=new WeakMap,_=!1;try{_=typeof OffscreenCanvas<"u"&&new OffscreenCanvas(1,1).getContext("2d")!==null}catch{}function S(L,x){return _?new OffscreenCanvas(L,x):ir("canvas")}function g(L,x,X){let K=1,oe=et(L);if((oe.width>X||oe.height>X)&&(K=X/Math.max(oe.width,oe.height)),K<1)if(typeof HTMLImageElement<"u"&&L instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&L instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&L instanceof ImageBitmap||typeof VideoFrame<"u"&&L instanceof VideoFrame){let be=Math.floor(K*oe.width),Ae=Math.floor(K*oe.height);u===void 0&&(u=S(be,Ae));let F=x?S(be,Ae):u;return F.width=be,F.height=Ae,F.getContext("2d").drawImage(L,0,0,be,Ae),$e("WebGLRenderer: Texture has been resized from ("+oe.width+"x"+oe.height+") to ("+be+"x"+Ae+")."),F}else return"data"in L&&$e("WebGLRenderer: Image in DataTexture is too big ("+oe.width+"x"+oe.height+")."),L;return L}function p(L){return L.generateMipmaps}function w(L){i.generateMipmap(L)}function I(L){return L.isWebGLCubeRenderTarget?i.TEXTURE_CUBE_MAP:L.isWebGL3DRenderTarget?i.TEXTURE_3D:L.isWebGLArrayRenderTarget||L.isCompressedArrayTexture?i.TEXTURE_2D_ARRAY:i.TEXTURE_2D}function y(L,x,X,K,oe,be=!1){if(L!==null){if(i[L]!==void 0)return i[L];$e("WebGLRenderer: Attempt to use non-existing WebGL internal format '"+L+"'")}let Ae;K&&(Ae=e.get("EXT_texture_norm16"),Ae||$e("WebGLRenderer: Unable to use normalized textures without EXT_texture_norm16 extension"));let F=x;if(x===i.RED&&(X===i.FLOAT&&(F=i.R32F),X===i.HALF_FLOAT&&(F=i.R16F),X===i.UNSIGNED_BYTE&&(F=i.R8),X===i.UNSIGNED_SHORT&&Ae&&(F=Ae.R16_EXT),X===i.SHORT&&Ae&&(F=Ae.R16_SNORM_EXT)),x===i.RED_INTEGER&&(X===i.UNSIGNED_BYTE&&(F=i.R8UI),X===i.UNSIGNED_SHORT&&(F=i.R16UI),X===i.UNSIGNED_INT&&(F=i.R32UI),X===i.BYTE&&(F=i.R8I),X===i.SHORT&&(F=i.R16I),X===i.INT&&(F=i.R32I)),x===i.RG&&(X===i.FLOAT&&(F=i.RG32F),X===i.HALF_FLOAT&&(F=i.RG16F),X===i.UNSIGNED_BYTE&&(F=i.RG8),X===i.UNSIGNED_SHORT&&Ae&&(F=Ae.RG16_EXT),X===i.SHORT&&Ae&&(F=Ae.RG16_SNORM_EXT)),x===i.RG_INTEGER&&(X===i.UNSIGNED_BYTE&&(F=i.RG8UI),X===i.UNSIGNED_SHORT&&(F=i.RG16UI),X===i.UNSIGNED_INT&&(F=i.RG32UI),X===i.BYTE&&(F=i.RG8I),X===i.SHORT&&(F=i.RG16I),X===i.INT&&(F=i.RG32I)),x===i.RGB_INTEGER&&(X===i.UNSIGNED_BYTE&&(F=i.RGB8UI),X===i.UNSIGNED_SHORT&&(F=i.RGB16UI),X===i.UNSIGNED_INT&&(F=i.RGB32UI),X===i.BYTE&&(F=i.RGB8I),X===i.SHORT&&(F=i.RGB16I),X===i.INT&&(F=i.RGB32I)),x===i.RGBA_INTEGER&&(X===i.UNSIGNED_BYTE&&(F=i.RGBA8UI),X===i.UNSIGNED_SHORT&&(F=i.RGBA16UI),X===i.UNSIGNED_INT&&(F=i.RGBA32UI),X===i.BYTE&&(F=i.RGBA8I),X===i.SHORT&&(F=i.RGBA16I),X===i.INT&&(F=i.RGBA32I)),x===i.RGB&&(X===i.UNSIGNED_SHORT&&Ae&&(F=Ae.RGB16_EXT),X===i.SHORT&&Ae&&(F=Ae.RGB16_SNORM_EXT),X===i.UNSIGNED_INT_5_9_9_9_REV&&(F=i.RGB9_E5),X===i.UNSIGNED_INT_10F_11F_11F_REV&&(F=i.R11F_G11F_B10F)),x===i.RGBA){let $=be?nr:at.getTransfer(oe);X===i.FLOAT&&(F=i.RGBA32F),X===i.HALF_FLOAT&&(F=i.RGBA16F),X===i.UNSIGNED_BYTE&&(F=$===yt?i.SRGB8_ALPHA8:i.RGBA8),X===i.UNSIGNED_SHORT&&Ae&&(F=Ae.RGBA16_EXT),X===i.SHORT&&Ae&&(F=Ae.RGBA16_SNORM_EXT),X===i.UNSIGNED_SHORT_4_4_4_4&&(F=i.RGBA4),X===i.UNSIGNED_SHORT_5_5_5_1&&(F=i.RGB5_A1)}return(F===i.R16F||F===i.R32F||F===i.RG16F||F===i.RG32F||F===i.RGBA16F||F===i.RGBA32F)&&e.get("EXT_color_buffer_float"),F}function A(L,x){let X;return L?x===null||x===Un||x===Is?X=i.DEPTH24_STENCIL8:x===Sn?X=i.DEPTH32F_STENCIL8:x===Rs&&(X=i.DEPTH24_STENCIL8,$e("DepthTexture: 16 bit depth attachment is not supported with stencil. Using 24-bit attachment.")):x===null||x===Un||x===Is?X=i.DEPTH_COMPONENT24:x===Sn?X=i.DEPTH_COMPONENT32F:x===Rs&&(X=i.DEPTH_COMPONENT16),X}function E(L,x){return p(L)===!0||L.isFramebufferTexture&&L.minFilter!==Gt&&L.minFilter!==Yt?Math.log2(Math.max(x.width,x.height))+1:L.mipmaps!==void 0&&L.mipmaps.length>0?L.mipmaps.length:L.isCompressedTexture&&Array.isArray(L.image)?x.mipmaps.length:1}function D(L){let x=L.target;x.removeEventListener("dispose",D),C(x),x.isVideoTexture&&h.delete(x),x.isHTMLTexture&&f.delete(x)}function v(L){let x=L.target;x.removeEventListener("dispose",v),V(x)}function C(L){let x=n.get(L);if(x.__webglInit===void 0)return;let X=L.source,K=d.get(X);if(K){let oe=K[x.__cacheKey];oe.usedTimes--,oe.usedTimes===0&&O(L),Object.keys(K).length===0&&d.delete(X)}n.remove(L)}function O(L){let x=n.get(L);i.deleteTexture(x.__webglTexture);let X=L.source,K=d.get(X);delete K[x.__cacheKey],a.memory.textures--}function V(L){let x=n.get(L);if(L.depthTexture&&(L.depthTexture.dispose(),n.remove(L.depthTexture)),L.isWebGLCubeRenderTarget)for(let K=0;K<6;K++){if(Array.isArray(x.__webglFramebuffer[K]))for(let oe=0;oe<x.__webglFramebuffer[K].length;oe++)i.deleteFramebuffer(x.__webglFramebuffer[K][oe]);else i.deleteFramebuffer(x.__webglFramebuffer[K]);x.__webglDepthbuffer&&i.deleteRenderbuffer(x.__webglDepthbuffer[K])}else{if(Array.isArray(x.__webglFramebuffer))for(let K=0;K<x.__webglFramebuffer.length;K++)i.deleteFramebuffer(x.__webglFramebuffer[K]);else i.deleteFramebuffer(x.__webglFramebuffer);if(x.__webglDepthbuffer&&i.deleteRenderbuffer(x.__webglDepthbuffer),x.__webglMultisampledFramebuffer&&i.deleteFramebuffer(x.__webglMultisampledFramebuffer),x.__webglColorRenderbuffer)for(let K=0;K<x.__webglColorRenderbuffer.length;K++)x.__webglColorRenderbuffer[K]&&i.deleteRenderbuffer(x.__webglColorRenderbuffer[K]);x.__webglDepthRenderbuffer&&i.deleteRenderbuffer(x.__webglDepthRenderbuffer)}let X=L.textures;for(let K=0,oe=X.length;K<oe;K++){let be=n.get(X[K]);be.__webglTexture&&(i.deleteTexture(be.__webglTexture),a.memory.textures--),n.remove(X[K])}n.remove(L)}let q=0;function j(){q=0}function z(){return q}function Y(L){q=L}function te(){let L=q;return L>=s.maxTextures&&$e("WebGLTextures: Trying to use "+(L+1)+" texture units while this GPU supports only "+s.maxTextures),q+=1,L}function re(L){let x=[];return x.push(L.wrapS),x.push(L.wrapT),x.push(L.wrapR||0),x.push(L.magFilter),x.push(L.minFilter),x.push(L.anisotropy),x.push(L.internalFormat),x.push(L.format),x.push(L.type),x.push(L.generateMipmaps),x.push(L.premultiplyAlpha),x.push(L.flipY),x.push(L.unpackAlignment),x.push(L.colorSpace),x.join()}function Z(L,x){let X=n.get(L);if(L.isVideoTexture&&W(L),L.isRenderTargetTexture===!1&&L.isExternalTexture!==!0&&L.version>0&&X.__version!==L.version){let K=L.image;if(K===null)$e("WebGLRenderer: Texture marked for update but no image data found.");else if(K.complete===!1)$e("WebGLRenderer: Texture marked for update but image is incomplete");else{Me(X,L,x);return}}else L.isExternalTexture&&(X.__webglTexture=L.sourceTexture?L.sourceTexture:null);t.bindTexture(i.TEXTURE_2D,X.__webglTexture,i.TEXTURE0+x)}function Q(L,x){let X=n.get(L);if(L.isRenderTargetTexture===!1&&L.version>0&&X.__version!==L.version){Me(X,L,x);return}else L.isExternalTexture&&(X.__webglTexture=L.sourceTexture?L.sourceTexture:null);t.bindTexture(i.TEXTURE_2D_ARRAY,X.__webglTexture,i.TEXTURE0+x)}function le(L,x){let X=n.get(L);if(L.isRenderTargetTexture===!1&&L.version>0&&X.__version!==L.version){Me(X,L,x);return}t.bindTexture(i.TEXTURE_3D,X.__webglTexture,i.TEXTURE0+x)}function se(L,x){let X=n.get(L);if(L.isCubeDepthTexture!==!0&&L.version>0&&X.__version!==L.version){Pe(X,L,x);return}t.bindTexture(i.TEXTURE_CUBE_MAP,X.__webglTexture,i.TEXTURE0+x)}let Oe={[Ua]:i.REPEAT,[On]:i.CLAMP_TO_EDGE,[Fa]:i.MIRRORED_REPEAT},Ie={[Gt]:i.NEAREST,[qu]:i.NEAREST_MIPMAP_NEAREST,[Ur]:i.NEAREST_MIPMAP_LINEAR,[Yt]:i.LINEAR,[mo]:i.LINEAR_MIPMAP_NEAREST,[Mi]:i.LINEAR_MIPMAP_LINEAR},it={[ju]:i.NEVER,[th]:i.ALWAYS,[Ju]:i.LESS,[Qo]:i.LEQUAL,[Ku]:i.EQUAL,[el]:i.GEQUAL,[Qu]:i.GREATER,[eh]:i.NOTEQUAL};function Ve(L,x){if(x.type===Sn&&e.has("OES_texture_float_linear")===!1&&(x.magFilter===Yt||x.magFilter===mo||x.magFilter===Ur||x.magFilter===Mi||x.minFilter===Yt||x.minFilter===mo||x.minFilter===Ur||x.minFilter===Mi)&&$e("WebGLRenderer: Unable to use linear filtering with floating point textures. OES_texture_float_linear not supported on this device."),i.texParameteri(L,i.TEXTURE_WRAP_S,Oe[x.wrapS]),i.texParameteri(L,i.TEXTURE_WRAP_T,Oe[x.wrapT]),(L===i.TEXTURE_3D||L===i.TEXTURE_2D_ARRAY)&&i.texParameteri(L,i.TEXTURE_WRAP_R,Oe[x.wrapR]),i.texParameteri(L,i.TEXTURE_MAG_FILTER,Ie[x.magFilter]),i.texParameteri(L,i.TEXTURE_MIN_FILTER,Ie[x.minFilter]),x.compareFunction&&(i.texParameteri(L,i.TEXTURE_COMPARE_MODE,i.COMPARE_REF_TO_TEXTURE),i.texParameteri(L,i.TEXTURE_COMPARE_FUNC,it[x.compareFunction])),e.has("EXT_texture_filter_anisotropic")===!0){if(x.magFilter===Gt||x.minFilter!==Ur&&x.minFilter!==Mi||x.type===Sn&&e.has("OES_texture_float_linear")===!1)return;if(x.anisotropy>1||n.get(x).__currentAnisotropy){let X=e.get("EXT_texture_filter_anisotropic");i.texParameterf(L,X.TEXTURE_MAX_ANISOTROPY_EXT,Math.min(x.anisotropy,s.getMaxAnisotropy())),n.get(x).__currentAnisotropy=x.anisotropy}}}function He(L,x){let X=!1;L.__webglInit===void 0&&(L.__webglInit=!0,x.addEventListener("dispose",D));let K=x.source,oe=d.get(K);oe===void 0&&(oe={},d.set(K,oe));let be=re(x);if(be!==L.__cacheKey){oe[be]===void 0&&(oe[be]={texture:i.createTexture(),usedTimes:0},a.memory.textures++,X=!0),oe[be].usedTimes++;let Ae=oe[L.__cacheKey];Ae!==void 0&&(oe[L.__cacheKey].usedTimes--,Ae.usedTimes===0&&O(x)),L.__cacheKey=be,L.__webglTexture=oe[be].texture}return X}function ee(L,x,X){return Math.floor(Math.floor(L/X)/x)}function ae(L,x,X,K){let be=L.updateRanges;if(be.length===0)t.texSubImage2D(i.TEXTURE_2D,0,0,0,x.width,x.height,X,K,x.data);else{be.sort((me,ce)=>me.start-ce.start);let Ae=0;for(let me=1;me<be.length;me++){let ce=be[Ae],fe=be[me],ye=ce.start+ce.count,Ee=ee(fe.start,x.width,4),Fe=ee(ce.start,x.width,4);fe.start<=ye+1&&Ee===Fe&&ee(fe.start+fe.count-1,x.width,4)===Ee?ce.count=Math.max(ce.count,fe.start+fe.count-ce.start):(++Ae,be[Ae]=fe)}be.length=Ae+1;let F=t.getParameter(i.UNPACK_ROW_LENGTH),$=t.getParameter(i.UNPACK_SKIP_PIXELS),ie=t.getParameter(i.UNPACK_SKIP_ROWS);t.pixelStorei(i.UNPACK_ROW_LENGTH,x.width);for(let me=0,ce=be.length;me<ce;me++){let fe=be[me],ye=Math.floor(fe.start/4),Ee=Math.ceil(fe.count/4),Fe=ye%x.width,H=Math.floor(ye/x.width),Se=Ee,J=1;t.pixelStorei(i.UNPACK_SKIP_PIXELS,Fe),t.pixelStorei(i.UNPACK_SKIP_ROWS,H),t.texSubImage2D(i.TEXTURE_2D,0,Fe,H,Se,J,X,K,x.data)}L.clearUpdateRanges(),t.pixelStorei(i.UNPACK_ROW_LENGTH,F),t.pixelStorei(i.UNPACK_SKIP_PIXELS,$),t.pixelStorei(i.UNPACK_SKIP_ROWS,ie)}}function Me(L,x,X){let K=i.TEXTURE_2D;(x.isDataArrayTexture||x.isCompressedArrayTexture)&&(K=i.TEXTURE_2D_ARRAY),x.isData3DTexture&&(K=i.TEXTURE_3D);let oe=He(L,x),be=x.source;t.bindTexture(K,L.__webglTexture,i.TEXTURE0+X);let Ae=n.get(be);if(be.version!==Ae.__version||oe===!0){if(t.activeTexture(i.TEXTURE0+X),(typeof ImageBitmap<"u"&&x.image instanceof ImageBitmap)===!1){let J=at.getPrimaries(at.workingColorSpace),ve=x.colorSpace===ti?null:at.getPrimaries(x.colorSpace),Ce=x.colorSpace===ti||J===ve?i.NONE:i.BROWSER_DEFAULT_WEBGL;t.pixelStorei(i.UNPACK_FLIP_Y_WEBGL,x.flipY),t.pixelStorei(i.UNPACK_PREMULTIPLY_ALPHA_WEBGL,x.premultiplyAlpha),t.pixelStorei(i.UNPACK_COLORSPACE_CONVERSION_WEBGL,Ce)}t.pixelStorei(i.UNPACK_ALIGNMENT,x.unpackAlignment);let $=g(x.image,!1,s.maxTextureSize);$=gt(x,$);let ie=r.convert(x.format,x.colorSpace),me=r.convert(x.type),ce=y(x.internalFormat,ie,me,x.normalized,x.colorSpace,x.isVideoTexture);Ve(K,x);let fe,ye=x.mipmaps,Ee=x.isVideoTexture!==!0,Fe=Ae.__version===void 0||oe===!0,H=be.dataReady,Se=E(x,$);if(x.isDepthTexture)ce=A(x.format===Si,x.type),Fe&&(Ee?t.texStorage2D(i.TEXTURE_2D,1,ce,$.width,$.height):t.texImage2D(i.TEXTURE_2D,0,ce,$.width,$.height,0,ie,me,null));else if(x.isDataTexture)if(ye.length>0){Ee&&Fe&&t.texStorage2D(i.TEXTURE_2D,Se,ce,ye[0].width,ye[0].height);for(let J=0,ve=ye.length;J<ve;J++)fe=ye[J],Ee?H&&t.texSubImage2D(i.TEXTURE_2D,J,0,0,fe.width,fe.height,ie,me,fe.data):t.texImage2D(i.TEXTURE_2D,J,ce,fe.width,fe.height,0,ie,me,fe.data);x.generateMipmaps=!1}else Ee?(Fe&&t.texStorage2D(i.TEXTURE_2D,Se,ce,$.width,$.height),H&&ae(x,$,ie,me)):t.texImage2D(i.TEXTURE_2D,0,ce,$.width,$.height,0,ie,me,$.data);else if(x.isCompressedTexture)if(x.isCompressedArrayTexture){Ee&&Fe&&t.texStorage3D(i.TEXTURE_2D_ARRAY,Se,ce,ye[0].width,ye[0].height,$.depth);for(let J=0,ve=ye.length;J<ve;J++)if(fe=ye[J],x.format!==Tn)if(ie!==null)if(Ee){if(H)if(x.layerUpdates.size>0){let Ce=Mc(fe.width,fe.height,x.format,x.type);for(let de of x.layerUpdates){let Be=fe.data.subarray(de*Ce/fe.data.BYTES_PER_ELEMENT,(de+1)*Ce/fe.data.BYTES_PER_ELEMENT);t.compressedTexSubImage3D(i.TEXTURE_2D_ARRAY,J,0,0,de,fe.width,fe.height,1,ie,Be)}}else t.compressedTexSubImage3D(i.TEXTURE_2D_ARRAY,J,0,0,0,fe.width,fe.height,$.depth,ie,fe.data)}else t.compressedTexImage3D(i.TEXTURE_2D_ARRAY,J,ce,fe.width,fe.height,$.depth,0,fe.data,0,0);else $e("WebGLRenderer: Attempt to load unsupported compressed texture format in .uploadTexture()");else Ee?H&&t.texSubImage3D(i.TEXTURE_2D_ARRAY,J,0,0,0,fe.width,fe.height,$.depth,ie,me,fe.data):t.texImage3D(i.TEXTURE_2D_ARRAY,J,ce,fe.width,fe.height,$.depth,0,ie,me,fe.data);x.layerUpdates.size>0&&x.clearLayerUpdates()}else{Ee&&Fe&&t.texStorage2D(i.TEXTURE_2D,Se,ce,ye[0].width,ye[0].height);for(let J=0,ve=ye.length;J<ve;J++)fe=ye[J],x.format!==Tn?ie!==null?Ee?H&&t.compressedTexSubImage2D(i.TEXTURE_2D,J,0,0,fe.width,fe.height,ie,fe.data):t.compressedTexImage2D(i.TEXTURE_2D,J,ce,fe.width,fe.height,0,fe.data):$e("WebGLRenderer: Attempt to load unsupported compressed texture format in .uploadTexture()"):Ee?H&&t.texSubImage2D(i.TEXTURE_2D,J,0,0,fe.width,fe.height,ie,me,fe.data):t.texImage2D(i.TEXTURE_2D,J,ce,fe.width,fe.height,0,ie,me,fe.data)}else if(x.isDataArrayTexture)if(Ee){if(Fe&&t.texStorage3D(i.TEXTURE_2D_ARRAY,Se,ce,$.width,$.height,$.depth),H)if(x.layerUpdates.size>0){let J=Mc($.width,$.height,x.format,x.type);for(let ve of x.layerUpdates){let Ce=$.data.subarray(ve*J/$.data.BYTES_PER_ELEMENT,(ve+1)*J/$.data.BYTES_PER_ELEMENT);t.texSubImage3D(i.TEXTURE_2D_ARRAY,0,0,0,ve,$.width,$.height,1,ie,me,Ce)}x.clearLayerUpdates()}else t.texSubImage3D(i.TEXTURE_2D_ARRAY,0,0,0,0,$.width,$.height,$.depth,ie,me,$.data)}else t.texImage3D(i.TEXTURE_2D_ARRAY,0,ce,$.width,$.height,$.depth,0,ie,me,$.data);else if(x.isData3DTexture)Ee?(Fe&&t.texStorage3D(i.TEXTURE_3D,Se,ce,$.width,$.height,$.depth),H&&t.texSubImage3D(i.TEXTURE_3D,0,0,0,0,$.width,$.height,$.depth,ie,me,$.data)):t.texImage3D(i.TEXTURE_3D,0,ce,$.width,$.height,$.depth,0,ie,me,$.data);else if(x.isFramebufferTexture){if(Fe)if(Ee)t.texStorage2D(i.TEXTURE_2D,Se,ce,$.width,$.height);else{let J=$.width,ve=$.height;for(let Ce=0;Ce<Se;Ce++)t.texImage2D(i.TEXTURE_2D,Ce,ce,J,ve,0,ie,me,null),J>>=1,ve>>=1}}else if(x.isHTMLTexture){if("texElementImage2D"in i){let J=i.canvas;if(J.hasAttribute("layoutsubtree")||J.setAttribute("layoutsubtree","true"),$.parentNode!==J){J.appendChild($),f.add(x),J.onpaint=ve=>{let Ce=ve.changedElements;for(let de of f)Ce.includes(de.image)&&(de.needsUpdate=!0)},J.requestPaint();return}if(i.texElementImage2D.length===3)i.texElementImage2D(i.TEXTURE_2D,i.RGBA8,$);else{let Ce=i.RGBA,de=i.RGBA,Be=i.UNSIGNED_BYTE;i.texElementImage2D(i.TEXTURE_2D,0,Ce,de,Be,$)}i.texParameteri(i.TEXTURE_2D,i.TEXTURE_MIN_FILTER,i.LINEAR),i.texParameteri(i.TEXTURE_2D,i.TEXTURE_WRAP_S,i.CLAMP_TO_EDGE),i.texParameteri(i.TEXTURE_2D,i.TEXTURE_WRAP_T,i.CLAMP_TO_EDGE)}}else if(ye.length>0){if(Ee&&Fe){let J=et(ye[0]);t.texStorage2D(i.TEXTURE_2D,Se,ce,J.width,J.height)}for(let J=0,ve=ye.length;J<ve;J++)fe=ye[J],Ee?H&&t.texSubImage2D(i.TEXTURE_2D,J,0,0,ie,me,fe):t.texImage2D(i.TEXTURE_2D,J,ce,ie,me,fe);x.generateMipmaps=!1}else if(Ee){if(Fe){let J=et($);t.texStorage2D(i.TEXTURE_2D,Se,ce,J.width,J.height)}H&&t.texSubImage2D(i.TEXTURE_2D,0,0,0,ie,me,$)}else t.texImage2D(i.TEXTURE_2D,0,ce,ie,me,$);p(x)&&w(K),Ae.__version=be.version,x.onUpdate&&x.onUpdate(x)}L.__version=x.version}function Pe(L,x,X){if(x.image.length!==6)return;let K=He(L,x),oe=x.source;t.bindTexture(i.TEXTURE_CUBE_MAP,L.__webglTexture,i.TEXTURE0+X);let be=n.get(oe);if(oe.version!==be.__version||K===!0){t.activeTexture(i.TEXTURE0+X);let Ae=at.getPrimaries(at.workingColorSpace),F=x.colorSpace===ti?null:at.getPrimaries(x.colorSpace),$=x.colorSpace===ti||Ae===F?i.NONE:i.BROWSER_DEFAULT_WEBGL;t.pixelStorei(i.UNPACK_FLIP_Y_WEBGL,x.flipY),t.pixelStorei(i.UNPACK_PREMULTIPLY_ALPHA_WEBGL,x.premultiplyAlpha),t.pixelStorei(i.UNPACK_ALIGNMENT,x.unpackAlignment),t.pixelStorei(i.UNPACK_COLORSPACE_CONVERSION_WEBGL,$);let ie=x.isCompressedTexture||x.image[0].isCompressedTexture,me=x.image[0]&&x.image[0].isDataTexture,ce=[];for(let de=0;de<6;de++)!ie&&!me?ce[de]=g(x.image[de],!0,s.maxCubemapSize):ce[de]=me?x.image[de].image:x.image[de],ce[de]=gt(x,ce[de]);let fe=ce[0],ye=r.convert(x.format,x.colorSpace),Ee=r.convert(x.type),Fe=y(x.internalFormat,ye,Ee,x.normalized,x.colorSpace),H=x.isVideoTexture!==!0,Se=be.__version===void 0||K===!0,J=oe.dataReady,ve=E(x,fe);Ve(i.TEXTURE_CUBE_MAP,x);let Ce;if(ie){H&&Se&&t.texStorage2D(i.TEXTURE_CUBE_MAP,ve,Fe,fe.width,fe.height);for(let de=0;de<6;de++){Ce=ce[de].mipmaps;for(let Be=0;Be<Ce.length;Be++){let Ue=Ce[Be];x.format!==Tn?ye!==null?H?J&&t.compressedTexSubImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+de,Be,0,0,Ue.width,Ue.height,ye,Ue.data):t.compressedTexImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+de,Be,Fe,Ue.width,Ue.height,0,Ue.data):$e("WebGLRenderer: Attempt to load unsupported compressed texture format in .setTextureCube()"):H?J&&t.texSubImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+de,Be,0,0,Ue.width,Ue.height,ye,Ee,Ue.data):t.texImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+de,Be,Fe,Ue.width,Ue.height,0,ye,Ee,Ue.data)}}}else{if(Ce=x.mipmaps,H&&Se){Ce.length>0&&ve++;let de=et(ce[0]);t.texStorage2D(i.TEXTURE_CUBE_MAP,ve,Fe,de.width,de.height)}for(let de=0;de<6;de++)if(me){H?J&&t.texSubImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+de,0,0,0,ce[de].width,ce[de].height,ye,Ee,ce[de].data):t.texImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+de,0,Fe,ce[de].width,ce[de].height,0,ye,Ee,ce[de].data);for(let Be=0;Be<Ce.length;Be++){let bt=Ce[Be].image[de].image;H?J&&t.texSubImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+de,Be+1,0,0,bt.width,bt.height,ye,Ee,bt.data):t.texImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+de,Be+1,Fe,bt.width,bt.height,0,ye,Ee,bt.data)}}else{H?J&&t.texSubImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+de,0,0,0,ye,Ee,ce[de]):t.texImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+de,0,Fe,ye,Ee,ce[de]);for(let Be=0;Be<Ce.length;Be++){let Ue=Ce[Be];H?J&&t.texSubImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+de,Be+1,0,0,ye,Ee,Ue.image[de]):t.texImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+de,Be+1,Fe,ye,Ee,Ue.image[de])}}}p(x)&&w(i.TEXTURE_CUBE_MAP),be.__version=oe.version,x.onUpdate&&x.onUpdate(x)}L.__version=x.version}function we(L,x,X,K,oe,be){let Ae=r.convert(X.format,X.colorSpace),F=r.convert(X.type),$=y(X.internalFormat,Ae,F,X.normalized,X.colorSpace),ie=n.get(x),me=n.get(X);if(me.__renderTarget=x,!ie.__hasExternalTextures){let ce=Math.max(1,x.width>>be),fe=Math.max(1,x.height>>be);oe===i.TEXTURE_3D||oe===i.TEXTURE_2D_ARRAY?t.texImage3D(oe,be,$,ce,fe,x.depth,0,Ae,F,null):t.texImage2D(oe,be,$,ce,fe,0,Ae,F,null)}t.bindFramebuffer(i.FRAMEBUFFER,L),tt(x)?o.framebufferTexture2DMultisampleEXT(i.FRAMEBUFFER,K,oe,me.__webglTexture,0,lt(x)):(oe===i.TEXTURE_2D||oe>=i.TEXTURE_CUBE_MAP_POSITIVE_X&&oe<=i.TEXTURE_CUBE_MAP_NEGATIVE_Z)&&i.framebufferTexture2D(i.FRAMEBUFFER,K,oe,me.__webglTexture,be),t.bindFramebuffer(i.FRAMEBUFFER,null)}function Ge(L,x,X){if(i.bindRenderbuffer(i.RENDERBUFFER,L),x.depthBuffer){let K=x.depthTexture,oe=K&&K.isDepthTexture?K.type:null,be=A(x.stencilBuffer,oe),Ae=x.stencilBuffer?i.DEPTH_STENCIL_ATTACHMENT:i.DEPTH_ATTACHMENT;tt(x)?o.renderbufferStorageMultisampleEXT(i.RENDERBUFFER,lt(x),be,x.width,x.height):X?i.renderbufferStorageMultisample(i.RENDERBUFFER,lt(x),be,x.width,x.height):i.renderbufferStorage(i.RENDERBUFFER,be,x.width,x.height),i.framebufferRenderbuffer(i.FRAMEBUFFER,Ae,i.RENDERBUFFER,L)}else{let K=x.textures;for(let oe=0;oe<K.length;oe++){let be=K[oe],Ae=r.convert(be.format,be.colorSpace),F=r.convert(be.type),$=y(be.internalFormat,Ae,F,be.normalized,be.colorSpace);tt(x)?o.renderbufferStorageMultisampleEXT(i.RENDERBUFFER,lt(x),$,x.width,x.height):X?i.renderbufferStorageMultisample(i.RENDERBUFFER,lt(x),$,x.width,x.height):i.renderbufferStorage(i.RENDERBUFFER,$,x.width,x.height)}}i.bindRenderbuffer(i.RENDERBUFFER,null)}function je(L,x,X){let K=x.isWebGLCubeRenderTarget===!0;if(t.bindFramebuffer(i.FRAMEBUFFER,L),!(x.depthTexture&&x.depthTexture.isDepthTexture))throw new Error("THREE.WebGLTextures: renderTarget.depthTexture must be an instance of THREE.DepthTexture.");let oe=n.get(x.depthTexture);if(oe.__renderTarget=x,(!oe.__webglTexture||x.depthTexture.image.width!==x.width||x.depthTexture.image.height!==x.height)&&(x.depthTexture.image.width=x.width,x.depthTexture.image.height=x.height,x.depthTexture.needsUpdate=!0),K){if(oe.__webglInit===void 0&&(oe.__webglInit=!0,x.depthTexture.addEventListener("dispose",D)),oe.__webglTexture===void 0){oe.__webglTexture=i.createTexture(),t.bindTexture(i.TEXTURE_CUBE_MAP,oe.__webglTexture),Ve(i.TEXTURE_CUBE_MAP,x.depthTexture);let ie=r.convert(x.depthTexture.format),me=r.convert(x.depthTexture.type),ce;x.depthTexture.format===Bn?ce=i.DEPTH_COMPONENT24:x.depthTexture.format===Si&&(ce=i.DEPTH24_STENCIL8);for(let fe=0;fe<6;fe++)i.texImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+fe,0,ce,x.width,x.height,0,ie,me,null)}}else Z(x.depthTexture,0);let be=oe.__webglTexture,Ae=lt(x),F=K?i.TEXTURE_CUBE_MAP_POSITIVE_X+X:i.TEXTURE_2D,$=x.depthTexture.format===Si?i.DEPTH_STENCIL_ATTACHMENT:i.DEPTH_ATTACHMENT;if(x.depthTexture.format===Bn)tt(x)?o.framebufferTexture2DMultisampleEXT(i.FRAMEBUFFER,$,F,be,0,Ae):i.framebufferTexture2D(i.FRAMEBUFFER,$,F,be,0);else if(x.depthTexture.format===Si)tt(x)?o.framebufferTexture2DMultisampleEXT(i.FRAMEBUFFER,$,F,be,0,Ae):i.framebufferTexture2D(i.FRAMEBUFFER,$,F,be,0);else throw new Error("THREE.WebGLTextures: Unknown depthTexture format.")}function Ze(L){let x=n.get(L),X=L.isWebGLCubeRenderTarget===!0;if(x.__boundDepthTexture!==L.depthTexture){let K=L.depthTexture;if(x.__depthDisposeCallback&&x.__depthDisposeCallback(),K){let oe=()=>{delete x.__boundDepthTexture,delete x.__depthDisposeCallback,K.removeEventListener("dispose",oe)};K.addEventListener("dispose",oe),x.__depthDisposeCallback=oe}x.__boundDepthTexture=K}if(L.depthTexture&&!x.__autoAllocateDepthBuffer)if(X)for(let K=0;K<6;K++)je(x.__webglFramebuffer[K],L,K);else{let K=L.texture.mipmaps;K&&K.length>0?je(x.__webglFramebuffer[0],L,0):je(x.__webglFramebuffer,L,0)}else if(X){x.__webglDepthbuffer=[];for(let K=0;K<6;K++)if(t.bindFramebuffer(i.FRAMEBUFFER,x.__webglFramebuffer[K]),x.__webglDepthbuffer[K]===void 0)x.__webglDepthbuffer[K]=i.createRenderbuffer(),Ge(x.__webglDepthbuffer[K],L,!1);else{let oe=L.stencilBuffer?i.DEPTH_STENCIL_ATTACHMENT:i.DEPTH_ATTACHMENT,be=x.__webglDepthbuffer[K];i.bindRenderbuffer(i.RENDERBUFFER,be),i.framebufferRenderbuffer(i.FRAMEBUFFER,oe,i.RENDERBUFFER,be)}}else{let K=L.texture.mipmaps;if(K&&K.length>0?t.bindFramebuffer(i.FRAMEBUFFER,x.__webglFramebuffer[0]):t.bindFramebuffer(i.FRAMEBUFFER,x.__webglFramebuffer),x.__webglDepthbuffer===void 0)x.__webglDepthbuffer=i.createRenderbuffer(),Ge(x.__webglDepthbuffer,L,!1);else{let oe=L.stencilBuffer?i.DEPTH_STENCIL_ATTACHMENT:i.DEPTH_ATTACHMENT,be=x.__webglDepthbuffer;i.bindRenderbuffer(i.RENDERBUFFER,be),i.framebufferRenderbuffer(i.FRAMEBUFFER,oe,i.RENDERBUFFER,be)}}t.bindFramebuffer(i.FRAMEBUFFER,null)}function Qe(L,x,X){let K=n.get(L);x!==void 0&&we(K.__webglFramebuffer,L,L.texture,i.COLOR_ATTACHMENT0,i.TEXTURE_2D,0),X!==void 0&&Ze(L)}function ht(L){let x=L.texture,X=n.get(L),K=n.get(x);L.addEventListener("dispose",v);let oe=L.textures,be=L.isWebGLCubeRenderTarget===!0,Ae=oe.length>1;if(Ae||(K.__webglTexture===void 0&&(K.__webglTexture=i.createTexture()),K.__version=x.version,a.memory.textures++),be){X.__webglFramebuffer=[];for(let F=0;F<6;F++)if(x.mipmaps&&x.mipmaps.length>0){X.__webglFramebuffer[F]=[];for(let $=0;$<x.mipmaps.length;$++)X.__webglFramebuffer[F][$]=i.createFramebuffer()}else X.__webglFramebuffer[F]=i.createFramebuffer()}else{if(x.mipmaps&&x.mipmaps.length>0){X.__webglFramebuffer=[];for(let F=0;F<x.mipmaps.length;F++)X.__webglFramebuffer[F]=i.createFramebuffer()}else X.__webglFramebuffer=i.createFramebuffer();if(Ae)for(let F=0,$=oe.length;F<$;F++){let ie=n.get(oe[F]);ie.__webglTexture===void 0&&(ie.__webglTexture=i.createTexture(),a.memory.textures++)}if(L.samples>0&&tt(L)===!1){X.__webglMultisampledFramebuffer=i.createFramebuffer(),X.__webglColorRenderbuffer=[],t.bindFramebuffer(i.FRAMEBUFFER,X.__webglMultisampledFramebuffer);for(let F=0;F<oe.length;F++){let $=oe[F];X.__webglColorRenderbuffer[F]=i.createRenderbuffer(),i.bindRenderbuffer(i.RENDERBUFFER,X.__webglColorRenderbuffer[F]);let ie=r.convert($.format,$.colorSpace),me=r.convert($.type),ce=y($.internalFormat,ie,me,$.normalized,$.colorSpace,L.isXRRenderTarget===!0),fe=lt(L);i.renderbufferStorageMultisample(i.RENDERBUFFER,fe,ce,L.width,L.height),i.framebufferRenderbuffer(i.FRAMEBUFFER,i.COLOR_ATTACHMENT0+F,i.RENDERBUFFER,X.__webglColorRenderbuffer[F])}i.bindRenderbuffer(i.RENDERBUFFER,null),L.depthBuffer&&(X.__webglDepthRenderbuffer=i.createRenderbuffer(),Ge(X.__webglDepthRenderbuffer,L,!0)),t.bindFramebuffer(i.FRAMEBUFFER,null)}}if(be){t.bindTexture(i.TEXTURE_CUBE_MAP,K.__webglTexture),Ve(i.TEXTURE_CUBE_MAP,x);for(let F=0;F<6;F++)if(x.mipmaps&&x.mipmaps.length>0)for(let $=0;$<x.mipmaps.length;$++)we(X.__webglFramebuffer[F][$],L,x,i.COLOR_ATTACHMENT0,i.TEXTURE_CUBE_MAP_POSITIVE_X+F,$);else we(X.__webglFramebuffer[F],L,x,i.COLOR_ATTACHMENT0,i.TEXTURE_CUBE_MAP_POSITIVE_X+F,0);p(x)&&w(i.TEXTURE_CUBE_MAP),t.unbindTexture()}else if(Ae){for(let F=0,$=oe.length;F<$;F++){let ie=oe[F],me=n.get(ie),ce=i.TEXTURE_2D;(L.isWebGL3DRenderTarget||L.isWebGLArrayRenderTarget)&&(ce=L.isWebGL3DRenderTarget?i.TEXTURE_3D:i.TEXTURE_2D_ARRAY),t.bindTexture(ce,me.__webglTexture),Ve(ce,ie),we(X.__webglFramebuffer,L,ie,i.COLOR_ATTACHMENT0+F,ce,0),p(ie)&&w(ce)}t.unbindTexture()}else{let F=i.TEXTURE_2D;if((L.isWebGL3DRenderTarget||L.isWebGLArrayRenderTarget)&&(F=L.isWebGL3DRenderTarget?i.TEXTURE_3D:i.TEXTURE_2D_ARRAY),t.bindTexture(F,K.__webglTexture),Ve(F,x),x.mipmaps&&x.mipmaps.length>0)for(let $=0;$<x.mipmaps.length;$++)we(X.__webglFramebuffer[$],L,x,i.COLOR_ATTACHMENT0,F,$);else we(X.__webglFramebuffer,L,x,i.COLOR_ATTACHMENT0,F,0);p(x)&&w(F),t.unbindTexture()}L.depthBuffer&&Ze(L)}function Je(L){let x=L.textures;for(let X=0,K=x.length;X<K;X++){let oe=x[X];if(p(oe)){let be=I(L),Ae=n.get(oe).__webglTexture;t.bindTexture(be,Ae),w(be),t.unbindTexture()}}}let ft=[],Et=[];function Lt(L){if(L.samples>0){if(tt(L)===!1){let x=L.textures,X=L.width,K=L.height,oe=i.COLOR_BUFFER_BIT,be=L.stencilBuffer?i.DEPTH_STENCIL_ATTACHMENT:i.DEPTH_ATTACHMENT,Ae=n.get(L),F=x.length>1;if(F)for(let ie=0;ie<x.length;ie++)t.bindFramebuffer(i.FRAMEBUFFER,Ae.__webglMultisampledFramebuffer),i.framebufferRenderbuffer(i.FRAMEBUFFER,i.COLOR_ATTACHMENT0+ie,i.RENDERBUFFER,null),t.bindFramebuffer(i.FRAMEBUFFER,Ae.__webglFramebuffer),i.framebufferTexture2D(i.DRAW_FRAMEBUFFER,i.COLOR_ATTACHMENT0+ie,i.TEXTURE_2D,null,0);t.bindFramebuffer(i.READ_FRAMEBUFFER,Ae.__webglMultisampledFramebuffer);let $=L.texture.mipmaps;$&&$.length>0?t.bindFramebuffer(i.DRAW_FRAMEBUFFER,Ae.__webglFramebuffer[0]):t.bindFramebuffer(i.DRAW_FRAMEBUFFER,Ae.__webglFramebuffer);for(let ie=0;ie<x.length;ie++){if(L.resolveDepthBuffer&&(L.depthBuffer&&(oe|=i.DEPTH_BUFFER_BIT),L.stencilBuffer&&L.resolveStencilBuffer&&(oe|=i.STENCIL_BUFFER_BIT)),F){i.framebufferRenderbuffer(i.READ_FRAMEBUFFER,i.COLOR_ATTACHMENT0,i.RENDERBUFFER,Ae.__webglColorRenderbuffer[ie]);let me=n.get(x[ie]).__webglTexture;i.framebufferTexture2D(i.DRAW_FRAMEBUFFER,i.COLOR_ATTACHMENT0,i.TEXTURE_2D,me,0)}i.blitFramebuffer(0,0,X,K,0,0,X,K,oe,i.NEAREST),l===!0&&(ft.length=0,Et.length=0,ft.push(i.COLOR_ATTACHMENT0+ie),L.depthBuffer&&L.storeMultisampledDepthBuffer===!1&&(ft.push(be),Et.push(be),i.invalidateFramebuffer(i.DRAW_FRAMEBUFFER,Et)),i.invalidateFramebuffer(i.READ_FRAMEBUFFER,ft))}if(t.bindFramebuffer(i.READ_FRAMEBUFFER,null),t.bindFramebuffer(i.DRAW_FRAMEBUFFER,null),F)for(let ie=0;ie<x.length;ie++){t.bindFramebuffer(i.FRAMEBUFFER,Ae.__webglMultisampledFramebuffer),i.framebufferRenderbuffer(i.FRAMEBUFFER,i.COLOR_ATTACHMENT0+ie,i.RENDERBUFFER,Ae.__webglColorRenderbuffer[ie]);let me=n.get(x[ie]).__webglTexture;t.bindFramebuffer(i.FRAMEBUFFER,Ae.__webglFramebuffer),i.framebufferTexture2D(i.DRAW_FRAMEBUFFER,i.COLOR_ATTACHMENT0+ie,i.TEXTURE_2D,me,0)}t.bindFramebuffer(i.DRAW_FRAMEBUFFER,Ae.__webglMultisampledFramebuffer)}else if(L.depthBuffer&&L.storeMultisampledDepthBuffer===!1&&l){let x=L.stencilBuffer?i.DEPTH_STENCIL_ATTACHMENT:i.DEPTH_ATTACHMENT;i.invalidateFramebuffer(i.DRAW_FRAMEBUFFER,[x])}}}function lt(L){return Math.min(s.maxSamples,L.samples)}function tt(L){let x=n.get(L);return L.samples>0&&e.has("WEBGL_multisampled_render_to_texture")===!0&&x.__useRenderToTexture!==!1}function W(L){let x=a.render.frame;h.get(L)!==x&&(h.set(L,x),L.update())}function gt(L,x){let X=L.colorSpace,K=L.format,oe=L.type;return L.isCompressedTexture===!0||L.isVideoTexture===!0||X!==tr&&X!==ti&&(at.getTransfer(X)===yt?(K!==Tn||oe!==un)&&$e("WebGLTextures: sRGB encoded textures have to use RGBAFormat and UnsignedByteType."):Xe("WebGLTextures: Unsupported texture color space:",X)),x}function et(L){return typeof HTMLImageElement<"u"&&L instanceof HTMLImageElement?(c.width=L.naturalWidth||L.width,c.height=L.naturalHeight||L.height):typeof VideoFrame<"u"&&L instanceof VideoFrame?(c.width=L.displayWidth,c.height=L.displayHeight):(c.width=L.width,c.height=L.height),c}this.allocateTextureUnit=te,this.resetTextureUnits=j,this.getTextureUnits=z,this.setTextureUnits=Y,this.setTexture2D=Z,this.setTexture2DArray=Q,this.setTexture3D=le,this.setTextureCube=se,this.rebindTextures=Qe,this.setupRenderTarget=ht,this.updateRenderTargetMipmap=Je,this.updateMultisampleRenderTarget=Lt,this.setupDepthRenderbuffer=Ze,this.setupFrameBufferTexture=we,this.useMultisampledRTT=tt,this.isReversedDepthBuffer=function(){return t.buffers.depth.getReversed()}}function $0(i,e){function t(n,s=ti){let r,a=at.getTransfer(s);if(n===un)return i.UNSIGNED_BYTE;if(n===_o)return i.UNSIGNED_SHORT_4_4_4_4;if(n===xo)return i.UNSIGNED_SHORT_5_5_5_1;if(n===uc)return i.UNSIGNED_INT_5_9_9_9_REV;if(n===hc)return i.UNSIGNED_INT_10F_11F_11F_REV;if(n===lc)return i.BYTE;if(n===cc)return i.SHORT;if(n===Rs)return i.UNSIGNED_SHORT;if(n===go)return i.INT;if(n===Un)return i.UNSIGNED_INT;if(n===Sn)return i.FLOAT;if(n===jt)return i.HALF_FLOAT;if(n===dc)return i.ALPHA;if(n===fc)return i.RGB;if(n===Tn)return i.RGBA;if(n===Bn)return i.DEPTH_COMPONENT;if(n===Si)return i.DEPTH_STENCIL;if(n===vo)return i.RED;if(n===yo)return i.RED_INTEGER;if(n===Ti)return i.RG;if(n===bo)return i.RG_INTEGER;if(n===Mo)return i.RGBA_INTEGER;if(n===Fr||n===kr||n===Or||n===Br)if(a===yt)if(r=e.get("WEBGL_compressed_texture_s3tc_srgb"),r!==null){if(n===Fr)return r.COMPRESSED_SRGB_S3TC_DXT1_EXT;if(n===kr)return r.COMPRESSED_SRGB_ALPHA_S3TC_DXT1_EXT;if(n===Or)return r.COMPRESSED_SRGB_ALPHA_S3TC_DXT3_EXT;if(n===Br)return r.COMPRESSED_SRGB_ALPHA_S3TC_DXT5_EXT}else return null;else if(r=e.get("WEBGL_compressed_texture_s3tc"),r!==null){if(n===Fr)return r.COMPRESSED_RGB_S3TC_DXT1_EXT;if(n===kr)return r.COMPRESSED_RGBA_S3TC_DXT1_EXT;if(n===Or)return r.COMPRESSED_RGBA_S3TC_DXT3_EXT;if(n===Br)return r.COMPRESSED_RGBA_S3TC_DXT5_EXT}else return null;if(n===So||n===To||n===Eo||n===wo)if(r=e.get("WEBGL_compressed_texture_pvrtc"),r!==null){if(n===So)return r.COMPRESSED_RGB_PVRTC_4BPPV1_IMG;if(n===To)return r.COMPRESSED_RGB_PVRTC_2BPPV1_IMG;if(n===Eo)return r.COMPRESSED_RGBA_PVRTC_4BPPV1_IMG;if(n===wo)return r.COMPRESSED_RGBA_PVRTC_2BPPV1_IMG}else return null;if(n===Ao||n===Co||n===Ro||n===Io||n===Po||n===zr||n===Lo)if(r=e.get("WEBGL_compressed_texture_etc"),r!==null){if(n===Ao||n===Co)return a===yt?r.COMPRESSED_SRGB8_ETC2:r.COMPRESSED_RGB8_ETC2;if(n===Ro)return a===yt?r.COMPRESSED_SRGB8_ALPHA8_ETC2_EAC:r.COMPRESSED_RGBA8_ETC2_EAC;if(n===Io)return r.COMPRESSED_R11_EAC;if(n===Po)return r.COMPRESSED_SIGNED_R11_EAC;if(n===zr)return r.COMPRESSED_RG11_EAC;if(n===Lo)return r.COMPRESSED_SIGNED_RG11_EAC}else return null;if(n===No||n===Do||n===Uo||n===Fo||n===ko||n===Oo||n===Bo||n===zo||n===Vo||n===Ho||n===Go||n===Wo||n===$o||n===qo)if(r=e.get("WEBGL_compressed_texture_astc"),r!==null){if(n===No)return a===yt?r.COMPRESSED_SRGB8_ALPHA8_ASTC_4x4_KHR:r.COMPRESSED_RGBA_ASTC_4x4_KHR;if(n===Do)return a===yt?r.COMPRESSED_SRGB8_ALPHA8_ASTC_5x4_KHR:r.COMPRESSED_RGBA_ASTC_5x4_KHR;if(n===Uo)return a===yt?r.COMPRESSED_SRGB8_ALPHA8_ASTC_5x5_KHR:r.COMPRESSED_RGBA_ASTC_5x5_KHR;if(n===Fo)return a===yt?r.COMPRESSED_SRGB8_ALPHA8_ASTC_6x5_KHR:r.COMPRESSED_RGBA_ASTC_6x5_KHR;if(n===ko)return a===yt?r.COMPRESSED_SRGB8_ALPHA8_ASTC_6x6_KHR:r.COMPRESSED_RGBA_ASTC_6x6_KHR;if(n===Oo)return a===yt?r.COMPRESSED_SRGB8_ALPHA8_ASTC_8x5_KHR:r.COMPRESSED_RGBA_ASTC_8x5_KHR;if(n===Bo)return a===yt?r.COMPRESSED_SRGB8_ALPHA8_ASTC_8x6_KHR:r.COMPRESSED_RGBA_ASTC_8x6_KHR;if(n===zo)return a===yt?r.COMPRESSED_SRGB8_ALPHA8_ASTC_8x8_KHR:r.COMPRESSED_RGBA_ASTC_8x8_KHR;if(n===Vo)return a===yt?r.COMPRESSED_SRGB8_ALPHA8_ASTC_10x5_KHR:r.COMPRESSED_RGBA_ASTC_10x5_KHR;if(n===Ho)return a===yt?r.COMPRESSED_SRGB8_ALPHA8_ASTC_10x6_KHR:r.COMPRESSED_RGBA_ASTC_10x6_KHR;if(n===Go)return a===yt?r.COMPRESSED_SRGB8_ALPHA8_ASTC_10x8_KHR:r.COMPRESSED_RGBA_ASTC_10x8_KHR;if(n===Wo)return a===yt?r.COMPRESSED_SRGB8_ALPHA8_ASTC_10x10_KHR:r.COMPRESSED_RGBA_ASTC_10x10_KHR;if(n===$o)return a===yt?r.COMPRESSED_SRGB8_ALPHA8_ASTC_12x10_KHR:r.COMPRESSED_RGBA_ASTC_12x10_KHR;if(n===qo)return a===yt?r.COMPRESSED_SRGB8_ALPHA8_ASTC_12x12_KHR:r.COMPRESSED_RGBA_ASTC_12x12_KHR}else return null;if(n===Xo||n===Yo||n===Zo)if(r=e.get("EXT_texture_compression_bptc"),r!==null){if(n===Xo)return a===yt?r.COMPRESSED_SRGB_ALPHA_BPTC_UNORM_EXT:r.COMPRESSED_RGBA_BPTC_UNORM_EXT;if(n===Yo)return r.COMPRESSED_RGB_BPTC_SIGNED_FLOAT_EXT;if(n===Zo)return r.COMPRESSED_RGB_BPTC_UNSIGNED_FLOAT_EXT}else return null;if(n===jo||n===Jo||n===Vr||n===Ko)if(r=e.get("EXT_texture_compression_rgtc"),r!==null){if(n===jo)return r.COMPRESSED_RED_RGTC1_EXT;if(n===Jo)return r.COMPRESSED_SIGNED_RED_RGTC1_EXT;if(n===Vr)return r.COMPRESSED_RED_GREEN_RGTC2_EXT;if(n===Ko)return r.COMPRESSED_SIGNED_RED_GREEN_RGTC2_EXT}else return null;return n===Is?i.UNSIGNED_INT_24_8:i[n]!==void 0?i[n]:null}return{convert:t}}var q0=`
void main() {

	gl_Position = vec4( position, 1.0 );

}`,X0=`
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

}`,Fc=class{constructor(){this.texture=null,this.mesh=null,this.depthNear=0,this.depthFar=0}init(e,t){if(this.texture===null){let n=new fr(e.texture);(e.depthNear!==t.depthNear||e.depthFar!==t.depthFar)&&(this.depthNear=e.depthNear,this.depthFar=e.depthFar),this.texture=n}}getMesh(e){if(this.texture!==null&&this.mesh===null){let t=e.cameras[0].viewport,n=new Nt({vertexShader:q0,fragmentShader:X0,uniforms:{depthColor:{value:this.texture},depthWidth:{value:t.z},depthHeight:{value:t.w}}});this.mesh=new mt(new xr(20,20),n)}return this.mesh}reset(){this.texture=null,this.mesh=null}getDepthTexture(){return this.texture}},kc=class extends zn{constructor(e,t){super();let n=this,s=null,r=1,a=null,o="local-floor",l=1,c=null,h=null,f=null,u=null,d=null,_=null,S=typeof XRWebGLBinding<"u",g=new Fc,p={},w=t.getContextAttributes(),I=null,y=null,A=[],E=[],D=new De,v=null,C=null,O=new qt;O.viewport=new It;let V=new qt;V.viewport=new It;let q=[O,V],j=new uo,z=null,Y=null;this.cameraAutoUpdate=!0,this.enabled=!1,this.isPresenting=!1,this.getController=function(ee){let ae=A[ee];return ae===void 0&&(ae=new vs,A[ee]=ae),ae.getTargetRaySpace()},this.getControllerGrip=function(ee){let ae=A[ee];return ae===void 0&&(ae=new vs,A[ee]=ae),ae.getGripSpace()},this.getHand=function(ee){let ae=A[ee];return ae===void 0&&(ae=new vs,A[ee]=ae),ae.getHandSpace()};function te(ee){let ae=E.indexOf(ee.inputSource);if(ae===-1)return;let Me=A[ae];Me!==void 0&&(Me.update(ee.inputSource,ee.frame,c||a),Me.dispatchEvent({type:ee.type,data:ee.inputSource}))}function re(){s.removeEventListener("select",te),s.removeEventListener("selectstart",te),s.removeEventListener("selectend",te),s.removeEventListener("squeeze",te),s.removeEventListener("squeezestart",te),s.removeEventListener("squeezeend",te),s.removeEventListener("end",re),s.removeEventListener("inputsourceschange",Z);for(let ee=0;ee<A.length;ee++){let ae=E[ee];ae!==null&&(E[ee]=null,A[ee].disconnect(ae))}z=null,Y=null,g.reset();for(let ee in p)delete p[ee];if(e.setRenderTarget(I),d=null,u=null,f=null,s=null,y=null,He.stop(),n.isPresenting=!1,e.setPixelRatio(v),e.setSize(D.width,D.height,!1),C!==null){let ee=C.camera;ee.fov=C.fov,ee.zoom=C.zoom,ee.updateProjectionMatrix(),C=null}n.dispatchEvent({type:"sessionend"})}this.setFramebufferScaleFactor=function(ee){r=ee,n.isPresenting===!0&&$e("WebXRManager: Cannot change framebuffer scale while presenting.")},this.setReferenceSpaceType=function(ee){o=ee,n.isPresenting===!0&&$e("WebXRManager: Cannot change reference space type while presenting.")},this.getReferenceSpace=function(){return c||a},this.setReferenceSpace=function(ee){c=ee},this.getBaseLayer=function(){return u!==null?u:d},this.getBinding=function(){return f===null&&S&&(f=new XRWebGLBinding(s,t)),f},this.getFrame=function(){return _},this.getSession=function(){return s},this.setSession=async function(ee){if(s=ee,s!==null){if(I=e.getRenderTarget(),s.addEventListener("select",te),s.addEventListener("selectstart",te),s.addEventListener("selectend",te),s.addEventListener("squeeze",te),s.addEventListener("squeezestart",te),s.addEventListener("squeezeend",te),s.addEventListener("end",re),s.addEventListener("inputsourceschange",Z),w.xrCompatible!==!0&&await t.makeXRCompatible(),v=e.getPixelRatio(),e.getSize(D),S&&"createProjectionLayer"in XRWebGLBinding.prototype){let Me=null,Pe=null,we=null;w.depth&&(we=w.stencil?t.DEPTH24_STENCIL8:t.DEPTH_COMPONENT24,Me=w.stencil?Si:Bn,Pe=w.stencil?Is:Un);let Ge={colorFormat:t.RGBA8,depthFormat:we,scaleFactor:r};f=this.getBinding(),u=f.createProjectionLayer(Ge),s.updateRenderState({layers:[u]}),e.setPixelRatio(1),e.setSize(u.textureWidth,u.textureHeight,!1),y=new Ft(u.textureWidth,u.textureHeight,{format:Tn,type:un,depthTexture:new mi(u.textureWidth,u.textureHeight,Pe,void 0,void 0,void 0,void 0,void 0,void 0,Me),stencilBuffer:w.stencil,colorSpace:e.outputColorSpace,samples:w.antialias?4:0,resolveDepthBuffer:u.ignoreDepthValues===!1,resolveStencilBuffer:u.ignoreDepthValues===!1,storeMultisampledDepthBuffer:u.ignoreDepthValues===!1,storeMultisampledStencilBuffer:u.ignoreDepthValues===!1})}else{let Me={antialias:w.antialias,alpha:!0,depth:w.depth,stencil:w.stencil,framebufferScaleFactor:r};d=new XRWebGLLayer(s,t,Me),s.updateRenderState({baseLayer:d}),e.setPixelRatio(1),e.setSize(d.framebufferWidth,d.framebufferHeight,!1),y=new Ft(d.framebufferWidth,d.framebufferHeight,{format:Tn,type:un,colorSpace:e.outputColorSpace,stencilBuffer:w.stencil,resolveDepthBuffer:d.ignoreDepthValues===!1,resolveStencilBuffer:d.ignoreDepthValues===!1,storeMultisampledDepthBuffer:d.ignoreDepthValues===!1,storeMultisampledStencilBuffer:d.ignoreDepthValues===!1})}y.isXRRenderTarget=!0,this.setFoveation(l),c=null,a=await s.requestReferenceSpace(o),He.setContext(s),He.start(),n.isPresenting=!0,n.dispatchEvent({type:"sessionstart"})}},this.getEnvironmentBlendMode=function(){if(s!==null)return s.environmentBlendMode},this.getDepthTexture=function(){return g.getDepthTexture()};function Z(ee){for(let ae=0;ae<ee.removed.length;ae++){let Me=ee.removed[ae],Pe=E.indexOf(Me);Pe>=0&&(E[Pe]=null,A[Pe].disconnect(Me))}for(let ae=0;ae<ee.added.length;ae++){let Me=ee.added[ae],Pe=E.indexOf(Me);if(Pe===-1){for(let Ge=0;Ge<A.length;Ge++)if(Ge>=E.length){E.push(Me),Pe=Ge;break}else if(E[Ge]===null){E[Ge]=Me,Pe=Ge;break}if(Pe===-1)break}let we=A[Pe];we&&we.connect(Me)}}let Q=new B,le=new B;function se(ee,ae,Me){Q.setFromMatrixPosition(ae.matrixWorld),le.setFromMatrixPosition(Me.matrixWorld);let Pe=Q.distanceTo(le),we=ae.projectionMatrix.elements,Ge=Me.projectionMatrix.elements,je=we[14]/(we[10]-1),Ze=we[14]/(we[10]+1),Qe=(we[9]+1)/we[5],ht=(we[9]-1)/we[5],Je=(we[8]-1)/we[0],ft=(Ge[8]+1)/Ge[0],Et=je*Je,Lt=je*ft,lt=Pe/(-Je+ft),tt=lt*-Je;if(ae.matrixWorld.decompose(ee.position,ee.quaternion,ee.scale),ee.translateX(tt),ee.translateZ(lt),ee.matrixWorld.compose(ee.position,ee.quaternion,ee.scale),ee.matrixWorldInverse.copy(ee.matrixWorld).invert(),we[10]===-1)ee.projectionMatrix.copy(ae.projectionMatrix),ee.projectionMatrixInverse.copy(ae.projectionMatrixInverse);else{let W=je+lt,gt=Ze+lt,et=Et-tt,L=Lt+(Pe-tt),x=Qe*Ze/gt*W,X=ht*Ze/gt*W;ee.projectionMatrix.makePerspective(et,L,x,X,W,gt),ee.projectionMatrixInverse.copy(ee.projectionMatrix).invert()}}function Oe(ee,ae){ae===null?ee.matrixWorld.copy(ee.matrix):ee.matrixWorld.multiplyMatrices(ae.matrixWorld,ee.matrix),ee.matrixWorldInverse.copy(ee.matrixWorld).invert()}this.updateCamera=function(ee){if(s===null)return;let ae=ee.near,Me=ee.far;g.texture!==null&&(g.depthNear>0&&(ae=g.depthNear),g.depthFar>0&&(Me=g.depthFar)),j.near=V.near=O.near=ae,j.far=V.far=O.far=Me,(z!==j.near||Y!==j.far)&&(s.updateRenderState({depthNear:j.near,depthFar:j.far}),z=j.near,Y=j.far),j.layers.mask=ee.layers.mask|6,O.layers.mask=j.layers.mask&-5,V.layers.mask=j.layers.mask&-3;let Pe=ee.parent,we=j.cameras;Oe(j,Pe);for(let Ge=0;Ge<we.length;Ge++)Oe(we[Ge],Pe);we.length===2?se(j,O,V):j.projectionMatrix.copy(O.projectionMatrix),C===null&&ee.isPerspectiveCamera&&(C={camera:ee,fov:ee.fov,zoom:ee.zoom}),Ie(ee,j,Pe)};function Ie(ee,ae,Me){Me===null?ee.matrix.copy(ae.matrixWorld):(ee.matrix.copy(Me.matrixWorld),ee.matrix.invert(),ee.matrix.multiply(ae.matrixWorld)),ee.matrix.decompose(ee.position,ee.quaternion,ee.scale),ee.updateMatrixWorld(!0),ee.projectionMatrix.copy(ae.projectionMatrix),ee.projectionMatrixInverse.copy(ae.projectionMatrixInverse),ee.isPerspectiveCamera&&(ee.fov=gs*2*Math.atan(1/ee.projectionMatrix.elements[5]),ee.zoom=1)}this.getCamera=function(){return j},this.getFoveation=function(){if(!(u===null&&d===null))return l},this.setFoveation=function(ee){l=ee,u!==null&&(u.fixedFoveation=ee),d!==null&&d.fixedFoveation!==void 0&&(d.fixedFoveation=ee)},this.hasDepthSensing=function(){return g.texture!==null},this.getDepthSensingMesh=function(){return g.getMesh(j)},this.getCameraTexture=function(ee){return p[ee]};let it=null;function Ve(ee,ae){if(h=ae.getViewerPose(c||a),_=ae,h!==null){let Me=h.views;d!==null&&(e.setRenderTargetFramebuffer(y,d.framebuffer),e.setRenderTarget(y));let Pe=!1;Me.length!==j.cameras.length&&(j.cameras.length=0,Pe=!0);for(let Ze=0;Ze<Me.length;Ze++){let Qe=Me[Ze],ht=null;if(d!==null)ht=d.getViewport(Qe);else{let ft=f.getViewSubImage(u,Qe);ht=ft.viewport,Ze===0&&(e.setRenderTargetTextures(y,ft.colorTexture,ft.depthStencilTexture),e.setRenderTarget(y))}let Je=q[Ze];Je===void 0&&(Je=new qt,Je.layers.enable(Ze),Je.viewport=new It,q[Ze]=Je),Je.matrix.fromArray(Qe.transform.matrix),Je.matrix.decompose(Je.position,Je.quaternion,Je.scale),Je.projectionMatrix.fromArray(Qe.projectionMatrix),Je.projectionMatrixInverse.copy(Je.projectionMatrix).invert(),Je.viewport.set(ht.x,ht.y,ht.width,ht.height),Ze===0&&(j.matrix.copy(Je.matrix),j.matrix.decompose(j.position,j.quaternion,j.scale)),Pe===!0&&j.cameras.push(Je)}let we=s.enabledFeatures;if(we&&we.includes("depth-sensing")&&s.depthUsage=="gpu-optimized"&&S){f=n.getBinding();let Ze=f.getDepthInformation(Me[0]);Ze&&Ze.isValid&&Ze.texture&&g.init(Ze,s.renderState)}if(we&&we.includes("camera-access")&&S){e.state.unbindTexture(),f=n.getBinding();for(let Ze=0;Ze<Me.length;Ze++){let Qe=Me[Ze].camera;if(Qe){let ht=p[Qe];ht||(ht=new fr,p[Qe]=ht);let Je=f.getCameraImage(Qe);ht.sourceTexture=Je}}}}for(let Me=0;Me<A.length;Me++){let Pe=E[Me],we=A[Me];Pe!==null&&we!==void 0&&we.update(Pe,ae,c||a)}it&&it(ee,ae),ae.detectedPlanes&&n.dispatchEvent({type:"planesdetected",data:ae}),_=null}let He=new Ph;He.setAnimationLoop(Ve),this.setAnimationLoop=function(ee){it=ee},this.dispose=function(){}}},Y0=new ut,kh=new Ye;kh.set(-1,0,0,0,1,0,0,0,1);function Z0(i,e){function t(g,p){g.matrixAutoUpdate===!0&&g.updateMatrix(),p.value.copy(g.matrix)}function n(g,p){p.color.getRGB(g.fogColor.value,vc(i)),p.isFog?(g.fogNear.value=p.near,g.fogFar.value=p.far):p.isFogExp2&&(g.fogDensity.value=p.density)}function s(g,p,w,I,y){p.isNodeMaterial?p.uniformsNeedUpdate=!1:p.isMeshBasicMaterial?r(g,p):p.isMeshLambertMaterial?(r(g,p),p.envMap&&(g.envMapIntensity.value=p.envMapIntensity)):p.isMeshToonMaterial?(r(g,p),f(g,p)):p.isMeshPhongMaterial?(r(g,p),h(g,p),p.envMap&&(g.envMapIntensity.value=p.envMapIntensity)):p.isMeshStandardMaterial?(r(g,p),u(g,p),p.isMeshPhysicalMaterial&&d(g,p,y)):p.isMeshMatcapMaterial?(r(g,p),_(g,p)):p.isMeshDepthMaterial?r(g,p):p.isMeshDistanceMaterial?(r(g,p),S(g,p)):p.isMeshNormalMaterial?r(g,p):p.isLineBasicMaterial?(a(g,p),p.isLineDashedMaterial&&o(g,p)):p.isPointsMaterial?l(g,p,w,I):p.isSpriteMaterial?c(g,p):p.isShadowMaterial?(g.color.value.copy(p.color),g.opacity.value=p.opacity):p.isShaderMaterial&&(p.uniformsNeedUpdate=!1)}function r(g,p){g.opacity.value=p.opacity,p.color&&g.diffuse.value.copy(p.color),p.emissive&&g.emissive.value.copy(p.emissive).multiplyScalar(p.emissiveIntensity),p.map&&(g.map.value=p.map,t(p.map,g.mapTransform)),p.alphaMap&&(g.alphaMap.value=p.alphaMap,t(p.alphaMap,g.alphaMapTransform)),p.bumpMap&&(g.bumpMap.value=p.bumpMap,t(p.bumpMap,g.bumpMapTransform),g.bumpScale.value=p.bumpScale,p.side===Zt&&(g.bumpScale.value*=-1)),p.normalMap&&(g.normalMap.value=p.normalMap,t(p.normalMap,g.normalMapTransform),g.normalScale.value.copy(p.normalScale),p.side===Zt&&g.normalScale.value.negate()),p.displacementMap&&(g.displacementMap.value=p.displacementMap,t(p.displacementMap,g.displacementMapTransform),g.displacementScale.value=p.displacementScale,g.displacementBias.value=p.displacementBias),p.emissiveMap&&(g.emissiveMap.value=p.emissiveMap,t(p.emissiveMap,g.emissiveMapTransform)),p.specularMap&&(g.specularMap.value=p.specularMap,t(p.specularMap,g.specularMapTransform)),p.alphaTest>0&&(g.alphaTest.value=p.alphaTest);let w=e.get(p),I=w.envMap,y=w.envMapRotation;I&&(g.envMap.value=I,g.envMapRotation.value.setFromMatrix4(Y0.makeRotationFromEuler(y)).transpose(),I.isCubeTexture&&I.isRenderTargetTexture===!1&&g.envMapRotation.value.premultiply(kh),g.reflectivity.value=p.reflectivity,g.ior.value=p.ior,g.refractionRatio.value=p.refractionRatio),p.lightMap&&(g.lightMap.value=p.lightMap,g.lightMapIntensity.value=p.lightMapIntensity,t(p.lightMap,g.lightMapTransform)),p.aoMap&&(g.aoMap.value=p.aoMap,g.aoMapIntensity.value=p.aoMapIntensity,t(p.aoMap,g.aoMapTransform))}function a(g,p){g.diffuse.value.copy(p.color),g.opacity.value=p.opacity,p.map&&(g.map.value=p.map,t(p.map,g.mapTransform))}function o(g,p){g.dashSize.value=p.dashSize,g.totalSize.value=p.dashSize+p.gapSize,g.scale.value=p.scale}function l(g,p,w,I){g.diffuse.value.copy(p.color),g.opacity.value=p.opacity,g.size.value=p.size*w,g.scale.value=I*.5,p.map&&(g.map.value=p.map,t(p.map,g.uvTransform)),p.alphaMap&&(g.alphaMap.value=p.alphaMap,t(p.alphaMap,g.alphaMapTransform)),p.alphaTest>0&&(g.alphaTest.value=p.alphaTest)}function c(g,p){g.diffuse.value.copy(p.color),g.opacity.value=p.opacity,g.rotation.value=p.rotation,p.map&&(g.map.value=p.map,t(p.map,g.mapTransform)),p.alphaMap&&(g.alphaMap.value=p.alphaMap,t(p.alphaMap,g.alphaMapTransform)),p.alphaTest>0&&(g.alphaTest.value=p.alphaTest)}function h(g,p){g.specular.value.copy(p.specular),g.shininess.value=Math.max(p.shininess,1e-4)}function f(g,p){p.gradientMap&&(g.gradientMap.value=p.gradientMap)}function u(g,p){g.metalness.value=p.metalness,p.metalnessMap&&(g.metalnessMap.value=p.metalnessMap,t(p.metalnessMap,g.metalnessMapTransform)),g.roughness.value=p.roughness,p.roughnessMap&&(g.roughnessMap.value=p.roughnessMap,t(p.roughnessMap,g.roughnessMapTransform)),p.envMap&&(g.envMapIntensity.value=p.envMapIntensity)}function d(g,p,w){g.ior.value=p.ior,p.sheen>0&&(g.sheenColor.value.copy(p.sheenColor).multiplyScalar(p.sheen),g.sheenRoughness.value=p.sheenRoughness,p.sheenColorMap&&(g.sheenColorMap.value=p.sheenColorMap,t(p.sheenColorMap,g.sheenColorMapTransform)),p.sheenRoughnessMap&&(g.sheenRoughnessMap.value=p.sheenRoughnessMap,t(p.sheenRoughnessMap,g.sheenRoughnessMapTransform))),p.clearcoat>0&&(g.clearcoat.value=p.clearcoat,g.clearcoatRoughness.value=p.clearcoatRoughness,p.clearcoatMap&&(g.clearcoatMap.value=p.clearcoatMap,t(p.clearcoatMap,g.clearcoatMapTransform)),p.clearcoatRoughnessMap&&(g.clearcoatRoughnessMap.value=p.clearcoatRoughnessMap,t(p.clearcoatRoughnessMap,g.clearcoatRoughnessMapTransform)),p.clearcoatNormalMap&&(g.clearcoatNormalMap.value=p.clearcoatNormalMap,t(p.clearcoatNormalMap,g.clearcoatNormalMapTransform),g.clearcoatNormalScale.value.copy(p.clearcoatNormalScale),p.side===Zt&&g.clearcoatNormalScale.value.negate())),p.dispersion>0&&(g.dispersion.value=p.dispersion),p.retroreflectivity>0&&(g.retroreflectivity.value=p.retroreflectivity),p.iridescence>0&&(g.iridescence.value=p.iridescence,g.iridescenceIOR.value=p.iridescenceIOR,g.iridescenceThicknessMinimum.value=p.iridescenceThicknessRange[0],g.iridescenceThicknessMaximum.value=p.iridescenceThicknessRange[1],p.iridescenceMap&&(g.iridescenceMap.value=p.iridescenceMap,t(p.iridescenceMap,g.iridescenceMapTransform)),p.iridescenceThicknessMap&&(g.iridescenceThicknessMap.value=p.iridescenceThicknessMap,t(p.iridescenceThicknessMap,g.iridescenceThicknessMapTransform))),p.transmission>0&&(g.transmission.value=p.transmission,g.transmissionSamplerMap.value=w.texture,g.transmissionSamplerSize.value.set(w.width,w.height),p.transmissionMap&&(g.transmissionMap.value=p.transmissionMap,t(p.transmissionMap,g.transmissionMapTransform)),g.thickness.value=p.thickness,p.thicknessMap&&(g.thicknessMap.value=p.thicknessMap,t(p.thicknessMap,g.thicknessMapTransform)),g.attenuationDistance.value=p.attenuationDistance,g.attenuationColor.value.copy(p.attenuationColor)),p.anisotropy>0&&(g.anisotropyVector.value.set(p.anisotropy*Math.cos(p.anisotropyRotation),p.anisotropy*Math.sin(p.anisotropyRotation)),p.anisotropyMap&&(g.anisotropyMap.value=p.anisotropyMap,t(p.anisotropyMap,g.anisotropyMapTransform))),g.specularIntensity.value=p.specularIntensity,g.specularColor.value.copy(p.specularColor),p.specularColorMap&&(g.specularColorMap.value=p.specularColorMap,t(p.specularColorMap,g.specularColorMapTransform)),p.specularIntensityMap&&(g.specularIntensityMap.value=p.specularIntensityMap,t(p.specularIntensityMap,g.specularIntensityMapTransform))}function _(g,p){p.matcap&&(g.matcap.value=p.matcap)}function S(g,p){let w=e.get(p).light;g.referencePosition.value.setFromMatrixPosition(w.matrixWorld),g.nearDistance.value=w.shadow.camera.near,g.farDistance.value=w.shadow.camera.far}return{refreshFogUniforms:n,refreshMaterialUniforms:s}}function j0(i,e,t,n){let s={},r={},a=[],o=i.getParameter(i.MAX_UNIFORM_BUFFER_BINDINGS);function l(y,A){let E=A.program;n.uniformBlockBinding(y,E)}function c(y,A){let E=s[y.id];E===void 0&&(g(y),E=h(y),s[y.id]=E,y.addEventListener("dispose",w));let D=A.program;n.updateUBOMapping(y,D);let v=e.render.frame;r[y.id]!==v&&(u(y),r[y.id]=v)}function h(y){let A=f();y.__bindingPointIndex=A;let E=i.createBuffer(),D=y.__size,v=y.usage;return i.bindBuffer(i.UNIFORM_BUFFER,E),i.bufferData(i.UNIFORM_BUFFER,D,v),i.bindBuffer(i.UNIFORM_BUFFER,null),i.bindBufferBase(i.UNIFORM_BUFFER,A,E),E}function f(){for(let y=0;y<o;y++)if(a.indexOf(y)===-1)return a.push(y),y;return Xe("WebGLRenderer: Maximum number of simultaneously usable uniforms groups reached."),0}function u(y){let A=s[y.id],E=y.uniforms,D=y.__cache;i.bindBuffer(i.UNIFORM_BUFFER,A);for(let v=0,C=E.length;v<C;v++){let O=E[v];if(Array.isArray(O))for(let V=0,q=O.length;V<q;V++)d(O[V],v,V,D);else d(O,v,0,D)}i.bindBuffer(i.UNIFORM_BUFFER,null)}function d(y,A,E,D){if(S(y,A,E,D)===!0){let v=y.__offset,C=y.value;if(Array.isArray(C)){let O=0;for(let V=0;V<C.length;V++){let q=C[V],j=p(q);_(q,y.__data,O),typeof q!="number"&&typeof q!="boolean"&&!q.isMatrix3&&!ArrayBuffer.isView(q)&&(O+=j.storage/Float32Array.BYTES_PER_ELEMENT)}}else _(C,y.__data,0);i.bufferSubData(i.UNIFORM_BUFFER,v,y.__data)}}function _(y,A,E){typeof y=="number"||typeof y=="boolean"?A[0]=y:y.isMatrix3?(A[0]=y.elements[0],A[1]=y.elements[1],A[2]=y.elements[2],A[3]=0,A[4]=y.elements[3],A[5]=y.elements[4],A[6]=y.elements[5],A[7]=0,A[8]=y.elements[6],A[9]=y.elements[7],A[10]=y.elements[8],A[11]=0):ArrayBuffer.isView(y)?A.set(new y.constructor(y.buffer,y.byteOffset,A.length)):y.toArray(A,E)}function S(y,A,E,D){let v=y.value,C=A+"_"+E;if(D[C]===void 0)return typeof v=="number"||typeof v=="boolean"?D[C]=v:ArrayBuffer.isView(v)?D[C]=v.slice():D[C]=v.clone(),!0;{let O=D[C];if(typeof v=="number"||typeof v=="boolean"){if(O!==v)return D[C]=v,!0}else{if(ArrayBuffer.isView(v))return!0;if(O.equals(v)===!1)return O.copy(v),!0}}return!1}function g(y){let A=y.uniforms,E=0,D=16;for(let C=0,O=A.length;C<O;C++){let V=Array.isArray(A[C])?A[C]:[A[C]];for(let q=0,j=V.length;q<j;q++){let z=V[q],Y=Array.isArray(z.value)?z.value:[z.value];for(let te=0,re=Y.length;te<re;te++){let Z=Y[te],Q=p(Z),le=E%D,se=le%Q.boundary,Oe=le+se;E+=se,Oe!==0&&D-Oe<Q.storage&&(E+=D-Oe),z.__data=new Float32Array(Q.storage/Float32Array.BYTES_PER_ELEMENT),z.__offset=E,E+=Q.storage}}}let v=E%D;return v>0&&(E+=D-v),y.__size=E,y.__cache={},this}function p(y){let A={boundary:0,storage:0};return typeof y=="number"||typeof y=="boolean"?(A.boundary=4,A.storage=4):y.isVector2?(A.boundary=8,A.storage=8):y.isVector3||y.isColor?(A.boundary=16,A.storage=12):y.isVector4?(A.boundary=16,A.storage=16):y.isMatrix3?(A.boundary=48,A.storage=48):y.isMatrix4?(A.boundary=64,A.storage=64):y.isTexture?$e("WebGLRenderer: Texture samplers can not be part of an uniforms group."):ArrayBuffer.isView(y)?(A.boundary=16,A.storage=y.byteLength):$e("WebGLRenderer: Unsupported uniform value type.",y),A}function w(y){let A=y.target;A.removeEventListener("dispose",w);let E=a.indexOf(A.__bindingPointIndex);a.splice(E,1),i.deleteBuffer(s[A.id]),delete s[A.id],delete r[A.id]}function I(){for(let y in s)i.deleteBuffer(s[y]);a=[],s={},r={}}return{bind:l,update:c,dispose:I}}var J0=new Uint16Array([12469,15057,12620,14925,13266,14620,13807,14376,14323,13990,14545,13625,14713,13328,14840,12882,14931,12528,14996,12233,15039,11829,15066,11525,15080,11295,15085,10976,15082,10705,15073,10495,13880,14564,13898,14542,13977,14430,14158,14124,14393,13732,14556,13410,14702,12996,14814,12596,14891,12291,14937,11834,14957,11489,14958,11194,14943,10803,14921,10506,14893,10278,14858,9960,14484,14039,14487,14025,14499,13941,14524,13740,14574,13468,14654,13106,14743,12678,14818,12344,14867,11893,14889,11509,14893,11180,14881,10751,14852,10428,14812,10128,14765,9754,14712,9466,14764,13480,14764,13475,14766,13440,14766,13347,14769,13070,14786,12713,14816,12387,14844,11957,14860,11549,14868,11215,14855,10751,14825,10403,14782,10044,14729,9651,14666,9352,14599,9029,14967,12835,14966,12831,14963,12804,14954,12723,14936,12564,14917,12347,14900,11958,14886,11569,14878,11247,14859,10765,14828,10401,14784,10011,14727,9600,14660,9289,14586,8893,14508,8533,15111,12234,15110,12234,15104,12216,15092,12156,15067,12010,15028,11776,14981,11500,14942,11205,14902,10752,14861,10393,14812,9991,14752,9570,14682,9252,14603,8808,14519,8445,14431,8145,15209,11449,15208,11451,15202,11451,15190,11438,15163,11384,15117,11274,15055,10979,14994,10648,14932,10343,14871,9936,14803,9532,14729,9218,14645,8742,14556,8381,14461,8020,14365,7603,15273,10603,15272,10607,15267,10619,15256,10631,15231,10614,15182,10535,15118,10389,15042,10167,14963,9787,14883,9447,14800,9115,14710,8665,14615,8318,14514,7911,14411,7507,14279,7198,15314,9675,15313,9683,15309,9712,15298,9759,15277,9797,15229,9773,15166,9668,15084,9487,14995,9274,14898,8910,14800,8539,14697,8234,14590,7790,14479,7409,14367,7067,14178,6621,15337,8619,15337,8631,15333,8677,15325,8769,15305,8871,15264,8940,15202,8909,15119,8775,15022,8565,14916,8328,14804,8009,14688,7614,14569,7287,14448,6888,14321,6483,14088,6171,15350,7402,15350,7419,15347,7480,15340,7613,15322,7804,15287,7973,15229,8057,15148,8012,15046,7846,14933,7611,14810,7357,14682,7069,14552,6656,14421,6316,14251,5948,14007,5528,15356,5942,15356,5977,15353,6119,15348,6294,15332,6551,15302,6824,15249,7044,15171,7122,15070,7050,14949,6861,14818,6611,14679,6349,14538,6067,14398,5651,14189,5311,13935,4958,15359,4123,15359,4153,15356,4296,15353,4646,15338,5160,15311,5508,15263,5829,15188,6042,15088,6094,14966,6001,14826,5796,14678,5543,14527,5287,14377,4985,14133,4586,13869,4257,15360,1563,15360,1642,15358,2076,15354,2636,15341,3350,15317,4019,15273,4429,15203,4732,15105,4911,14981,4932,14836,4818,14679,4621,14517,4386,14359,4156,14083,3795,13808,3437,15360,122,15360,137,15358,285,15355,636,15344,1274,15322,2177,15281,2765,15215,3223,15120,3451,14995,3569,14846,3567,14681,3466,14511,3305,14344,3121,14037,2800,13753,2467,15360,0,15360,1,15359,21,15355,89,15346,253,15325,479,15287,796,15225,1148,15133,1492,15008,1749,14856,1882,14685,1886,14506,1783,14324,1608,13996,1398,13702,1183]),$n=null;function K0(){return $n===null&&($n=new lr(J0,16,16,Ti,jt),$n.name="DFG_LUT",$n.minFilter=Yt,$n.magFilter=Yt,$n.wrapS=On,$n.wrapT=On,$n.generateMipmaps=!1,$n.needsUpdate=!0),$n}var rl=class{constructor(e={}){let{canvas:t=ih(),context:n=null,depth:s=!0,stencil:r=!1,alpha:a=!1,antialias:o=!1,premultipliedAlpha:l=!0,preserveDrawingBuffer:c=!1,powerPreference:h="default",failIfMajorPerformanceCaveat:f=!1,reversedDepthBuffer:u=!1,outputBufferType:d=un}=e;this.isWebGLRenderer=!0;let _;if(n!==null){if(typeof WebGLRenderingContext<"u"&&n instanceof WebGLRenderingContext)throw new Error("THREE.WebGLRenderer: WebGL 1 is not supported since r163.");_=n.getContextAttributes().alpha}else _=a;let S=d,g=new Set([Mo,bo,yo]),p=new Set([un,Un,Rs,Is,_o,xo]),w=new Uint32Array(4),I=new Int32Array(4),y=new B,A=null,E=null,D=[],v=[],C=null;this.domElement=t,this.debug={checkShaderErrors:!0,diagnostics:{keywords:!1},onShaderError:null},this.autoClear=!0,this.autoClearColor=!0,this.autoClearDepth=!0,this.autoClearStencil=!0,this.sortObjects=!0,this.clippingPlanes=[],this.localClippingEnabled=!1,this.toneMapping=Dn,this.toneMappingExposure=1,this.transmissionResolutionScale=1;let O=this,V=!1,q=null,j=null,z=null,Y=null;this._outputColorSpace=nn;let te=0,re=0,Z=null,Q=-1,le=null,se=new It,Oe=new It,Ie=null,it=new qe(0),Ve=0,He=t.width,ee=t.height,ae=1,Me=null,Pe=null,we=new It(0,0,He,ee),Ge=new It(0,0,He,ee),je=!1,Ze=new ys,Qe=!1,ht=!1,Je=new ut,ft=new B,Et=new It,Lt={background:null,fog:null,environment:null,overrideMaterial:null,isScene:!0},lt=!1;function tt(){return Z===null?ae:1}let W=n;function gt(m,T){return t.getContext(m,T)}let et,L,x,X,K,oe,be,Ae,F,$,ie,me,ce,fe,ye,Ee,Fe,H,Se,J,ve,Ce,de;try{let m={alpha:!0,depth:s,stencil:r,antialias:o,premultipliedAlpha:l,preserveDrawingBuffer:c,powerPreference:h,failIfMajorPerformanceCaveat:f};if("setAttribute"in t&&t.setAttribute("data-engine",`three.js r${"186"}`),t.addEventListener("webglcontextlost",bt,!1),t.addEventListener("webglcontextrestored",xt,!1),t.addEventListener("webglcontextcreationerror",hn,!1),W===null){let T="webgl2";if(W=gt(T,m),W===null)throw gt(T)?new Error("THREE.WebGLRenderer: Error creating WebGL context with your selected attributes."):new Error("THREE.WebGLRenderer: Error creating WebGL context.")}Be()}catch(m){throw t.removeEventListener("webglcontextlost",bt,!1),t.removeEventListener("webglcontextrestored",xt,!1),t.removeEventListener("webglcontextcreationerror",hn,!1),Xe("WebGLRenderer: "+m.message),m}function Be(){et=new rg(W),et.init(),ve=new $0(W,et),L=new Zm(W,et,e,ve),x=new G0(W,et),L.reversedDepthBuffer&&u&&x.buffers.depth.setReversed(!0),j=W.createFramebuffer(),z=W.createFramebuffer(),Y=W.createFramebuffer(),X=new lg(W),K=new R0,oe=new W0(W,et,x,K,L,ve,X),be=new sg(O),Ae=new uf(W),Ce=new Xm(W,Ae),F=new ag(W,Ae,X,Ce),$=new ug(W,F,Ae,Ce,X),H=new cg(W,L,oe),ye=new jm(K),ie=new C0(O,be,et,L,Ce,ye),me=new Z0(O,K),ce=new P0,fe=new k0(et),Fe=new qm(O,be,x,$,_,l),Ee=new H0(O,$,L),de=new j0(W,X,L,x),Se=new Ym(W,et,X),J=new og(W,et,X),X.programs=ie.programs,O.capabilities=L,O.extensions=et,O.properties=K,O.renderLists=ce,O.shadowMap=Ee,O.state=x,O.info=X}S!==un&&(C=new dg(S,t.width,t.height,o,s,r));let Ue=new kc(O,W);this.xr=Ue,this.getContext=function(){return W},this.getContextAttributes=function(){return W.getContextAttributes()},this.forceContextLoss=function(){let m=et.get("WEBGL_lose_context");m&&m.loseContext()},this.forceContextRestore=function(){let m=et.get("WEBGL_lose_context");m&&m.restoreContext()},this.getPixelRatio=function(){return ae},this.setPixelRatio=function(m){m!==void 0&&(ae=m,this.setSize(He,ee,!1))},this.getSize=function(m){return m.set(He,ee)},this.setSize=function(m,T,P=!0){if(Ue.isPresenting){$e("WebGLRenderer: Can't change size while VR device is presenting.");return}He=m,ee=T,t.width=Math.floor(m*ae),t.height=Math.floor(T*ae),P===!0&&(t.style.width=m+"px",t.style.height=T+"px"),C!==null&&C.setSize(t.width,t.height),this.setViewport(0,0,m,T)},this.getDrawingBufferSize=function(m){return m.set(He*ae,ee*ae).floor()},this.setDrawingBufferSize=function(m,T,P){He=m,ee=T,ae=P,t.width=Math.floor(m*P),t.height=Math.floor(T*P),this.setViewport(0,0,m,T)},this.setEffects=function(m){if(S===un){Xe("WebGLRenderer: setEffects() requires outputBufferType set to HalfFloatType or FloatType.");return}if(m){for(let T=0;T<m.length;T++)if(m[T].isOutputPass===!0){$e("WebGLRenderer: OutputPass is not needed in setEffects(). Tone mapping and color space conversion are applied automatically.");break}}C.setEffects(m||[])},this.getCurrentViewport=function(m){return m.copy(se)},this.getViewport=function(m){return m.copy(we)},this.setViewport=function(m,T,P,U){m.isVector4?we.set(m.x,m.y,m.z,m.w):we.set(m,T,P,U),x.viewport(se.copy(we).multiplyScalar(ae).round())},this.getScissor=function(m){return m.copy(Ge)},this.setScissor=function(m,T,P,U){m.isVector4?Ge.set(m.x,m.y,m.z,m.w):Ge.set(m,T,P,U),x.scissor(Oe.copy(Ge).multiplyScalar(ae).round())},this.getScissorTest=function(){return je},this.setScissorTest=function(m){x.setScissorTest(je=m)},this.setOpaqueSort=function(m){Me=m},this.setTransparentSort=function(m){Pe=m},this.getClearColor=function(m){return m.copy(Fe.getClearColor())},this.setClearColor=function(){Fe.setClearColor(...arguments)},this.getClearAlpha=function(){return Fe.getClearAlpha()},this.setClearAlpha=function(){Fe.setClearAlpha(...arguments)},this.clear=function(m=!0,T=!0,P=!0){let U=0;if(m){let N=!1;if(Z!==null){let ne=Z.texture.format;N=g.has(ne)}if(N){let ne=Z.texture.type,he=p.has(ne),k=Fe.getClearColor(),pe=Fe.getClearAlpha(),ge=k.r,xe=k.g,Re=k.b;he?(w[0]=ge,w[1]=xe,w[2]=Re,w[3]=pe,W.clearBufferuiv(W.COLOR,0,w)):(I[0]=ge,I[1]=xe,I[2]=Re,I[3]=pe,W.clearBufferiv(W.COLOR,0,I))}else U|=W.COLOR_BUFFER_BIT}T&&(U|=W.DEPTH_BUFFER_BIT,this.state.buffers.depth.setMask(!0)),P&&(U|=W.STENCIL_BUFFER_BIT,this.state.buffers.stencil.setMask(4294967295)),U!==0&&W.clear(U)},this.clearColor=function(){this.clear(!0,!1,!1)},this.clearDepth=function(){this.clear(!1,!0,!1)},this.clearStencil=function(){this.clear(!1,!1,!0)},this.setNodesHandler=function(m){m.setRenderer(this),q=m},this.dispose=function(){t.removeEventListener("webglcontextlost",bt,!1),t.removeEventListener("webglcontextrestored",xt,!1),t.removeEventListener("webglcontextcreationerror",hn,!1),Fe.dispose(),ce.dispose(),fe.dispose(),K.dispose(),be.dispose(),$.dispose(),Ce.dispose(),de.dispose(),ie.dispose(),Ue.dispose(),Ue.removeEventListener("sessionstart",Kr),Ue.removeEventListener("sessionend",Hs),_n.stop()};function bt(m){m.preventDefault(),gc("WebGLRenderer: Context Lost."),V=!0}function xt(){gc("WebGLRenderer: Context Restored."),V=!1;let m=X.autoReset,T=Ee.enabled,P=Ee.autoUpdate,U=Ee.needsUpdate,N=Ee.type;Be(),X.autoReset=m,Ee.enabled=T,Ee.autoUpdate=P,Ee.needsUpdate=U,Ee.type=N}function hn(m){Xe("WebGLRenderer: A WebGL context could not be created. Reason: ",m.statusMessage)}function gn(m){let T=m.target;T.removeEventListener("dispose",gn),ml(T)}function ml(m){gl(m),K.remove(m)}function gl(m){let T=K.get(m).programs;T!==void 0&&(T.forEach(function(P){ie.releaseProgram(P)}),m.isShaderMaterial&&ie.releaseShaderCache(m))}this.renderBufferDirect=function(m,T,P,U,N,ne){T===null&&(T=Lt);let he=N.isMesh&&N.matrixWorld.determinantAffine()<0,k=M(m,T,P,U,N);x.setMaterial(U,he);let pe=P.index,ge=1;if(U.wireframe===!0){if(pe=F.getWireframeAttribute(P),pe===void 0)return;ge=2}let xe=P.drawRange,Re=P.attributes.position,Te=xe.start*ge,ze=(xe.start+xe.count)*ge;ne!==null&&(Te=Math.max(Te,ne.start*ge),ze=Math.min(ze,(ne.start+ne.count)*ge)),pe!==null?(Te=Math.max(Te,0),ze=Math.min(ze,pe.count)):Re!=null&&(Te=Math.max(Te,0),ze=Math.min(ze,Re.count));let Ke=ze-Te;if(Ke<0||Ke===1/0)return;Ce.setup(N,U,k,P,pe);let st,_t=Se;if(pe!==null&&(st=Ae.get(pe),_t=J,_t.setIndex(st)),N.isMesh)U.wireframe===!0?(x.setLineWidth(U.wireframeLinewidth*tt()),_t.setMode(W.LINES)):_t.setMode(W.TRIANGLES);else if(N.isLine){let Pt=U.linewidth;Pt===void 0&&(Pt=1),x.setLineWidth(Pt*tt()),N.isLineSegments?_t.setMode(W.LINES):N.isLineLoop?_t.setMode(W.LINE_LOOP):_t.setMode(W.LINE_STRIP)}else N.isPoints?_t.setMode(W.POINTS):N.isSprite&&_t.setMode(W.TRIANGLES);if(N.isBatchedMesh)if(et.get("WEBGL_multi_draw"))_t.renderMultiDraw(N._multiDrawStarts,N._multiDrawCounts,N._multiDrawCount);else{let Pt=N._multiDrawStarts,Ne=N._multiDrawCounts,Ct=N._multiDrawCount,We=pe?Ae.get(pe).bytesPerElement:1,Rt=K.get(U).currentProgram.getUniforms();for(let Vt=0;Vt<Ct;Vt++)Rt.setValue(W,"_gl_DrawID",Vt),_t.render(Pt[Vt]/We,Ne[Vt])}else if(N.isInstancedMesh)_t.renderInstances(Te,Ke,N.count);else if(P.isInstancedBufferGeometry){let Pt=P._maxInstanceCount!==void 0?P._maxInstanceCount:1/0,Ne=Math.min(P.instanceCount,Pt);_t.renderInstances(Te,Ke,Ne)}else _t.render(Te,Ke)};function Jr(m,T,P,U){q!==null&&m.isNodeMaterial&&q.setObject(U,m),Qe===!0&&ye.setState(m,P,!1),m.transparent===!0&&m.side===Wn&&m.forceSinglePass===!1?(m.side=Zt,m.needsUpdate=!0,ai(m,T,U),m.side=yi,m.needsUpdate=!0,ai(m,T,U),m.side=Wn):ai(m,T,U)}this.compile=function(m,T,P=null){P===null&&(P=m),q!==null&&q.renderStart(m,T,P),E=fe.get(P),E.init(T),v.push(E),P.traverseVisible(function(N){N.isLight&&N.layers.test(T.layers)&&(E.pushLight(N),N.castShadow&&E.pushShadow(N))}),m!==P&&m.traverseVisible(function(N){N.isLight&&N.layers.test(T.layers)&&(E.pushLight(N),N.castShadow&&E.pushShadow(N))}),E.setupLights(),q!==null&&q.updateLights(E.state.lightsArray),ht=this.localClippingEnabled,Qe=ye.init(this.clippingPlanes,ht),Qe===!0&&ye.setGlobalState(this.clippingPlanes,T),q!==null&&Ee.render(E.state.shadowsArray,P,T);let U=new Set;return m.traverse(function(N){if(!(N.isMesh||N.isPoints||N.isLine||N.isSprite))return;let ne=N.material;if(ne)if(Array.isArray(ne))for(let he=0;he<ne.length;he++){let k=ne[he];Jr(k,P,T,N),U.add(k)}else Jr(ne,P,T,N),U.add(ne)}),E=v.pop(),q!==null&&q.renderEnd(),U},this.compileAsync=function(m,T,P=null){let U=this.compile(m,T,P);return new Promise(N=>{function ne(){if(U.forEach(function(he){let pe=K.get(he).currentProgram;(pe===void 0||pe.isReady())&&U.delete(he)}),U.size===0){N(m);return}setTimeout(ne,10)}et.get("KHR_parallel_shader_compile")!==null?ne():setTimeout(ne,10)})};let Vs=null;function _l(m){Vs&&Vs(m)}function Kr(){_n.stop()}function Hs(){_n.start()}let _n=new Ph;_n.setAnimationLoop(_l),typeof self<"u"&&_n.setContext(self),this.setAnimationLoop=function(m){Vs=m,Ue.setAnimationLoop(m),m===null?_n.stop():_n.start()},Ue.addEventListener("sessionstart",Kr),Ue.addEventListener("sessionend",Hs),this.render=function(m,T){if(T!==void 0&&T.isCamera!==!0){Xe("WebGLRenderer.render: camera is not an instance of THREE.Camera.");return}if(V===!0)return;q!==null&&q.renderStart(m,T);let P=Ue.enabled===!0&&Ue.isPresenting===!0,U=C!==null&&(Z===null||P)&&C.begin(O,Z);if(m.matrixWorldAutoUpdate===!0&&m.updateMatrixWorld(),T.parent===null&&T.matrixWorldAutoUpdate===!0&&T.updateMatrixWorld(),Ue.enabled===!0&&Ue.isPresenting===!0&&(C===null||C.isCompositing()===!1)&&(Ue.cameraAutoUpdate===!0&&Ue.updateCamera(T),T=Ue.getCamera()),m.isScene===!0&&m.onBeforeRender(O,m,T,Z),E=fe.get(m,v.length),E.init(T),E.state.textureUnits=oe.getTextureUnits(),v.push(E),Je.multiplyMatrices(T.projectionMatrix,T.matrixWorldInverse),Ze.setFromProjectionMatrix(Je,Pn,T.reversedDepth),ht=this.localClippingEnabled,Qe=ye.init(this.clippingPlanes,ht),A=ce.get(m,D.length),A.init(),D.push(A),Ue.enabled===!0&&Ue.isPresenting===!0){let he=O.xr.getDepthSensingMesh();he!==null&&ri(he,T,-1/0,O.sortObjects)}ri(m,T,0,O.sortObjects),A.finish(),q!==null&&q.updateLights(E.state.lightsArray),O.sortObjects===!0&&A.sort(Me,Pe),lt=Ue.enabled===!1||Ue.isPresenting===!1||Ue.hasDepthSensing()===!1,lt&&Fe.addToRenderList(A,m),this.info.render.frame++,this.info.autoReset===!0&&this.info.reset(),Qe===!0&&ye.beginShadows();let N=E.state.shadowsArray;if(Ee.render(N,m,T),Qe===!0&&ye.endShadows(),(U&&C.hasRenderPass())===!1){let he=A.opaque,k=A.transmissive;if(E.setupLights(),T.isArrayCamera){let pe=T.cameras;if(k.length>0)for(let ge=0,xe=pe.length;ge<xe;ge++){let Re=pe[ge];Xi(he,k,m,Re)}lt&&Fe.render(m);for(let ge=0,xe=pe.length;ge<xe;ge++){let Re=pe[ge];Ci(A,m,Re,Re.viewport)}}else k.length>0&&Xi(he,k,m,T),lt&&Fe.render(m),Ci(A,m,T)}Z!==null&&re===0&&(oe.updateMultisampleRenderTarget(Z),oe.updateRenderTargetMipmap(Z)),U&&C.end(O),m.isScene===!0&&m.onAfterRender(O,m,T),Ce.resetDefaultState(),Q=-1,le=null,v.pop(),v.length>0?(E=v[v.length-1],oe.setTextureUnits(E.state.textureUnits),Qe===!0&&ye.setGlobalState(O.clippingPlanes,E.state.camera)):E=null,D.pop(),D.length>0?A=D[D.length-1]:A=null,q!==null&&q.renderEnd()};function ri(m,T,P,U){if(m.visible===!1)return;if(m.layers.test(T.layers)){if(m.isGroup)P=m.renderOrder;else if(m.isLOD)m.autoUpdate===!0&&m.update(T);else if(m.isLightProbeGrid)E.pushLightProbeGrid(m);else if(m.isLight)E.pushLight(m),m.castShadow&&E.pushShadow(m);else if(m.isSprite){if(!m.frustumCulled||m.intersectsFrustum(Ze)){U&&Et.setFromMatrixPosition(m.matrixWorld).applyMatrix4(Je);let he=$.update(m),k=m.material;k.visible&&A.push(m,he,k,P,Et.z,null,T)}}else if((m.isMesh||m.isLine||m.isPoints)&&(!m.frustumCulled||m.intersectsFrustum(Ze))){let he=$.update(m),k=m.material;if(U&&(m.boundingSphere!==void 0?(m.boundingSphere===null&&m.computeBoundingSphere(),Et.copy(m.boundingSphere.center)):(he.boundingSphere===null&&he.computeBoundingSphere(),Et.copy(he.boundingSphere.center)),Et.applyMatrix4(m.matrixWorld).applyMatrix4(Je)),Array.isArray(k)){let pe=he.groups;for(let ge=0,xe=pe.length;ge<xe;ge++){let Re=pe[ge],Te=k[Re.materialIndex];Te&&Te.visible&&A.push(m,he,Te,P,Et.z,Re,T)}}else k.visible&&A.push(m,he,k,P,Et.z,null,T)}}let ne=m.children;for(let he=0,k=ne.length;he<k;he++)ri(ne[he],T,P,U)}function Ci(m,T,P,U){let{opaque:N,transmissive:ne,transparent:he}=m;E.setupLightsView(P),Qe===!0&&ye.setGlobalState(O.clippingPlanes,P),U&&x.viewport(se.copy(U)),N.length>0&&Fn(N,T,P),ne.length>0&&Fn(ne,T,P),he.length>0&&Fn(he,T,P),x.buffers.depth.setTest(!0),x.buffers.depth.setMask(!0),x.buffers.color.setMask(!0),x.setPolygonOffset(!1)}function Xi(m,T,P,U){if((P.isScene===!0?P.overrideMaterial:null)!==null)return;if(E.state.transmissionRenderTarget[U.id]===void 0){let Te=et.has("EXT_color_buffer_half_float")||et.has("EXT_color_buffer_float");E.state.transmissionRenderTarget[U.id]=new Ft(1,1,{generateMipmaps:!0,type:Te?jt:un,minFilter:Mi,samples:Math.max(4,L.samples),stencilBuffer:r,resolveDepthBuffer:!1,resolveStencilBuffer:!1,storeMultisampledDepthBuffer:!1,storeMultisampledStencilBuffer:!1,colorSpace:at.workingColorSpace})}let ne=E.state.transmissionRenderTarget[U.id],he=U.viewport||se;ne.setSize(he.z*O.transmissionResolutionScale,he.w*O.transmissionResolutionScale);let k=O.getRenderTarget(),pe=O.getActiveCubeFace(),ge=O.getActiveMipmapLevel();O.setRenderTarget(ne),O.getClearColor(it),Ve=O.getClearAlpha(),Ve<1&&O.setClearColor(16777215,.5),O.clear(),lt&&Fe.render(P);let xe=O.toneMapping;O.toneMapping=Dn;let Re=U.viewport;if(U.viewport!==void 0&&(U.viewport=void 0),E.setupLightsView(U),Qe===!0&&ye.setGlobalState(O.clippingPlanes,U),Fn(m,P,U),oe.updateMultisampleRenderTarget(ne),oe.updateRenderTargetMipmap(ne),et.has("WEBGL_multisampled_render_to_texture")===!1){let Te=!1;for(let ze=0,Ke=T.length;ze<Ke;ze++){let st=T[ze],{object:_t,geometry:Pt,material:Ne,group:Ct}=st;if(Ne.side===Wn&&_t.layers.test(U.layers)){let We=Ne.side;Ne.side=Zt,Ne.needsUpdate=!0,Yi(_t,P,U,Pt,Ne,Ct),Ne.side=We,Ne.needsUpdate=!0,Te=!0}}Te===!0&&(oe.updateMultisampleRenderTarget(ne),oe.updateRenderTargetMipmap(ne))}O.setRenderTarget(k,pe,ge),O.setClearColor(it,Ve),Re!==void 0&&(U.viewport=Re),O.toneMapping=xe}function Fn(m,T,P){let U=T.isScene===!0?T.overrideMaterial:null;for(let N=0,ne=m.length;N<ne;N++){let he=m[N],{object:k,geometry:pe,group:ge}=he,xe=he.material;xe.allowOverride===!0&&U!==null&&(xe=U),k.layers.test(P.layers)&&Yi(k,T,P,pe,xe,ge)}}function Yi(m,T,P,U,N,ne){q!==null&&N.isNodeMaterial&&q.setObject(m,N),m.onBeforeRender(O,T,P,U,N,ne),m.modelViewMatrix.multiplyMatrices(P.matrixWorldInverse,m.matrixWorld),m.normalMatrix.getNormalMatrix(m.modelViewMatrix),N.onBeforeRender(O,T,P,U,m,ne),N.transparent===!0&&N.side===Wn&&N.forceSinglePass===!1?(N.side=Zt,N.needsUpdate=!0,O.renderBufferDirect(P,T,U,N,m,ne),N.side=yi,N.needsUpdate=!0,O.renderBufferDirect(P,T,U,N,m,ne),N.side=Wn):O.renderBufferDirect(P,T,U,N,m,ne),m.onAfterRender(O,T,P,U,N,ne)}function ai(m,T,P){T.isScene!==!0&&(T=Lt);let U=K.get(m),N=E.state.lights,ne=E.state.shadowsArray,he=N.state.version,k=ie.getParameters(m,N.state,ne,T,P,E.state.lightProbeGridArray),pe=ie.getProgramCacheKey(k),ge=U.programs;U.environment=m.isMeshStandardMaterial||m.isMeshLambertMaterial||m.isMeshPhongMaterial?T.environment:null,U.fog=T.fog;let xe=m.isMeshStandardMaterial||m.isMeshLambertMaterial&&!m.envMap||m.isMeshPhongMaterial&&!m.envMap;U.envMap=be.get(m.envMap||U.environment,xe),U.envMapRotation=U.environment!==null&&m.envMap===null?T.environmentRotation:m.envMapRotation,ge===void 0&&(m.addEventListener("dispose",gn),ge=new Map,U.programs=ge);let Re=ge.get(pe);if(Re!==void 0){if(U.currentProgram===Re&&U.lightsStateVersion===he)return Qr(m,k),Re}else k.uniforms=ie.getUniforms(m),q!==null&&m.isNodeMaterial&&q.build(m,P,k),m.onBeforeCompile(k,O),Re=ie.acquireProgram(k,pe),ge.set(pe,Re),U.uniforms=k.uniforms;let Te=U.uniforms;return(!m.isShaderMaterial&&!m.isRawShaderMaterial||m.clipping===!0)&&(Te.clippingPlanes=ye.uniform),Qr(m,k),U.needsLights=b(m),U.lightsStateVersion=he,U.needsLights&&(Te.ambientLightColor.value=N.state.ambient,Te.lightProbe.value=N.state.probe,Te.sunLights.value=N.state.sun,Te.sunLightShadows.value=N.state.sunShadow,Te.directionalLights.value=N.state.directional,Te.directionalLightShadows.value=N.state.directionalShadow,Te.spotLights.value=N.state.spot,Te.spotLightShadows.value=N.state.spotShadow,Te.rectAreaLights.value=N.state.rectArea,Te.ltc_1.value=N.state.rectAreaLTC1,Te.ltc_2.value=N.state.rectAreaLTC2,Te.pointLights.value=N.state.point,Te.pointLightShadows.value=N.state.pointShadow,Te.hemisphereLights.value=N.state.hemi,Te.sunShadowMatrix.value=N.state.sunShadowMatrix,Te.sunShadowCascade.value=N.state.sunShadowCascade,Te.directionalShadowMatrix.value=N.state.directionalShadowMatrix,Te.spotLightMatrix.value=N.state.spotLightMatrix,Te.spotLightMap.value=N.state.spotLightMap,Te.pointShadowMatrix.value=N.state.pointShadowMatrix),U.lightProbeGrid=E.state.lightProbeGridArray.length>0,U.currentProgram=Re,U.uniformsList=null,Re}function Zi(m){if(m.uniformsList===null){let T=m.currentProgram.getUniforms();m.uniformsList=Ds.seqWithValue(T.seq,m.uniforms)}return m.uniformsList}function Qr(m,T){let P=K.get(m);P.outputColorSpace=T.outputColorSpace,P.batching=T.batching,P.batchingColor=T.batchingColor,P.instancing=T.instancing,P.instancingColor=T.instancingColor,P.instancingMorph=T.instancingMorph,P.skinning=T.skinning,P.morphTargets=T.morphTargets,P.morphNormals=T.morphNormals,P.morphColors=T.morphColors,P.morphTargetsCount=T.morphTargetsCount,P.numClippingPlanes=T.numClippingPlanes,P.numIntersection=T.numClipIntersection,P.vertexAlphas=T.vertexAlphas,P.vertexTangents=T.vertexTangents,P.toneMapping=T.toneMapping}function oi(m,T){if(m.length===0)return null;if(m.length===1)return m[0].texture!==null?m[0]:null;y.setFromMatrixPosition(T.matrixWorld);for(let P=0,U=m.length;P<U;P++){let N=m[P];if(N.texture!==null&&N.boundingBox.containsPoint(y))return N}return null}function M(m,T,P,U,N){T.isScene!==!0&&(T=Lt),oe.resetTextureUnits();let ne=T.fog,he=U.isMeshStandardMaterial||U.isMeshLambertMaterial||U.isMeshPhongMaterial?T.environment:null,k=Z===null?O.outputColorSpace:Z.isXRRenderTarget===!0?Z.texture.colorSpace:at.workingColorSpace,pe=U.isMeshStandardMaterial||U.isMeshLambertMaterial&&!U.envMap||U.isMeshPhongMaterial&&!U.envMap,ge=be.get(U.envMap||he,pe),xe=U.vertexColors===!0&&!!P.attributes.color&&P.attributes.color.itemSize===4,Re=!!P.attributes.tangent&&(!!U.normalMap||U.anisotropy>0),Te=!!P.morphAttributes.position,ze=!!P.morphAttributes.normal,Ke=!!P.morphAttributes.color,st=Dn;U.toneMapped&&(Z===null||Z.isXRRenderTarget===!0)&&(st=O.toneMapping);let _t=P.morphAttributes.position||P.morphAttributes.normal||P.morphAttributes.color,Pt=_t!==void 0?_t.length:0,Ne=K.get(U),Ct=E.state.lights;if(Qe===!0&&(ht===!0||m!==le)){let Mt=m===le&&U.id===Q;ye.setState(U,m,Mt)}let We=!1;U.version===Ne.__version?(Ne.needsLights&&Ne.lightsStateVersion!==Ct.state.version||Ne.outputColorSpace!==k||N.isBatchedMesh&&Ne.batching===!1||!N.isBatchedMesh&&Ne.batching===!0||N.isBatchedMesh&&Ne.batchingColor===!0&&N._colorsTexture===null||N.isBatchedMesh&&Ne.batchingColor===!1&&N._colorsTexture!==null||N.isInstancedMesh&&Ne.instancing===!1||!N.isInstancedMesh&&Ne.instancing===!0||N.isSkinnedMesh&&Ne.skinning===!1||!N.isSkinnedMesh&&Ne.skinning===!0||N.isInstancedMesh&&Ne.instancingColor===!0&&N.instanceColor===null||N.isInstancedMesh&&Ne.instancingColor===!1&&N.instanceColor!==null||N.isInstancedMesh&&Ne.instancingMorph===!0&&N.morphTexture===null||N.isInstancedMesh&&Ne.instancingMorph===!1&&N.morphTexture!==null||Ne.envMap!==ge||U.fog===!0&&Ne.fog!==ne||Ne.numClippingPlanes!==void 0&&(Ne.numClippingPlanes!==ye.numPlanes||Ne.numIntersection!==ye.numIntersection)||Ne.vertexAlphas!==xe||Ne.vertexTangents!==Re||Ne.morphTargets!==Te||Ne.morphNormals!==ze||Ne.morphColors!==Ke||Ne.toneMapping!==st||Ne.morphTargetsCount!==Pt||!!Ne.lightProbeGrid!=E.state.lightProbeGridArray.length>0)&&(We=!0):(We=!0,Ne.__version=U.version);let Rt=Ne.currentProgram;We===!0&&(Rt=ai(U,T,N),q&&U.isNodeMaterial&&q.onUpdateProgram(U,Rt,Ne));let Vt=!1,en=!1,En=!1,vt=Rt.getUniforms(),ke=Ne.uniforms;if(x.useProgram(Rt.program)&&(Vt=!0,en=!0,En=!0),U.id!==Q&&(Q=U.id,en=!0),Ne.needsLights){let Mt=oi(E.state.lightProbeGridArray,N);Ne.lightProbeGrid!==Mt&&(Ne.lightProbeGrid=Mt,en=!0)}if(Vt||le!==m){x.buffers.depth.getReversed()&&m.reversedDepth!==!0&&(m._reversedDepth=!0,m.updateProjectionMatrix()),vt.setValue(W,"projectionMatrix",m.projectionMatrix),vt.setValue(W,"viewMatrix",m.matrixWorldInverse);let wn=vt.map.cameraPosition;wn!==void 0&&wn.setValue(W,ft.setFromMatrixPosition(m.matrixWorld)),L.logarithmicDepthBuffer&&vt.setValue(W,"logDepthBufFC",2/(Math.log(m.far+1)/Math.LN2)),(U.isMeshPhongMaterial||U.isMeshToonMaterial||U.isMeshLambertMaterial||U.isMeshBasicMaterial||U.isMeshStandardMaterial||U.isShaderMaterial)&&vt.setValue(W,"isOrthographic",m.isOrthographicCamera===!0),le!==m&&(le=m,en=!0,En=!0)}if(Ne.needsLights&&(Ct.state.sunShadowMap.length>0&&vt.setValue(W,"sunShadowMap",Ct.state.sunShadowMap,oe),Ct.state.directionalShadowMap.length>0&&vt.setValue(W,"directionalShadowMap",Ct.state.directionalShadowMap,oe),Ct.state.spotShadowMap.length>0&&vt.setValue(W,"spotShadowMap",Ct.state.spotShadowMap,oe),Ct.state.pointShadowMap.length>0&&vt.setValue(W,"pointShadowMap",Ct.state.pointShadowMap,oe)),N.isSkinnedMesh){vt.setOptional(W,N,"bindMatrix"),vt.setOptional(W,N,"bindMatrixInverse");let Mt=N.skeleton;Mt&&(Mt.boneTexture===null&&Mt.computeBoneTexture(),vt.setValue(W,"boneTexture",Mt.boneTexture,oe))}N.isBatchedMesh&&(vt.setOptional(W,N,"batchingTexture"),vt.setValue(W,"batchingTexture",N._matricesTexture,oe),vt.setOptional(W,N,"batchingIdTexture"),vt.setValue(W,"batchingIdTexture",N._indirectTexture,oe),vt.setOptional(W,N,"batchingColorTexture"),N._colorsTexture!==null&&vt.setValue(W,"batchingColorTexture",N._colorsTexture,oe));let dt=P.morphAttributes;if((dt.position!==void 0||dt.normal!==void 0||dt.color!==void 0)&&H.update(N,P,Rt),(en||Ne.receiveShadow!==N.receiveShadow)&&(Ne.receiveShadow=N.receiveShadow,vt.setValue(W,"receiveShadow",N.receiveShadow)),(U.isMeshStandardMaterial||U.isMeshLambertMaterial||U.isMeshPhongMaterial)&&U.envMap===null&&T.environment!==null&&(ke.envMapIntensity.value=T.environmentIntensity),ke.dfgLUT!==void 0&&(ke.dfgLUT.value=K0()),en){if(vt.setValue(W,"toneMappingExposure",O.toneMappingExposure),Ne.needsLights&&R(ke,En),ne&&U.fog===!0&&me.refreshFogUniforms(ke,ne),me.refreshMaterialUniforms(ke,U,ae,ee,E.state.transmissionRenderTarget[m.id]),Ne.needsLights&&Ne.lightProbeGrid){let Mt=Ne.lightProbeGrid;ke.probesSH.value=Mt.texture,ke.probesMin.value.copy(Mt.boundingBox.min),ke.probesMax.value.copy(Mt.boundingBox.max),ke.probesResolution.value.copy(Mt.resolution)}Ds.upload(W,Zi(Ne),ke,oe)}if(U.isShaderMaterial&&U.uniformsNeedUpdate===!0&&(Ds.upload(W,Zi(Ne),ke,oe),U.uniformsNeedUpdate=!1),U.isSpriteMaterial&&vt.setValue(W,"center",N.center),vt.setValue(W,"modelViewMatrix",N.modelViewMatrix),vt.setValue(W,"normalMatrix",N.normalMatrix),vt.setValue(W,"modelMatrix",N.matrixWorld),U.uniformsGroups!==void 0){let Mt=U.uniformsGroups;for(let wn=0,li=Mt.length;wn<li;wn++){let ji=Mt[wn];de.update(ji,Rt),de.bind(ji,Rt)}}return Rt}function R(m,T){m.ambientLightColor.needsUpdate=T,m.lightProbe.needsUpdate=T,m.sunLights.needsUpdate=T,m.sunLightShadows.needsUpdate=T,m.directionalLights.needsUpdate=T,m.directionalLightShadows.needsUpdate=T,m.pointLights.needsUpdate=T,m.pointLightShadows.needsUpdate=T,m.spotLights.needsUpdate=T,m.spotLightShadows.needsUpdate=T,m.rectAreaLights.needsUpdate=T,m.hemisphereLights.needsUpdate=T}function b(m){return m.isMeshLambertMaterial||m.isMeshToonMaterial||m.isMeshPhongMaterial||m.isMeshStandardMaterial||m.isShadowMaterial||m.isShaderMaterial&&m.lights===!0}this.getActiveCubeFace=function(){return te},this.getActiveMipmapLevel=function(){return re},this.getRenderTarget=function(){return Z},this.setRenderTargetTextures=function(m,T,P){let U=K.get(m);U.__autoAllocateDepthBuffer=m.resolveDepthBuffer===!1,U.__autoAllocateDepthBuffer===!1&&(U.__useRenderToTexture=!1),K.get(m.texture).__webglTexture=T,K.get(m.depthTexture).__webglTexture=U.__autoAllocateDepthBuffer?void 0:P,U.__hasExternalTextures=!0},this.setRenderTargetFramebuffer=function(m,T){let P=K.get(m);P.__webglFramebuffer=T,P.__useDefaultFramebuffer=T===void 0},this.setRenderTarget=function(m,T=0,P=0){Z=m,te=T,re=P;let U=null,N=!1,ne=!1;if(m){let k=K.get(m);if(k.__useDefaultFramebuffer!==void 0){x.bindFramebuffer(W.FRAMEBUFFER,k.__webglFramebuffer),se.copy(m.viewport),Oe.copy(m.scissor),Ie=m.scissorTest,x.viewport(se),x.scissor(Oe),x.setScissorTest(Ie),Q=-1;return}else if(k.__webglFramebuffer===void 0)oe.setupRenderTarget(m);else if(k.__hasExternalTextures)oe.rebindTextures(m,K.get(m.texture).__webglTexture,K.get(m.depthTexture).__webglTexture);else if(m.depthBuffer){let xe=m.depthTexture;if(k.__boundDepthTexture!==xe){if(xe!==null&&K.has(xe)&&(m.width!==xe.image.width||m.height!==xe.image.height))throw new Error("THREE.WebGLRenderer: Attached DepthTexture is initialized to the incorrect size.");oe.setupDepthRenderbuffer(m)}}let pe=m.texture;(pe.isData3DTexture||pe.isDataArrayTexture||pe.isCompressedArrayTexture)&&(ne=!0);let ge=K.get(m).__webglFramebuffer;m.isWebGLCubeRenderTarget?(Array.isArray(ge[T])?U=ge[T][P]:U=ge[T],N=!0):m.samples>0&&oe.useMultisampledRTT(m)===!1?U=K.get(m).__webglMultisampledFramebuffer:Array.isArray(ge)?U=ge[P]:U=ge,se.copy(m.viewport),Oe.copy(m.scissor),Ie=m.scissorTest}else se.copy(we).multiplyScalar(ae).floor(),Oe.copy(Ge).multiplyScalar(ae).floor(),Ie=je;if(P!==0&&(U=j),x.bindFramebuffer(W.FRAMEBUFFER,U)&&x.drawBuffers(m,U),x.viewport(se),x.scissor(Oe),x.setScissorTest(Ie),N){let k=K.get(m.texture);W.framebufferTexture2D(W.FRAMEBUFFER,W.COLOR_ATTACHMENT0,W.TEXTURE_CUBE_MAP_POSITIVE_X+T,k.__webglTexture,P)}else if(ne){let k=T;for(let pe=0;pe<m.textures.length;pe++){let ge=K.get(m.textures[pe]);W.framebufferTextureLayer(W.FRAMEBUFFER,W.COLOR_ATTACHMENT0+pe,ge.__webglTexture,P,k)}}else if(m!==null&&P!==0){let k=K.get(m.texture);W.framebufferTexture2D(W.FRAMEBUFFER,W.COLOR_ATTACHMENT0,W.TEXTURE_2D,k.__webglTexture,P)}Q=-1};function G(m){let T=K.get(m);return(T.__readFormat!==m.format||T.__readType!==m.type)&&(T.__readFormat=m.format,T.__readType=m.type,T.__formatReadable=L.textureFormatReadable(m.format),T.__typeReadable=L.textureTypeReadable(m.type)),T}this.readRenderTargetPixels=function(m,T,P,U,N,ne,he,k=0){if(!(m&&m.isWebGLRenderTarget)){Xe("WebGLRenderer.readRenderTargetPixels: renderTarget is not THREE.WebGLRenderTarget.");return}let pe=K.get(m).__webglFramebuffer;if(m.isWebGLCubeRenderTarget&&he!==void 0&&(pe=pe[he]),pe){x.bindFramebuffer(W.FRAMEBUFFER,pe);try{let ge=m.textures[k],xe=ge.format,Re=ge.type;m.textures.length>1&&W.readBuffer(W.COLOR_ATTACHMENT0+k);let Te=G(ge);if(Te.__formatReadable===!1){Xe("WebGLRenderer.readRenderTargetPixels: renderTarget is not in RGBA or implementation defined format.");return}if(Te.__typeReadable===!1){Xe("WebGLRenderer.readRenderTargetPixels: renderTarget is not in UnsignedByteType or implementation defined type.");return}T>=0&&T<=m.width-U&&P>=0&&P<=m.height-N&&W.readPixels(T,P,U,N,ve.convert(xe),ve.convert(Re),ne)}finally{let ge=Z!==null?K.get(Z).__webglFramebuffer:null;x.bindFramebuffer(W.FRAMEBUFFER,ge)}}},this.readRenderTargetPixelsAsync=async function(m,T,P,U,N,ne,he,k=0){if(!(m&&m.isWebGLRenderTarget))throw new Error("THREE.WebGLRenderer.readRenderTargetPixels: renderTarget is not THREE.WebGLRenderTarget.");let pe=K.get(m).__webglFramebuffer;if(m.isWebGLCubeRenderTarget&&he!==void 0&&(pe=pe[he]),pe)if(T>=0&&T<=m.width-U&&P>=0&&P<=m.height-N){x.bindFramebuffer(W.FRAMEBUFFER,pe);let ge=m.textures[k],xe=ge.format,Re=ge.type;m.textures.length>1&&W.readBuffer(W.COLOR_ATTACHMENT0+k);let Te=G(ge);if(Te.__formatReadable===!1)throw new Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: renderTarget is not in RGBA or implementation defined format.");if(Te.__typeReadable===!1)throw new Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: renderTarget is not in UnsignedByteType or implementation defined type.");let ze=W.createBuffer();W.bindBuffer(W.PIXEL_PACK_BUFFER,ze),W.bufferData(W.PIXEL_PACK_BUFFER,ne.byteLength,W.STREAM_READ),W.readPixels(T,P,U,N,ve.convert(xe),ve.convert(Re),0),W.bindBuffer(W.PIXEL_PACK_BUFFER,null);let Ke=Z!==null?K.get(Z).__webglFramebuffer:null;x.bindFramebuffer(W.FRAMEBUFFER,Ke);let st=W.fenceSync(W.SYNC_GPU_COMMANDS_COMPLETE,0);return W.flush(),await rh(W,st,4),W.bindBuffer(W.PIXEL_PACK_BUFFER,ze),W.getBufferSubData(W.PIXEL_PACK_BUFFER,0,ne),W.bindBuffer(W.PIXEL_PACK_BUFFER,null),W.deleteBuffer(ze),W.deleteSync(st),ne}else throw new Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: requested read bounds are out of range.")},this.copyFramebufferToTexture=function(m,T=null,P=0){let U=Math.pow(2,-P),N=Math.floor(m.image.width*U),ne=Math.floor(m.image.height*U),he=T!==null?T.x:0,k=T!==null?T.y:0;oe.setTexture2D(m,0),W.copyTexSubImage2D(W.TEXTURE_2D,P,0,0,he,k,N,ne),x.unbindTexture()},this.copyTextureToTexture=function(m,T,P=null,U=null,N=0,ne=0){let he,k,pe,ge,xe,Re,Te,ze,Ke,st=m.isCompressedTexture?m.mipmaps[ne]:m.image;if(P!==null)he=P.max.x-P.min.x,k=P.max.y-P.min.y,pe=P.isBox3?P.max.z-P.min.z:1,ge=P.min.x,xe=P.min.y,Re=P.isBox3?P.min.z:0;else{let ke=Math.pow(2,-N);he=Math.floor(st.width*ke),k=Math.floor(st.height*ke),m.isDataArrayTexture?pe=st.depth:m.isData3DTexture?pe=Math.floor(st.depth*ke):pe=1,ge=0,xe=0,Re=0}U!==null?(Te=U.x,ze=U.y,Ke=U.z):(Te=0,ze=0,Ke=0);let _t=ve.convert(T.format),Pt=ve.convert(T.type),Ne;T.isData3DTexture?(oe.setTexture3D(T,0),Ne=W.TEXTURE_3D):T.isDataArrayTexture||T.isCompressedArrayTexture?(oe.setTexture2DArray(T,0),Ne=W.TEXTURE_2D_ARRAY):(oe.setTexture2D(T,0),Ne=W.TEXTURE_2D),x.activeTexture(W.TEXTURE0),x.pixelStorei(W.UNPACK_FLIP_Y_WEBGL,T.flipY),x.pixelStorei(W.UNPACK_PREMULTIPLY_ALPHA_WEBGL,T.premultiplyAlpha),x.pixelStorei(W.UNPACK_ALIGNMENT,T.unpackAlignment);let Ct=x.getParameter(W.UNPACK_ROW_LENGTH),We=x.getParameter(W.UNPACK_IMAGE_HEIGHT),Rt=x.getParameter(W.UNPACK_SKIP_PIXELS),Vt=x.getParameter(W.UNPACK_SKIP_ROWS),en=x.getParameter(W.UNPACK_SKIP_IMAGES);x.pixelStorei(W.UNPACK_ROW_LENGTH,st.width),x.pixelStorei(W.UNPACK_IMAGE_HEIGHT,st.height),x.pixelStorei(W.UNPACK_SKIP_PIXELS,ge),x.pixelStorei(W.UNPACK_SKIP_ROWS,xe),x.pixelStorei(W.UNPACK_SKIP_IMAGES,Re);let En=m.isDataArrayTexture||m.isData3DTexture,vt=T.isDataArrayTexture||T.isData3DTexture;if(m.isDepthTexture){let ke=K.get(m),dt=K.get(T),Mt=K.get(ke.__renderTarget),wn=K.get(dt.__renderTarget);x.bindFramebuffer(W.READ_FRAMEBUFFER,Mt.__webglFramebuffer),x.bindFramebuffer(W.DRAW_FRAMEBUFFER,wn.__webglFramebuffer);for(let li=0;li<pe;li++)En&&(W.framebufferTextureLayer(W.READ_FRAMEBUFFER,W.COLOR_ATTACHMENT0,K.get(m).__webglTexture,N,Re+li),W.framebufferTextureLayer(W.DRAW_FRAMEBUFFER,W.COLOR_ATTACHMENT0,K.get(T).__webglTexture,ne,Ke+li)),W.blitFramebuffer(ge,xe,he,k,Te,ze,he,k,W.DEPTH_BUFFER_BIT,W.NEAREST);x.bindFramebuffer(W.READ_FRAMEBUFFER,null),x.bindFramebuffer(W.DRAW_FRAMEBUFFER,null)}else if(N!==0||m.isRenderTargetTexture||K.has(m)){let ke=K.get(m),dt=K.get(T);x.bindFramebuffer(W.READ_FRAMEBUFFER,z),x.bindFramebuffer(W.DRAW_FRAMEBUFFER,Y);for(let Mt=0;Mt<pe;Mt++)En?W.framebufferTextureLayer(W.READ_FRAMEBUFFER,W.COLOR_ATTACHMENT0,ke.__webglTexture,N,Re+Mt):W.framebufferTexture2D(W.READ_FRAMEBUFFER,W.COLOR_ATTACHMENT0,W.TEXTURE_2D,ke.__webglTexture,N),vt?W.framebufferTextureLayer(W.DRAW_FRAMEBUFFER,W.COLOR_ATTACHMENT0,dt.__webglTexture,ne,Ke+Mt):W.framebufferTexture2D(W.DRAW_FRAMEBUFFER,W.COLOR_ATTACHMENT0,W.TEXTURE_2D,dt.__webglTexture,ne),N!==0?W.blitFramebuffer(ge,xe,he,k,Te,ze,he,k,W.COLOR_BUFFER_BIT,W.NEAREST):vt?W.copyTexSubImage3D(Ne,ne,Te,ze,Ke+Mt,ge,xe,he,k):W.copyTexSubImage2D(Ne,ne,Te,ze,ge,xe,he,k);x.bindFramebuffer(W.READ_FRAMEBUFFER,null),x.bindFramebuffer(W.DRAW_FRAMEBUFFER,null)}else vt?m.isDataTexture||m.isData3DTexture?W.texSubImage3D(Ne,ne,Te,ze,Ke,he,k,pe,_t,Pt,st.data):T.isCompressedArrayTexture?W.compressedTexSubImage3D(Ne,ne,Te,ze,Ke,he,k,pe,_t,st.data):W.texSubImage3D(Ne,ne,Te,ze,Ke,he,k,pe,_t,Pt,st):m.isDataTexture?W.texSubImage2D(W.TEXTURE_2D,ne,Te,ze,he,k,_t,Pt,st.data):m.isCompressedTexture?W.compressedTexSubImage2D(W.TEXTURE_2D,ne,Te,ze,st.width,st.height,_t,st.data):W.texSubImage2D(W.TEXTURE_2D,ne,Te,ze,he,k,_t,Pt,st);x.pixelStorei(W.UNPACK_ROW_LENGTH,Ct),x.pixelStorei(W.UNPACK_IMAGE_HEIGHT,We),x.pixelStorei(W.UNPACK_SKIP_PIXELS,Rt),x.pixelStorei(W.UNPACK_SKIP_ROWS,Vt),x.pixelStorei(W.UNPACK_SKIP_IMAGES,en),ne===0&&T.generateMipmaps&&W.generateMipmap(Ne),x.unbindTexture()},this.initRenderTarget=function(m){K.get(m).__webglFramebuffer===void 0&&oe.setupRenderTarget(m)},this.initTexture=function(m){m.isCubeTexture?oe.setTextureCube(m,0):m.isData3DTexture?oe.setTexture3D(m,0):m.isDataArrayTexture||m.isCompressedArrayTexture?oe.setTexture2DArray(m,0):oe.setTexture2D(m,0),x.unbindTexture()},this.resetState=function(){te=0,re=0,Z=null,x.reset(),Ce.reset()},typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("observe",{detail:this}))}get coordinateSystem(){return Pn}get outputColorSpace(){return this._outputColorSpace}set outputColorSpace(e){this._outputColorSpace=e;let t=this.getContext();t.drawingBufferColorSpace=at._getDrawingBufferColorSpace(e),t.unpackColorSpace=at._getUnpackColorSpace()}};var ks={name:"CopyShader",uniforms:{tDiffuse:{value:null},opacity:{value:1}},vertexShader:`

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


		}`};var mn=class{constructor(){this.isPass=!0,this.enabled=!0,this.needsSwap=!0,this.clear=!1,this.renderToScreen=!1}setSize(){}render(){console.error("THREE.Pass: .render() must be implemented in derived pass.")}dispose(){}},Q0=new vi(-1,1,1,-1,0,1),Bc=class extends St{constructor(){super(),this.setAttribute("position",new pt([-1,3,0,-1,-1,0,3,-1,0],3)),this.setAttribute("uv",new pt([0,2,0,0,2,0],2))}},e_=new Bc,Ei=class{constructor(e){this._mesh=new mt(e_,e)}dispose(){this._mesh.geometry.dispose()}render(e){e.render(this._mesh,Q0)}get material(){return this._mesh.material}set material(e){this._mesh.material=e}};var ll=class extends mn{constructor(e,t="tDiffuse"){super(),this.textureID=t,this.uniforms=null,this.material=null,e instanceof Nt?(this.uniforms=e.uniforms,this.material=e):e&&(this.uniforms=ni.clone(e.uniforms),this.material=new Nt({name:e.name!==void 0?e.name:"unspecified",defines:Object.assign({},e.defines),uniforms:this.uniforms,vertexShader:e.vertexShader,fragmentShader:e.fragmentShader})),this._fsQuad=new Ei(this.material)}render(e,t,n){this.uniforms[this.textureID]&&(this.uniforms[this.textureID].value=n.texture),this._fsQuad.material=this.material,this.renderToScreen?(e.setRenderTarget(null),this._fsQuad.render(e)):(e.setRenderTarget(t),this.clear&&e.clear(e.autoClearColor,e.autoClearDepth,e.autoClearStencil),this._fsQuad.render(e))}dispose(){this.material.dispose(),this._fsQuad.dispose()}};var qr=class extends mn{constructor(e,t){super(),this.scene=e,this.camera=t,this.clear=!0,this.needsSwap=!1,this.inverse=!1}render(e,t,n){let s=e.getContext(),r=e.state;r.buffers.color.setMask(!1),r.buffers.depth.setMask(!1),r.buffers.color.setLocked(!0),r.buffers.depth.setLocked(!0);let a,o;this.inverse?(a=0,o=1):(a=1,o=0),r.buffers.stencil.setTest(!0),r.buffers.stencil.setOp(s.REPLACE,s.REPLACE,s.REPLACE),r.buffers.stencil.setFunc(s.ALWAYS,a,4294967295),r.buffers.stencil.setClear(o),r.buffers.stencil.setLocked(!0),e.setRenderTarget(n),this.clear&&e.clear(),e.render(this.scene,this.camera),e.setRenderTarget(t),this.clear&&e.clear(),e.render(this.scene,this.camera),r.buffers.color.setLocked(!1),r.buffers.depth.setLocked(!1),r.buffers.color.setMask(!0),r.buffers.depth.setMask(!0),r.buffers.stencil.setLocked(!1),r.buffers.stencil.setFunc(s.EQUAL,1,4294967295),r.buffers.stencil.setOp(s.KEEP,s.KEEP,s.KEEP),r.buffers.stencil.setLocked(!0)}},cl=class extends mn{constructor(){super(),this.needsSwap=!1}render(e){e.state.buffers.stencil.setLocked(!1),e.state.buffers.stencil.setTest(!1)}};var ul=class{constructor(e,t){if(this.renderer=e,this._pixelRatio=e.getPixelRatio(),t===void 0){let n=e.getSize(new De);this._width=n.width,this._height=n.height,t=new Ft(this._width*this._pixelRatio,this._height*this._pixelRatio,{type:jt}),t.texture.name="EffectComposer.rt1"}else this._width=t.width,this._height=t.height;this.renderTarget1=t,this.renderTarget2=t.clone(),this.renderTarget2.texture.name="EffectComposer.rt2",this.writeBuffer=this.renderTarget1,this.readBuffer=this.renderTarget2,this.renderToScreen=!0,this.passes=[],this.copyPass=new ll(ks),this.copyPass.material.blending=Mn,this.timer=new Er}swapBuffers(){let e=this.readBuffer;this.readBuffer=this.writeBuffer,this.writeBuffer=e}addPass(e){this.passes.push(e),e.setSize(this._width*this._pixelRatio,this._height*this._pixelRatio)}insertPass(e,t){this.passes.splice(t,0,e),e.setSize(this._width*this._pixelRatio,this._height*this._pixelRatio)}removePass(e){let t=this.passes.indexOf(e);t!==-1&&this.passes.splice(t,1)}isLastEnabledPass(e){for(let t=e+1;t<this.passes.length;t++)if(this.passes[t].enabled)return!1;return!0}render(e){this.timer.update(),e===void 0&&(e=this.timer.getDelta());let t=this.renderer.getRenderTarget(),n=!1;for(let s=0,r=this.passes.length;s<r;s++){let a=this.passes[s];if(a.enabled!==!1){if(a.renderToScreen=this.renderToScreen&&this.isLastEnabledPass(s),a.render(this.renderer,this.writeBuffer,this.readBuffer,e,n),a.needsSwap){if(n){let o=this.renderer.getContext(),l=this.renderer.state.buffers.stencil;l.setFunc(o.NOTEQUAL,1,4294967295),this.copyPass.render(this.renderer,this.writeBuffer,this.readBuffer,e),l.setFunc(o.EQUAL,1,4294967295)}this.swapBuffers()}qr!==void 0&&(a instanceof qr?n=!0:a instanceof cl&&(n=!1))}}this.renderer.setRenderTarget(t)}reset(e){if(e===void 0){let t=this.renderer.getSize(new De);this._pixelRatio=this.renderer.getPixelRatio(),this._width=t.width,this._height=t.height,e=this.renderTarget1.clone(),e.setSize(this._width*this._pixelRatio,this._height*this._pixelRatio)}this.renderTarget1.dispose(),this.renderTarget2.dispose(),this.renderTarget1=e,this.renderTarget2=e.clone(),this.writeBuffer=this.renderTarget1,this.readBuffer=this.renderTarget2}setSize(e,t){this._width=e,this._height=t;let n=this._width*this._pixelRatio,s=this._height*this._pixelRatio;this.renderTarget1.setSize(n,s),this.renderTarget2.setSize(n,s);for(let r=0;r<this.passes.length;r++)this.passes[r].setSize(n,s)}setPixelRatio(e){this._pixelRatio=e,this.setSize(this._width,this._height)}dispose(){this.renderTarget1.dispose(),this.renderTarget2.dispose(),this.copyPass.dispose()}};var hl=class extends mn{constructor(e,t,n=null,s=null,r=null){super(),this.scene=e,this.camera=t,this.overrideMaterial=n,this.clearColor=s,this.clearAlpha=r,this.clear=!0,this.clearDepth=!1,this.needsSwap=!1,this.isRenderPass=!0,this._oldClearColor=new qe}render(e,t,n){let s=e.autoClear;e.autoClear=!1;let r,a;this.overrideMaterial!==null&&(a=this.scene.overrideMaterial,this.scene.overrideMaterial=this.overrideMaterial),this.clearColor!==null&&(e.getClearColor(this._oldClearColor),e.setClearColor(this.clearColor,e.getClearAlpha())),this.clearAlpha!==null&&(r=e.getClearAlpha(),e.setClearAlpha(this.clearAlpha)),this.clearDepth==!0&&e.clearDepth(),e.setRenderTarget(this.renderToScreen?null:n),this.clear===!0&&e.clear(e.autoClearColor,e.autoClearDepth,e.autoClearStencil),e.render(this.scene,this.camera),this.clearColor!==null&&e.setClearColor(this._oldClearColor),this.clearAlpha!==null&&e.setClearAlpha(r),this.overrideMaterial!==null&&(this.scene.overrideMaterial=a),e.autoClear=s}};var Oh={name:"LuminosityHighPassShader",uniforms:{tDiffuse:{value:null},luminosityThreshold:{value:1},smoothWidth:{value:1},defaultColor:{value:new qe(0)},defaultOpacity:{value:0}},vertexShader:`

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

		}`};var Os=class i extends mn{constructor(e,t=1,n,s){super(),this.strength=t,this.radius=n,this.threshold=s,this.resolution=e!==void 0?new De(e.x,e.y):new De(256,256),this.clearColor=new qe(0,0,0),this.needsSwap=!1,this.renderTargetsHorizontal=[],this.renderTargetsVertical=[],this.nMips=5;let r=Math.round(this.resolution.x/2),a=Math.round(this.resolution.y/2);this.renderTargetBright=new Ft(r,a,{type:jt,depthBuffer:!1}),this.renderTargetBright.texture.name="UnrealBloomPass.bright",this.renderTargetBright.texture.generateMipmaps=!1;for(let h=0;h<this.nMips;h++){let f=new Ft(r,a,{type:jt,depthBuffer:!1});f.texture.name="UnrealBloomPass.h"+h,f.texture.generateMipmaps=!1,this.renderTargetsHorizontal.push(f);let u=new Ft(r,a,{type:jt,depthBuffer:!1});u.texture.name="UnrealBloomPass.v"+h,u.texture.generateMipmaps=!1,this.renderTargetsVertical.push(u),r=Math.round(r/2),a=Math.round(a/2)}let o=Oh;this.highPassUniforms=ni.clone(o.uniforms),this.highPassUniforms.luminosityThreshold.value=s,this.highPassUniforms.smoothWidth.value=.01,this.materialHighPassFilter=new Nt({uniforms:this.highPassUniforms,vertexShader:o.vertexShader,fragmentShader:o.fragmentShader}),this.separableBlurMaterials=[];let l=[6,10,14,18,22];r=Math.round(this.resolution.x/2),a=Math.round(this.resolution.y/2);for(let h=0;h<this.nMips;h++)this.separableBlurMaterials.push(this._getSeparableBlurMaterial(l[h])),this.separableBlurMaterials[h].uniforms.invSize.value=new De(1/r,1/a),r=Math.round(r/2),a=Math.round(a/2);this.compositeMaterial=this._getCompositeMaterial(this.nMips),this.compositeMaterial.uniforms.blurTexture1.value=this.renderTargetsVertical[0].texture,this.compositeMaterial.uniforms.blurTexture2.value=this.renderTargetsVertical[1].texture,this.compositeMaterial.uniforms.blurTexture3.value=this.renderTargetsVertical[2].texture,this.compositeMaterial.uniforms.blurTexture4.value=this.renderTargetsVertical[3].texture,this.compositeMaterial.uniforms.blurTexture5.value=this.renderTargetsVertical[4].texture,this.compositeMaterial.uniforms.bloomStrength.value=t,this.compositeMaterial.uniforms.bloomRadius.value=.1;let c=[1,.8,.6,.4,.2];this.compositeMaterial.uniforms.bloomFactors.value=c,this.bloomTintColors=[new B(1,1,1),new B(1,1,1),new B(1,1,1),new B(1,1,1),new B(1,1,1)],this.compositeMaterial.uniforms.bloomTintColors.value=this.bloomTintColors,this.copyUniforms=ni.clone(ks.uniforms),this.blendMaterial=new Nt({uniforms:this.copyUniforms,vertexShader:ks.vertexShader,fragmentShader:ks.fragmentShader,premultipliedAlpha:!0,blending:Bi,depthTest:!1,depthWrite:!1,transparent:!0}),this._oldClearColor=new qe,this._oldClearAlpha=1,this._basic=new sn,this._fsQuad=new Ei(null)}dispose(){for(let e=0;e<this.renderTargetsHorizontal.length;e++)this.renderTargetsHorizontal[e].dispose();for(let e=0;e<this.renderTargetsVertical.length;e++)this.renderTargetsVertical[e].dispose();this.renderTargetBright.dispose();for(let e=0;e<this.separableBlurMaterials.length;e++)this.separableBlurMaterials[e].dispose();this.compositeMaterial.dispose(),this.blendMaterial.dispose(),this._basic.dispose(),this._fsQuad.dispose()}setSize(e,t){let n=Math.round(e/2),s=Math.round(t/2);this.renderTargetBright.setSize(n,s);for(let r=0;r<this.nMips;r++)this.renderTargetsHorizontal[r].setSize(n,s),this.renderTargetsVertical[r].setSize(n,s),this.separableBlurMaterials[r].uniforms.invSize.value=new De(1/n,1/s),n=Math.round(n/2),s=Math.round(s/2)}render(e,t,n,s,r){e.getClearColor(this._oldClearColor),this._oldClearAlpha=e.getClearAlpha();let a=e.autoClear;e.autoClear=!1,e.setClearColor(this.clearColor,0),r&&e.state.buffers.stencil.setTest(!1),this.renderToScreen&&(this._fsQuad.material=this._basic,this._basic.map=n.texture,e.setRenderTarget(null),e.clear(),this._fsQuad.render(e)),this.highPassUniforms.tDiffuse.value=n.texture,this.highPassUniforms.luminosityThreshold.value=this.threshold,this._fsQuad.material=this.materialHighPassFilter,e.setRenderTarget(this.renderTargetBright),e.clear(),this._fsQuad.render(e);let o=this.renderTargetBright;for(let l=0;l<this.nMips;l++)this._fsQuad.material=this.separableBlurMaterials[l],this.separableBlurMaterials[l].uniforms.colorTexture.value=o.texture,this.separableBlurMaterials[l].uniforms.direction.value=i.BlurDirectionX,e.setRenderTarget(this.renderTargetsHorizontal[l]),e.clear(),this._fsQuad.render(e),this.separableBlurMaterials[l].uniforms.colorTexture.value=this.renderTargetsHorizontal[l].texture,this.separableBlurMaterials[l].uniforms.direction.value=i.BlurDirectionY,e.setRenderTarget(this.renderTargetsVertical[l]),e.clear(),this._fsQuad.render(e),o=this.renderTargetsVertical[l];this._fsQuad.material=this.compositeMaterial,this.compositeMaterial.uniforms.bloomStrength.value=this.strength,this.compositeMaterial.uniforms.bloomRadius.value=this.radius,this.compositeMaterial.uniforms.bloomTintColors.value=this.bloomTintColors,e.setRenderTarget(this.renderTargetsHorizontal[0]),e.clear(),this._fsQuad.render(e),this._fsQuad.material=this.blendMaterial,this.copyUniforms.tDiffuse.value=this.renderTargetsHorizontal[0].texture,r&&e.state.buffers.stencil.setTest(!0),this.renderToScreen?(e.setRenderTarget(null),this._fsQuad.render(e)):(e.setRenderTarget(n),this._fsQuad.render(e)),e.setClearColor(this._oldClearColor,this._oldClearAlpha),e.autoClear=a}_getSeparableBlurMaterial(e){let t=[],n=e/3;for(let a=0;a<e;a++)t.push(.39894*Math.exp(-.5*a*a/(n*n))/n);let s=[],r=[];for(let a=1;a<e;a+=2){let o=t[a],l=a+1<e?t[a+1]:0,c=o+l;s.push((a*o+(a+1)*l)/c),r.push(c)}return new Nt({defines:{KERNEL_PAIRS:s.length},uniforms:{colorTexture:{value:null},invSize:{value:new De(.5,.5)},direction:{value:new De(.5,.5)},centerWeight:{value:t[0]},gaussianOffsets:{value:s},gaussianWeights:{value:r}},vertexShader:`

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

				}`})}_getCompositeMaterial(e){return new Nt({defines:{NUM_MIPS:e},uniforms:{blurTexture1:{value:null},blurTexture2:{value:null},blurTexture3:{value:null},blurTexture4:{value:null},blurTexture5:{value:null},bloomStrength:{value:1},bloomFactors:{value:null},bloomTintColors:{value:null},bloomRadius:{value:0}},vertexShader:`

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

				}`})}};Os.BlurDirectionX=new De(1,0);Os.BlurDirectionY=new De(0,1);var Xr={name:"OutputShader",uniforms:{tDiffuse:{value:null},toneMappingExposure:{value:1}},vertexShader:`
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

		}`};var dl=class extends mn{constructor(){super(),this.isOutputPass=!0,this.uniforms=ni.clone(Xr.uniforms),this.material=new Es({name:Xr.name,uniforms:this.uniforms,vertexShader:Xr.vertexShader,fragmentShader:Xr.fragmentShader}),this._fsQuad=new Ei(this.material),this._outputColorSpace=null,this._toneMapping=null}render(e,t,n){this.uniforms.tDiffuse.value=n.texture,this.uniforms.toneMappingExposure.value=e.toneMappingExposure,(this._outputColorSpace!==e.outputColorSpace||this._toneMapping!==e.toneMapping)&&(this._outputColorSpace=e.outputColorSpace,this._toneMapping=e.toneMapping,this.material.defines={},at.getTransfer(this._outputColorSpace)===yt&&(this.material.defines.SRGB_TRANSFER=""),this._toneMapping===Cr?this.material.defines.LINEAR_TONE_MAPPING="":this._toneMapping===Rr?this.material.defines.REINHARD_TONE_MAPPING="":this._toneMapping===Ir?this.material.defines.CINEON_TONE_MAPPING="":this._toneMapping===Vi?this.material.defines.ACES_FILMIC_TONE_MAPPING="":this._toneMapping===Lr?this.material.defines.AGX_TONE_MAPPING="":this._toneMapping===Nr?this.material.defines.NEUTRAL_TONE_MAPPING="":this._toneMapping===Pr&&(this.material.defines.CUSTOM_TONE_MAPPING=""),this.material.needsUpdate=!0),this.renderToScreen===!0?(e.setRenderTarget(null),this._fsQuad.render(e)):(e.setRenderTarget(t),this.clear&&e.clear(e.autoClearColor,e.autoClearDepth,e.autoClearStencil),this._fsQuad.render(e))}dispose(){this.material.dispose(),this._fsQuad.dispose()}};var fl=class extends Di{constructor(){super(),this.name="RoomEnvironment",this.position.y=-3.5;let e=new Nn;e.deleteAttribute("uv");let t=new Wt({side:Zt}),n=new Wt,s=new ei(16777215,900,28,2);s.position.set(.418,16.199,.3),this.add(s);let r=new mt(e,t);r.position.set(-.757,13.219,.717),r.scale.set(31.713,28.305,28.591),this.add(r);let a=new ln(e,n,6),o=new kt;o.position.set(-10.906,2.009,1.846),o.rotation.set(0,-.195,0),o.scale.set(2.328,7.905,4.651),o.updateMatrix(),a.setMatrixAt(0,o.matrix),o.position.set(-5.607,-.754,-.758),o.rotation.set(0,.994,0),o.scale.set(1.97,1.534,3.955),o.updateMatrix(),a.setMatrixAt(1,o.matrix),o.position.set(6.167,.857,7.803),o.rotation.set(0,.561,0),o.scale.set(3.927,6.285,3.687),o.updateMatrix(),a.setMatrixAt(2,o.matrix),o.position.set(-2.017,.018,6.124),o.rotation.set(0,.333,0),o.scale.set(2.002,4.566,2.064),o.updateMatrix(),a.setMatrixAt(3,o.matrix),o.position.set(2.291,-.756,-2.621),o.rotation.set(0,-.286,0),o.scale.set(1.546,1.552,1.496),o.updateMatrix(),a.setMatrixAt(4,o.matrix),o.position.set(-2.193,-.369,-5.547),o.rotation.set(0,.516,0),o.scale.set(3.875,3.487,2.986),o.updateMatrix(),a.setMatrixAt(5,o.matrix),this.add(a);let l=new mt(e,Bs(50));l.position.set(-16.116,14.37,8.208),l.scale.set(.1,2.428,2.739),this.add(l);let c=new mt(e,Bs(50));c.position.set(-16.109,18.021,-8.207),c.scale.set(.1,2.425,2.751),this.add(c);let h=new mt(e,Bs(17));h.position.set(14.904,12.198,-1.832),h.scale.set(.15,4.265,6.331),this.add(h);let f=new mt(e,Bs(43));f.position.set(-.462,8.89,14.52),f.scale.set(4.38,5.441,.088),this.add(f);let u=new mt(e,Bs(20));u.position.set(3.235,11.486,-12.541),u.scale.set(2.5,2,.1),this.add(u);let d=new mt(e,Bs(100));d.position.set(0,20,0),d.scale.set(1,.1,1),this.add(d)}dispose(){let e=new Set;this.traverse(t=>{t.isMesh&&(e.add(t.geometry),e.add(t.material))});for(let t of e)t.dispose()}};function Bs(i){return new yr({color:0,emissive:16777215,emissiveIntensity:i})}var Bh={idle:{energy:.34,speed:.16,cyan:8314111,amber:15180363},receiving:{energy:.72,speed:.55,cyan:9169407,amber:16757851},working:{energy:1,speed:.92,cyan:10154751,amber:16760162},tool:{energy:.92,speed:1.12,cyan:8388572,amber:16761183},delegating:{energy:.88,speed:.82,cyan:7536592,amber:16756815},waiting_result:{energy:.48,speed:.28,cyan:7985407,amber:14064458},waiting_user:{energy:.76,speed:.34,cyan:16748405,amber:16738383},speaking:{energy:.7,speed:.74,cyan:9238751,amber:16762218},complete:{energy:.56,speed:.32,cyan:9041343,amber:16762733},error:{energy:.74,speed:.2,cyan:16744556,amber:16736072},offline:{energy:.12,speed:.04,cyan:5858923,amber:6706244}},zh=tl.clamp;function Vh({low:i=!1}={}){let e=new Ut;e.name="Reactive orchestration quantum core";let t=new Set,n=Z=>(t.add(Z),Z),s={transparent:!0,depthWrite:!1,blending:Bi},r=n(new Wt({color:16765065,emissive:16754237,emissiveIntensity:3.2,roughness:.28,metalness:.15,transparent:!0,opacity:.9})),a=new mt(n(new Ts(.48,i?2:4)),r);a.name="Energy nucleus",e.add(a);let o=n(new sn({color:10218239,wireframe:!0,opacity:.35,...s})),l=new mt(n(new Ts(.76,i?2:3)),o);l.name="Nucleus field cage",e.add(l);let c=new Ut;c.name="Concentric computation rings",e.add(c);let h=[],f=[],u=i?7:11;for(let Z=0;Z<u;Z++){let Q=1.05+Z*.19,le=n(new sn({color:Z%2?8710399:15773013,opacity:.16+Z%3*.035,...s}));h.push(le);let se=new mt(n(new bn(Q,.009+Z%3*.004,i?5:7,i?72:128)),le);se.rotation.set(Z%3*Math.PI/3+.16,Z*2%5*Math.PI/5,Z%4*.19),se.userData.phase=Z*.71,c.add(se),f.push(se)}let d=new Ut;d.name="Data orbit filaments",e.add(d);let _=[];for(let Z=0;Z<(i?7:12);Z++){let Q=[],le=i?90:150,se=1.32+Z%5*.29,Oe=.56+Z%4*.11;for(let He=0;He<=le;He++){let ee=He/le*Math.PI*2;Q.push(new B(Math.cos(ee)*se,Math.sin(ee)*se*Oe,Math.sin(ee*2+Z)*.16))}let Ie=n(new St().setFromPoints(Q)),it=n(new Qn({color:Z%3?9169663:16758621,opacity:Z%3?.2:.28,...s}));_.push(it);let Ve=new ur(Ie,it);Ve.rotation.set(Z*.39,Z*.51,Z*.23),Ve.userData.phase=Z*.64,d.add(Ve)}let S=1369948382,g=()=>(S=1664525*S+1013904223>>>0,S/4294967296),p=(Z,Q,le,se,Oe)=>{let Ie=new Float32Array(Z*3);for(let ee=0;ee<Z;ee++){let ae=g()*2-1,Me=g()*Math.PI*2,Pe=Q+(le-Q)*Math.pow(g(),.62),we=Math.sqrt(Math.max(0,1-ae*ae));Ie[ee*3]=Math.cos(Me)*we*Pe,Ie[ee*3+1]=ae*Pe,Ie[ee*3+2]=Math.sin(Me)*we*Pe}let it=n(new St);it.setAttribute("position",new Xt(Ie,3));let Ve=n(new bs({color:se,size:Oe,sizeAttenuation:!0,opacity:.72,...s})),He=new hr(it,Ve);return e.add(He),{points:He,material:Ve}},w=p(i?430:1050,.86,2.86,10219263,i?.025:.021),I=p(i?180:430,.72,2.5,16757842,i?.031:.027),y=n(new sn({color:10940415,opacity:.12,...s})),A=new mt(n(new Gn(.018,.055,7.5,10,1,!0)),y),E=A.clone();E.geometry=n(A.geometry.clone()),E.rotation.z=Math.PI/2,e.add(A,E);let D=n(new cn(.035,i?5:7,i?4:6)),v=n(new sn({color:15268607,...s})),C=new ln(D,v,i?24:48),O=new ut,V=new B(1,1,1),q=new Ot;for(let Z=0;Z<C.count;Z++){let Q=Z/C.count*Math.PI*2,le=1.52+Z%6*.23,se=Math.sin(Q*3)*.9;O.compose(new B(Math.cos(Q)*le,se,Math.sin(Q)*le),q,V),C.setMatrixAt(Z,O)}C.instanceMatrix.needsUpdate=!0,e.add(C);let j=new ei(10153983,11,11,1.5);e.add(j);let z=.28,Y="offline",te={running:0,pending:0,blocked:0,userBlocked:0,workingAgents:0};function re({time:Z=0,delta:Q=1/60,state:le=Y,reduced:se=!1,activity:Oe=te}={}){Y=Bh[le]?le:"offline",te={...te,...Oe};let Ie=Bh[Y],it=zh((te.running||0)*.26+(te.workingAgents||0)*.16+Math.min(te.pending||0,6)*.035,0,.58),Ve=zh(Ie.energy+it,.08,1.28),He=se?1:1-Math.exp(-Math.max(Q,0)*4.2);z=tl.lerp(z,Ve,He);let ee=Y==="waiting_user"||Y==="error"||(te.userBlocked||0)>0,ae=ee?16742500:Ie.cyan,Me=ee?16735816:Ie.amber,Pe=se?0:Ie.speed*(.72+z*.72),we=se?1:1+Math.sin(Z*(1.8+Pe*3.2))*.055*z;a.scale.setScalar(we*(.92+z*.11)),l.scale.setScalar(1+(se?0:Math.sin(Z*1.13)*.025*z)),r.emissive.setHex(Me),r.emissiveIntensity=.2+z*3.7,r.opacity=.32+z*.55,o.color.setHex(ae),o.opacity=.08+z*.34,c.rotation.y=se?0:Z*Pe*.19,c.rotation.x=se?.11:.11+Math.sin(Z*.17)*.08,f.forEach((Ge,je)=>{se||(Ge.rotation.z+=Q*Pe*(.12+je%5*.035)*(je%2?1:-1)),Ge.material.color.setHex(je%2?ae:Me),Ge.material.opacity=.05+z*(.11+je%3*.025)}),d.rotation.z=se?0:-Z*Pe*.08,d.rotation.y=se?0:Z*Pe*.06,_.forEach((Ge,je)=>{Ge.color.setHex(je%3?ae:Me),Ge.opacity=.045+z*(je%3?.18:.25)}),w.points.rotation.y=se?0:Z*Pe*.09,w.points.rotation.z=se?0:Z*Pe*.035,I.points.rotation.y=se?0:-Z*Pe*.14,I.points.rotation.x=se?0:Z*Pe*.028,w.material.color.setHex(ae),w.material.opacity=.16+z*.68,I.material.color.setHex(Me),I.material.opacity=.1+z*.64,y.color.setHex(ae),y.opacity=Y==="offline"?.02:.035+z*.14,A.scale.set(1,.75+z*.32,1),E.scale.set(.72+z*.34,1,1),v.color.setHex(ee?16752767:15137791),C.rotation.y=se?0:Z*Pe*.12,C.rotation.x=se?0:Math.sin(Z*.11)*.14,j.color.setHex(ae),j.intensity=.45+z*12.5}return{group:e,update:re,setActivity(Z){te={...te,...Z}},diagnostics(){return{type:"reactive-quantum-core",state:Y,energy:z,rings:f.length,particles:w.points.geometry.attributes.position.count+I.points.geometry.attributes.position.count,nodes:C.count,activity:{...te}}},dispose(){for(let Z of t)Z.dispose?.()}}}var zc=new B(0,1,0),Yr=Math.PI*2;function Hh(i){let e=i|0||1;return()=>(e^=e<<13,e^=e>>>17,e^=e<<5,(e>>>0)/4294967296)}function Gh(){return{armor:new Wt({color:2698543,metalness:.88,roughness:.39}),edge:new Wt({color:7828841,metalness:.92,roughness:.3}),black:new Wt({color:527374,metalness:.6,roughness:.48}),bronze:new Wt({color:6048048,metalness:.91,roughness:.39}),cable:new Wt({color:1711906,metalness:.7,roughness:.44}),light:new Wt({color:16756811,emissive:16751153,emissiveIntensity:1.2,metalness:.35,roughness:.27}),lens:new Wt({color:16768921,emissive:16752947,emissiveIntensity:2.5,metalness:.3,roughness:.16})}}var pl=class{constructor(e){this.materials=e,this.buckets={},this.count=0,this.matrix=new ut,this.normalMatrix=new Ye,this.position=new B,this.normal=new B,this.rotation=new Ot}add(e,t,n=[0,0,0],s=[1,1,1],r=null){let a=t.index?t.toNonIndexed():t,o=this.buckets[e]||(this.buckets[e]={position:[],normal:[]});this.rotation.identity(),r instanceof Ot?this.rotation.copy(r):r&&this.rotation.setFromEuler(new vn(...r)),this.matrix.compose(new B(...n),this.rotation,new B(...s)),this.normalMatrix.getNormalMatrix(this.matrix);let l=a.getAttribute("position"),c=a.getAttribute("normal");for(let h=0;h<l.count;h++)this.position.fromBufferAttribute(l,h).applyMatrix4(this.matrix),this.normal.fromBufferAttribute(c,h).applyNormalMatrix(this.normalMatrix),o.position.push(this.position.x,this.position.y,this.position.z),o.normal.push(this.normal.x,this.normal.y,this.normal.z);this.count++,a!==t&&a.dispose(),t.dispose()}box(e,t,n,s=null){this.add(e,new Nn(1,1,1),t,n,s)}strut(e,t,n,s=.015,r=6,a=s){let o=new B(...t),l=new B(...n),c=l.clone().sub(o),h=c.length();h<1e-4||this.add(e,new Gn(a,s,h,r),o.add(l).multiplyScalar(.5).toArray(),[1,1,1],new Ot().setFromUnitVectors(zc,c.normalize()))}cable(e,t,n=.015,s=18){let r=new Ss(t.map(a=>new B(...a)));this.add(e,new vr(r,s,n,5,!1))}finish(e){for(let[t,n]of Object.entries(this.buckets)){let s=new St;s.setAttribute("position",new pt(n.position,3)),s.setAttribute("normal",new pt(n.normal,3)),s.computeBoundingSphere();let r=new mt(s,this.materials[t]);r.name=`machine-batch-${t}`,e.add(r)}return Object.keys(this.buckets).length}};function wi(i,e,t,n,s=.075){i.add("black",new Gn(s*1.4,s*1.3,.105,12),[e,t,n-.025],[1,1,1],[Math.PI/2,0,0]),i.add("edge",new bn(s*1.15,.015,5,16),[e,t,n+.028]),i.add("bronze",new bn(s*.82,.007,4,14),[e,t,n+.039]),i.add("lens",new cn(s*.69,12,8),[e,t,n+.025],[1,1,.35]),i.add("black",new cn(s*.19,8,6),[e,t,n+.053],[1,1,.2])}function t_(i,e,t){i.add("black",new cn(.48,20,12),[0,0,0],[1,.9,.91]);let n=t?12:18;for(let s=0;s<n;s++){let r=s/n*Yr,a=[];for(let c=0;c<7;c++){let h=-1.23+c*2.46/6;a.push([Math.cos(r)*Math.cos(h)*.53,Math.sin(h)*.5,Math.sin(r)*Math.cos(h)*.46])}for(let c=0;c<a.length-1;c++)i.strut(s%4===0?"bronze":"armor",a[c],a[c+1],.034,6),i.add("edge",new cn(.028,6,4),a[c]);let o=r+.1,l=[Math.cos(o)*.48,.15*Math.sin(r*2),Math.sin(o)*.43];i.box("armor",l,[.12,.19+e()*.13,.06],[0,-o+Math.PI/2,.12]),i.strut("edge",[Math.cos(r)*.32,.43,Math.sin(r)*.3],[Math.cos(r)*.18,.62+e()*.12,Math.sin(r)*.17],.012)}for(let s of[-.27,.02,.29]){let r=Math.sqrt(1-(s/.52)**2)*.51;i.add("edge",new bn(r,.014,5,40),[0,s,0],[1,.85,1],[Math.PI/2,0,0])}i.box("armor",[0,.045,.43],[.37,.28,.14],[.05,0,0]),wi(i,0,.07,.53,.092),wi(i,-.16,-.025,.486,.048),wi(i,.16,-.025,.486,.048),wi(i,-.095,.205,.46,.035),wi(i,.095,.205,.46,.035);for(let s=0;s<4;s++){let r=(s-1.5)*.095;i.box("black",[r,-.35,.26],[.068,.16,.11]),i.box("bronze",[r,-.44,.26],[.075,.025,.12]),i.box("light",[r,-.41,.321],[.031,.018,.008])}for(let s=0;s<95;s++){let r=e()*Yr,a=(e()-.5)*.8,o=Math.sqrt(1-a*a/.25)*.51;i.box(s%8===0?"bronze":"edge",[Math.cos(r)*o,a,Math.sin(r)*o*.9],[.015,.027,.013],[e(),r,e()])}for(let s=0;s<5;s++){let r=(s-2)*.12,a=.68+e()*.35;i.strut("armor",[r,.38,-.05],[r*1.12,a,-.08],.022,6,.007),i.box("edge",[r,.54,-.05],[.035,.07,.04]),s%2===0&&i.add("light",new cn(.012,6,4),[r*1.12,a,-.08])}}function n_(i,e,t){i.box("black",[0,0,0],[.63,.72,.56]);let n=t?34:56;for(let s=0;s<n;s++){let a=s%4*Math.PI/2,o=.065+e()*.12,l=.19+e()*.48,c=(e()-.5)*.63,h=.29+e()*.11,f=Math.sin(a)*h+Math.cos(a)*c,u=Math.cos(a)*h-Math.sin(a)*c,d=(e()-.5)*.36;i.box(s%5===0?"bronze":"armor",[f,d,u],[o,l,.11],[0,a,0]),i.box("edge",[f,d+l*.45,u],[o*1.09,.018,.13],[0,a,0]),i.box("black",[f,d-l*.25,u],[o*1.1,.03,.13],[0,a,0]);let _=new B(Math.sin(a),0,Math.cos(a));for(let S=0;S<3;S++)i.box(S%3===0?"light":"edge",[f+_.x*.061,d+S*.042,u+_.z*.061],[.012,.023,.008],[0,a,0])}for(let s=-1;s<=1;s+=2)for(let r=0;r<4;r++){let a=(r-1.5)*.16;i.box("armor",[s*.44,a,-.07],[.34,.038,.55],[0,0,s*.07]),i.strut("edge",[s*.29,a-.09,.15],[s*.6,a,.15],.009),i.box("bronze",[s*.59,a,-.08],[.015,.045,.56])}wi(i,0,.04,.435,.063),wi(i,-.14,.09,.41,.028),wi(i,.14,.09,.41,.028);for(let s=0;s<9;s++){let r=(e()-.5)*.54,a=(e()-.5)*.45,o=.22+e()*.45;i.box("armor",[r,.35+o/2,a],[.043,o,.05]),i.strut("edge",[r,.35+o,a],[r,.54+o,a],.007,5,.002),i.box("bronze",[r,.46,a],[.067,.016,.075])}for(let s=0;s<12;s++){let r=(s%4-1.5)*.145,a=(Math.floor(s/4)-1)*.14,o=.14+e()*.22;i.strut("armor",[r,-.33,a],[r,-.33-o,a],.03,6,.014),i.add("bronze",new bn(.025,.007,4,8),[r,-.36-o/2,a],[1,1,1],[Math.PI/2,0,0])}}function i_(i,e,t,n,s){let r=n==="hermes"?s?7:10:6,a=s?11:17,o=r*a,l=new ln(new Gn(1,1,1,6),e.cable,o),c=new ln(new Nn(1,1,1),e.armor,o),h=new ln(new cn(1,6,4),e.edge,o),f=new ln(new pr(1,1,5),e.bronze,r*2);for(let E of[l,c,h,f])E.instanceMatrix.setUsage(pc),E.frustumCulled=!1,E.name=`articulated-${E===l?"cables":E===c?"armor":E===h?"joints":"claws"}`,i.add(E);let u=Array.from({length:r},(E,D)=>({angle:D/r*Yr+(n==="hermes"?0:.14),phase:t()*Yr,reach:(n==="hermes"?1.12:.84)+t()*.35,depth:(t()-.5)*.9,curl:t()>.5?1:-1})),d=new ut,_=new Ot,S=new B,g=new B,p=new B,w=new B,I=new B;function y(E,D,v,C,O){let V=E.angle+Math.sin(v*.27+E.phase)*.065*C+E.curl*D*D*.75,q=.43+Math.sin(D*1.37)*E.reach,j=Math.sin(v*.48+E.phase-D*3.9)*.085*C*D;return O.set(Math.cos(V)*q,Math.sin(V)*q*.61-D*D*.35+j,-.1+Math.sin(D*Math.PI)*E.depth+Math.cos(v*.39+E.phase)*.07*C*D),O}function A(E,D){let v=0;for(let C=0;C<u.length;C++){let O=u[C];for(let V=0;V<a;V++,v++){let q=V/a;y(O,q,E,D,S),y(O,(V+1)/a,E,D,g),w.copy(g).sub(S);let j=w.length();_.setFromUnitVectors(zc,w.normalize()),p.copy(S).add(g).multiplyScalar(.5);let z=(1-q*.77)*.029;I.set(z,j,z),d.compose(p,_,I),l.setMatrixAt(v,d),I.set(z*2.4,j*.58,z*2.15),d.compose(p,_,I),c.setMatrixAt(v,d),I.setScalar(z*1.08),d.compose(S,_,I),h.setMatrixAt(v,d)}y(O,1,E,D,S);for(let V=0;V<2;V++)y(O,.96,E,D,g),w.copy(S).sub(g).normalize(),w.z+=V?.4:-.4,w.normalize(),p.copy(S).addScaledVector(w,.047),_.setFromUnitVectors(zc,w),d.compose(p,_,I.set(.015,.12,.015)),f.setMatrixAt(C*2+V,d)}for(let C of[l,c,h,f])C.instanceMatrix.needsUpdate=!0}return A(0,0),{update:A,armCount:r,segments:a}}function Wh({kind:i="hermes",seed:e=1,low:t=!1}={}){let n=new Ut;n.name=`flying-${i}-machine`;let s=new Ut;s.name="hovering-articulated-body",n.add(s);let r=Hh(e),a=Gh(),o=new pl(a);i==="codex"?n_(o,r,t):t_(o,r,t);let l=o.finish(s),c=i_(s,a,r,i,t),h=r()*Yr,f=1,u="",d=0;return{group:n,update({time:_=0,state:S="idle",reduced:g=!1,delta:p=1/60}={}){let w=["offline","unavailable","unknown","disconnected"].includes(S),I=["working","tool","delegating","receiving","speaking"].includes(S),y=["error","blocked","waiting_user"].includes(S),A=w?.09:y?.75:I?1.4:.72;f=g?A:f+(A-f)*Math.min(1,p*4),a.lens.emissiveIntensity=f*2,a.light.emissiveIntensity=f*.62,S!==u&&(a.lens.emissive.setHex(y?16474676:16754235),a.light.emissive.setHex(y?15888690:16753719),u=S);let E=g||w?0:I?1:.46;s.position.y=Math.sin(_*.53+h)*.045*E,s.rotation.y=Math.sin(_*.24+h)*.1*E,s.rotation.z=Math.sin(_*.31+h)*.025*E,s.rotation.x=Math.sin(_*.29+h*.3)*.024*E,(!t||d++%2===0||g)&&c.update(g?0:_,E)},diagnostics(){return{kind:i,geometryOnly:!0,staticPieces:o.count,articulatedArms:c.armCount,segmentsPerArm:c.segments,drawCalls:l+4,nominalCoreDiameter:1.2,fullSpan:i==="hermes"?3.65:3.15}}}}function $h({low:i=!1}={}){let e=new Ut;e.name="machine-city-architecture";let t=Hh(691309),n=Gh();n.black.color.setHex(133133),n.armor.color.setHex(1188138),n.edge.color.setHex(2179408),n.bronze.color.setHex(2573133),n.cable.color.setHex(463899),n.light.color.setHex(2990020),n.light.emissive.setHex(1740216),n.light.emissiveIntensity=.42;let s=new pl(n),r=[],a=i?18:30;for(let l=0;l<a;l++){let c=l%2?1:-1,h=13+t()*18,f=c*(8.6+t()*17),u=-h,d=.45+t()*.9,_=8+t()*15,S=-7.5+_/2;r.push({x:f,z:u,width:d,height:_}),s.box("black",[f,S,u],[d,_,d*.92]);let g=i?2:3;for(let w=0;w<g;w++){let I=f+(w/Math.max(1,g-1)-.5)*d*1.12,y=d*(.58+t()*.18);s.box("armor",[I,S,u+y*.14],[d*.09,_*.94,y]),s.box("edge",[I,S,u+y*.67],[.018,_*.9,.018])}let p=Math.floor(_/1.18);for(let w=0;w<p;w++){let I=-7.25+w*1.18;s.box("armor",[f,I,u+d*.12],[d*1.13,.035,d*.92]),w%4===0&&s.box("edge",[f,I+.09,u+d*.53],[d*.92,.015,.02]);let y=i?1:2;for(let A=0;A<y;A++)t()<.68||s.box("light",[f+((A+.5)/y-.5)*d*.72,I+.18,u+d*.49],[.022+t()*.025,.045+t()*.06,.012])}}for(let l=0;l<(i?4:7);l++){let c=l%2?1:-1,h=c*(8.3+t()*2.2),f=c*(18+t()*8),u=-4.8+t()*12.5,d=-14-t()*10,_=Math.abs(f-h),S=(h+f)/2;s.box("black",[S,u,d],[_,.11,.36]),s.box("edge",[S,u+.34,d+.16],[_,.022,.022]);for(let g=0;g<Math.floor(_/2);g++){let p=Math.min(h,f)+g*2;s.strut("armor",[p,u-.24,d+.2],[p+c*.55,u+.34,d+.2],.014),g%3===0&&s.box("light",[p,u+.1,d+.25],[.025,.035,.01])}}for(let l of[-1,1])for(let c=0;c<(i?3:5);c++){let h=l*(9+t()*6),f=-14-t()*10,u=l*(.5+t()*.55);s.cable("cable",[[h,13,f],[h+u*.25,7,f+.35],[h+u*.65,1,f],[h+u,-7,f-.5]],.012+t()*.018,18)}let o=s.finish(e);return{group:e,update(){},diagnostics(){return{geometryOnly:!0,towers:r.length,staticPieces:s.count,drawCalls:o,centerClearance:8,depthRange:[-31,-13],visualMode:"quiet-server-room"}}}}var s_=["majak-hermes","majak-codex","quantlab-hermes","quantlab-codex"],Zr=(i,e,t)=>new B(i,e,t),r_={working:"working",blocked:"waiting_user",done:"complete",idle:"idle",unknown:"offline",offline:"offline"},qh=new Set(["offline","unavailable","unknown","disconnected"]);function a_(i,e,t,n=12){let s=Math.min(e/2,t/2+n);return Math.max(s,Math.min(e-s,i))}function o_(i,e,t,n,s){let r=Math.tan(e*Math.PI/360)*t*i,a=24/s*r*2,o=Math.max(0,r-1.4*n-.18-a);return Math.min(i<1?2.48:Math.min(5.35,i*2.58),o)}function Xh(i,e){let t=new rl({canvas:i,antialias:!0,powerPreference:"high-performance"}),n=innerWidth<760||navigator.deviceMemory&&navigator.deviceMemory<=4,s=Math.min(devicePixelRatio,n?1:1.5);t.setPixelRatio(s),t.outputColorSpace=nn,t.toneMapping=Vi,t.toneMappingExposure=1.2;let r=new Di;r.background=new qe(133393),r.fog=new rr(463644,.041);let a=new qt(35,1,.1,90);a.position.set(.35,.55,13.8),a.lookAt(0,.35,0);let o=new Us(t),l=new fl,c=o.fromScene(l,.08).texture;r.environment=c,r.environmentIntensity=.72,l.dispose(),o.dispose(),r.add(new Mr(9423327,329997,.82));let h=new Oi(12115434,3.6);h.position.set(-5,7,8),r.add(h);let f=new Oi(4169662,1.35);f.position.set(5,1,6),r.add(f);let u=new Oi(5228520,4.4);u.position.set(4,6,-6),r.add(u);let d=new ei(14917708,7.5,13,2);d.position.set(-1,-3,3),r.add(d);let _=Vh({low:n}),S=new Ut;S.position.set(0,.42,-.35),S.add(_.group),r.add(S);let g=$h({low:n});r.add(g.group);let p=new Map;for(let[F,$]of s_.entries()){let ie=Wh({kind:$.endsWith("hermes")?"hermes":"codex",seed:F+71,low:n});ie.group.userData.agentId=$,ie.base=Zr(0,0,0),ie.id=$,ie.status="offline",ie.group.traverse(me=>{me.userData.agentId=$}),r.add(ie.group),p.set($,ie)}let w=new Ut;w.name="swarm-task-nodes",r.add(w);let I=new Ut;I.name="swarm-task-links",r.add(I);let y=new Map,A=[],E={running:7598815,pending:12163946,blocked:16747634,failed:16736082,done:7522710},D={running:0,blocked:1,failed:2,pending:3,done:4},v=null,C=()=>{};function O(F){w.remove(F.group),F.group.traverse($=>{if($.geometry?.dispose(),$.material)for(let ie of Array.isArray($.material)?$.material:[$.material])ie.dispose()})}function V(F,$,ie,me=0){let ce=new Ut;ce.name=me?"swarm-task-cluster":`swarm-task-${F}`;let fe=E[$]||10261639,ye=new mt(me?new mr(.22,0):new _r(.16,0),new Wt({color:2435885,emissive:fe,emissiveIntensity:$==="running"?1.8:.75,metalness:.72,roughness:.28})),Ee=new mt(new bn(me?.3:.23,.012,5,20),new sn({color:fe,transparent:!0,opacity:.7}));Ee.rotation.x=Math.PI/2,ce.add(ye,Ee),ce.userData.taskId=me?null:F,ce.userData.clusterCount=me,ce.traverse(H=>{H.userData.taskId=me?null:F});let Fe={id:F,status:$,index:ie,clusterCount:me,group:ce,body:ye,ring:Ee,base:new B};return w.add(ce),Fe}function q(){let F=[...y.values()],$=F.length;F.forEach((ie,me)=>{let ce=me<10?0:1,fe=ce?me-10:me,ye=ce?Math.max(1,$-10):Math.min(10,$),Ee=-Math.PI*.92+fe/Math.max(1,ye-1)*Math.PI*1.84,Fe=ce?3.55:2.65,H=ce?2.38:1.82;ie.base.set(Math.cos(Ee)*Fe,.42+Math.sin(Ee)*H,ce?1.48:1.18),ie.group.position.copy(ie.base),ie.group.scale.setScalar(ie.clusterCount?.9:.72)})}function j(){for(;A.length;){let F=A.pop();I.remove(F.line),F.line.geometry.dispose(),F.line.material.dispose()}}function z(){for(let F of A){let $=y.get(F.from),ie=y.get(F.to);if(!$||!ie){F.line.visible=!1;continue}F.line.visible=!0,F.line.geometry.setFromPoints([$.group.position,ie.group.position])}}function Y(F){j();let $=new Set;for(let ie of F){let me=[];ie.parent_task_id&&me.push([ie.parent_task_id,"parent"]);for(let ce of ie.dependencies||[])me.push([ce,"dependency"]);for(let[ce,fe]of me){if(!y.has(ce)||!y.has(ie.task_id))continue;let ye=`${ce}\0${ie.task_id}\0${fe}`;if($.has(ye))continue;$.add(ye);let Ee=new St,Fe=new Qn({color:fe==="dependency"?14981684:7598815,transparent:!0,opacity:fe==="dependency"?.26:.34}),H=new Fi(Ee,Fe);H.name=`swarm-task-${fe}-edge`,H.renderOrder=-1,I.add(H),A.push({line:H,from:ce,to:ie.task_id,kind:fe})}}z()}function te(F){let $=[...Array.isArray(F)?F:[]].filter(ye=>ye&&ye.status!=="done").sort((ye,Ee)=>(D[ye.status]??9)-(D[Ee.status]??9)||(Ee.updated_at||0)-(ye.updated_at||0)||String(ye.task_id).localeCompare(String(Ee.task_id))),ie=20,me=$.slice(0,ie),ce=new Map(me.map((ye,Ee)=>[ye.task_id,{row:ye,index:Ee}])),fe=Math.max(0,$.length-ie);fe&&ce.set("__cluster__",{row:{task_id:"__cluster__",status:"pending"},index:me.length,clusterCount:fe});for(let[ye,Ee]of[...y])ce.has(ye)||(O(Ee),y.delete(ye));for(let[ye,Ee]of ce){let Fe=y.get(ye);(!Fe||Fe.status!==Ee.row.status||Fe.clusterCount!==(Ee.clusterCount||0))&&(Fe&&O(Fe),Fe=V(ye,Ee.row.status,Ee.index,Ee.clusterCount||0),y.set(ye,Fe)),Fe.index=Ee.index,Fe.status=Ee.row.status}v&&!y.has(v)&&(v=null),q(),Y(me),Me=!0}let re=new St;re.setAttribute("position",new Xt(new Float32Array(195),3));let Z=new Fi(re,new Qn({color:9035184,transparent:!0,opacity:.32}));Z.visible=!1,r.add(Z);let Q=new ln(new cn(.028,6,4),new sn({color:12582855}),12);Q.visible=!1,r.add(Q);let le=new ut,se=Zr(1,1,1),Oe=new Ot,Ie=new ul(t);Ie.addPass(new hl(r,a));let it=new Os(new De(1,1),.38,.38,1.18);Ie.addPass(it),Ie.addPass(new dl);let Ve="offline",He=matchMedia("(prefers-reduced-motion: reduce)").matches,ee=!0,ae=!1,Me=!0,Pe={enabled:!1,state:"idle",target:"majak-codex"},we=null,Ge=()=>{},je=0,Ze=0,Qe=0,ht=0,Je=0,ft=!1,Et=0,Lt=0,lt={running:0,pending:0,blocked:0,workingAgents:0,activeAgent:null},tt=new wr,W=new De,gt=new B,et=F=>{let $=p.get(F);return $?.group.visible?$:null};function L(F){ae||(ae=!0,cancelAnimationFrame(ht),ht=0,e.hidden=!1,i.dispatchEvent(new CustomEvent("scene-unavailable",{bubbles:!0})),F&&console.error("Machine City renderer unavailable",F))}let x=()=>{if(!ae)try{let{width:F,height:$}=i.getBoundingClientRect();if(!F||!$)return;a.aspect=F/$,a.position.z=a.aspect<1?17.6:13.8,a.updateProjectionMatrix(),a.updateMatrixWorld(),t.setSize(F,$,!1),Ie.setSize(F,$);let ie=a.aspect<1?.48:.7,me=a.getWorldDirection(Zr(0,0,0));[...p.values()].forEach((ce,fe)=>{let ye=fe%2===0?.5:1.05,Ee=o_(a.aspect,a.fov,Math.max(.1,a.position.z-ye-.25),ie,F),Fe=a.position.x+(ye-a.position.z)/me.z*me.x;ce.base.set(Fe+(fe<2?-Ee:Ee),fe%2===0?2.15:-1.1,ye),ce.group.scale.setScalar(ie),ce.group.position.copy(ce.base)}),q(),Me=!0}catch(F){L(F)}},X=new ResizeObserver(x);X.observe(i);function K(F){let $=i.getBoundingClientRect();return!$.width||!$.height?null:(W.set((F.clientX-$.left)/$.width*2-1,-(F.clientY-$.top)/$.height*2+1),tt.setFromCamera(W,a),tt.intersectObjects([...y.values()].map(me=>me.group),!0).find(me=>!!me.object.userData.taskId)?.object.userData.taskId||null)}i.addEventListener("pointermove",F=>{let $=i.getBoundingClientRect();Et=(F.clientX-$.left)/$.width-.5,Lt=(F.clientY-$.top)/$.height-.5;let ie=K(F);i.dispatchEvent(new CustomEvent("swarm-task-hover",{bubbles:!0,detail:{taskId:ie,x:F.clientX-$.left,y:F.clientY-$.top}}))}),i.addEventListener("pointerleave",()=>{Et=0,Lt=0,i.dispatchEvent(new CustomEvent("swarm-task-hover",{bubbles:!0,detail:{taskId:null,x:0,y:0}}))}),i.addEventListener("click",F=>{if(ae||!ee)return;let $=i.getBoundingClientRect();if(!$.width||!$.height)return;W.set((F.clientX-$.left)/$.width*2-1,-(F.clientY-$.top)/$.height*2+1),tt.setFromCamera(W,a);let ie=[...p.values()].filter(ce=>ce.group.visible).map(ce=>ce.group).concat([...y.values()].map(ce=>ce.group)),me=tt.intersectObjects(ie,!0).find(ce=>{for(let fe=ce.object;fe;fe=fe.parent)if(!fe.visible)return!1;return!!(ce.object.userData.agentId||ce.object.userData.taskId)});if(me){let ce=me.object.userData.taskId,fe=me.object.userData.agentId;ce?C(ce):fe&&Ge(fe)}}),i.addEventListener("webglcontextlost",F=>{F.preventDefault(),L()}),i.addEventListener("webglcontextrestored",()=>{e.hidden=!1}),document.addEventListener("visibilitychange",()=>{Qe=0,Me=!0});function oe(){r.updateMatrixWorld(),a.updateMatrixWorld();let F=i.getBoundingClientRect();if(!F.width||!F.height)return;for(let[ie,me]of p){let ce=document.querySelector(`#film-view [data-agent="${ie}"]`);if(!ce||!me.group.visible)continue;me.group.getWorldPosition(gt),gt.y-=.78*me.group.scale.x,gt.project(a);let fe=ce.offsetParent?.getBoundingClientRect()||F,ye=a_((gt.x*.5+.5)*F.width,F.width,ce.offsetWidth);ce.style.setProperty("--agent-x",`${F.left-fe.left+ye}px`),ce.style.setProperty("--agent-y",`${F.top-fe.top+(-gt.y*.5+.5)*F.height}px`)}let $=v?y.get(v):null;$?($.group.getWorldPosition(gt),gt.project(a),i.dispatchEvent(new CustomEvent("swarm-task-focus-position",{bubbles:!0,detail:{taskId:$.id,x:(gt.x*.5+.5)*F.width,y:(-gt.y*.5+.5)*F.height}}))):i.dispatchEvent(new CustomEvent("swarm-task-focus-position",{bubbles:!0,detail:{taskId:null,x:0,y:0}}))}function be(F){if(ht=0,!ae){try{if(document.hidden||!ee||He&&!Me){ht=requestAnimationFrame(be);return}let $=Qe?Math.min((F-Qe)/1e3,.08):1/60;Qe=F,He||(Ze+=$);let ie=He?0:Ze,me=He||qh.has(Ve);S.rotation.y=je||(me?0:ie*.028+Et*.11),S.rotation.x=me?0:-Lt*.07+Math.sin(ie*.17)*.025;let ce=[...p.values()].filter(J=>J.group.visible&&J.status==="working").length;_.update({time:ie,state:Ve,reduced:He,delta:$,activity:{...lt,workingAgents:ce}}),g.update({time:ie,reduced:He});let fe=0;for(let J of p.values()){let ve=fe*1.83,Ce=Pe.enabled?J.id===Pe.target?Ve:"idle":r_[J.status]||"offline";J.group.position.copy(J.base),!He&&!qh.has(Ce)&&(J.group.position.x+=Math.sin(ie*.24+ve)*.18,J.group.position.y+=Math.sin(ie*.37+ve)*.15,J.group.position.z+=Math.cos(ie*.22+ve)*.25),J.group.rotation.y=J.base.x<0?.3:-.3,J.update({time:ie,state:Ce,reduced:He,delta:$}),fe++}let ye=0;for(let J of y.values()){let ve=ye*.73;J.group.position.copy(J.base),He?(J.ring.rotation.z=ve,J.group.rotation.y=0):(J.group.position.y+=Math.sin(ie*.42+ve)*.055,J.group.position.z+=Math.cos(ie*.31+ve)*.08,J.ring.rotation.z=ie*(J.status==="running"?.75:.18)+ve,J.group.rotation.y=ie*.08+ve*.2);let Ce=v===J.id,de=J.clusterCount?.9:.72;J.group.scale.setScalar(Ce?de*1.45:de),J.body.material.emissiveIntensity=(J.status==="running"?1.8:.75)+(Ce?.9:0),ye++}z();let Ee=lt.activeAgent?et(lt.activeAgent):[...p.values()].find(J=>J.group.visible&&["working","blocked"].includes(J.status)),Fe=Pe.enabled?et(Pe.target):Ee,H=Pe.enabled?Ve:Ve==="waiting_user"||(lt.userBlocked||0)>0||Fe?.status==="blocked"?"waiting_user":"working",Se=!!(Fe&&(Pe.enabled?["delegating","waiting_result","complete","tool"].includes(Ve):["working","waiting_user"].includes(H)));if(Z.visible=Se,Q.visible=Se&&H!=="waiting_user",Se){let J=Fe.group.position,ve=new ki(Zr(J.x<0?-1.55:1.55,.5,.6),Zr(J.x*.56,J.y-.42,2.05),J.clone()),Ce=ve.getPoints(64);re.setFromPoints(Ce);let de=H==="waiting_user"?16742500:J.x<0?16758359:7598815;Z.material.color.setHex(de),Q.material.color.setHex(de),Z.material.opacity=H==="waiting_user"?.2:.43;for(let Be=0;Be<12;Be++){let Ue=He?(Be+1)/13:(ie*(.3+Math.min(lt.running||0,2)*.08)+Be/12)%1;Pe.enabled&&Ve==="complete"&&(Ue=1-Ue),le.compose(ve.getPoint(Ue),Oe,se),Q.setMatrixAt(Be,le)}Q.instanceMatrix.needsUpdate=!0}oe(),Ie.render(),Me=!1,!He&&$>.048?Je++:Je=Math.max(0,Je-1),Je>90&&!ft&&(s=1,t.setPixelRatio(1),Ie.setPixelRatio(1),it.enabled=!1,ft=!0,x())}catch($){L($);return}ae||(ht=requestAnimationFrame(be))}}x(),ae||(ht=requestAnimationFrame(be));let Ae=document.querySelector("#inspect-model");return Ae?.addEventListener("click",()=>{je=je===0?.6:je===.6?1.2:0,Ae.textContent=je===0?"Prohl\xE9dnout j\xE1dro":je===.6?"J\xE1dro ze t\u0159\xED \u010Dtvrtin":"J\xE1dro z boku",Me=!0}),{setState(F){Ve!==F&&(Ve=F,Me=!0)},setReduced(F){He=F,Me=!0,Qe=0},setActive(F){ee=F,Me=!0,Qe=0,F&&x()},setGaze(){},setActivity(F){lt={...lt,...F},_.setActivity(lt),Me=!0},setAgents(F){for(let $ of p.values()){let ie=F.find(me=>(me.id||me.agent)===$.id);$.status=ie?.status||"offline",$.group.visible=!!ie&&ie.visible!==!1}et(we)||(we=null),et(Pe.target)||(Pe.target=null),Me=!0},setTasks(F){te(F)},focusAgent(F){we=et(F)?F:null,Me=!0},focusTask(F){v=F&&y.has(F)?F:null,Me=!0},setDemo(F){Pe={...Pe,...F},et(Pe.target)||(Pe.target=null),Me=!0},onSelect(F){Ge=F},onTaskSelect(F){C=F},diagnostics(){return{geometry:"true-3d",state:Ve,reduced:He,active:ee,contextLost:ae,quality:ft?"adaptive-low":n?"low":"high",core:_.diagnostics(),drones:[...p.values()].map(F=>({id:F.id,position:F.group.position.toArray(),...F.diagnostics()})),tasks:[...y.values()].map(F=>({id:F.id,status:F.status,clusterCount:F.clusterCount,position:F.group.position.toArray()})),taskEdges:A.map(F=>({from:F.from,to:F.to,kind:F.kind})),drawCalls:t.info.render.calls,triangles:t.info.render.triangles}},quality:n?"\xDAsporn\xE1":"Vysok\xE1",dispose(){cancelAnimationFrame(ht),X.disconnect(),r.traverse(F=>{if(F.geometry?.dispose(),F.material)for(let $ of Array.isArray(F.material)?F.material:[F.material])$.dispose()}),c.dispose(),Ie.dispose(),t.dispose()}}}var zs={idle:{label:"\u010Cek\xE1",copy:"Klidov\xFD re\u017Eim \xB7 \u017E\xE1dn\xE1 hl\xE1\u0161en\xE1 aktivn\xED pr\xE1ce",tone:"amber"},receiving:{label:"P\u0159ij\xEDm\xE1 zad\xE1n\xED",copy:"Demo p\u0159ijet\xED nov\xE9ho zad\xE1n\xED",tone:"amber"},working:{label:"Zpracov\xE1v\xE1 \xFAlohu",copy:"Demo zpracov\xE1n\xED \xFAlohy",tone:"amber"},tool:{label:"Pou\u017E\xEDv\xE1 n\xE1stroj",copy:"Demo n\xE1strojov\xE9 operace \xB7 \u017Eiv\xFD zdroj tuto ud\xE1lost neposkytuje",tone:"green"},delegating:{label:"Deleguje",copy:"Demo p\u0159ed\xE1n\xED \xFAkolu vybran\xE9mu agentovi",tone:"green"},waiting_result:{label:"\u010Cek\xE1 na v\xFDsledek",copy:"Demo \u010Dek\xE1n\xED \xB7 neprob\xEDh\xE1 intenzivn\xED pr\xE1ce",tone:"amber"},waiting_user:{label:"\u010Cek\xE1 na z\xE1sah",copy:"Agent je blokovan\xFD a pot\u0159ebuje kontrolu",tone:"red"},speaking:{label:"Mluv\xED",copy:"Stylizovan\xE1 animace odpov\u011Bdi \xB7 audio nen\xED p\u0159ipojeno",tone:"green"},complete:{label:"\xDAloha dokon\u010Dena",copy:"Agent ohl\xE1sil stav done",tone:"green"},error:{label:"Probl\xE9m syst\xE9mu",copy:"Jeden nebo v\xEDce datov\xFDch zdroj\u016F selhalo",tone:"red"},offline:{label:"Odpojeno",copy:"\u010Cerstv\xFD \u017Eiv\xFD stav nen\xED dostupn\xFD",tone:"muted"}},rn=["majak","quantlab"],Yh=new Set(["majak-hermes","majak-codex","quantlab-hermes","quantlab-codex"]),Zh={hermes:"Orchestrace, pam\u011B\u0165, n\xE1stroje a \u0159\xEDzen\xED pr\xE1ce",codex:"Implementace, testov\xE1n\xED a technick\xE1 revize"},jh={idle:"\u010Cek\xE1",working:"Pracuje",blocked:"Blokov\xE1no",done:"Hotovo",unknown:"Nezn\xE1m\xE9",offline:"Odpojeno"},an={pending:"\u010Cek\xE1",running:"B\u011B\u017E\xED",blocked:"Blokov\xE1no",done:"Hotovo",failed:"Selhalo"},Jh={pending:"pending",ready:"pending",running:"running",review:"running",blocked:"blocked",done:"done",failed:"failed",cancelled:"done"},Kh="Bbambaaamm/Autonomous-Quant-Lab",l_=["count","usd","microusd","tokens","bytes","ms","seconds","percent"],c_=["producer","dashboard_read_model"],u_=["fresh","stale","unknown"],h_=[1800,900,3600,86400,604800,2592e3,31536e3],d_=["requests","tasks","searches","nodes","tokens","contexts","episodes","variants","executions","runs","prompts","proposals","trials","all","none"],f_=["work","cost","context","execution","verification","search","prompt","approval","evidence","experiments","teamwork","memory"],p_={900:"15 min",1800:"30 min",3600:"1 h",86400:"24 h",604800:"7 dn\xED",2592e3:"30 dn\xED",31536e3:"365 dn\xED"},m_=["cost","latency","quality","premium_denied","fallback","availability","policy","unknown"],g_=["DISCOVER","PLAN_GATE","BASELINE","BUILD","VERIFY","HANDOFF"],__=["auto_pass","human_approved","credential_required","privilege_required","denied","unknown"],At=new Intl.NumberFormat("cs-CZ"),$i=new Intl.NumberFormat("cs-CZ",{notation:"compact",maximumFractionDigits:1}),ue=i=>String(i??"").replace(/[&<>"']/g,e=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[e]),Tt=i=>i==null?"Nedostupn\xE9":At.format(i),Ai=i=>i==null?"Nezn\xE1m\xE9":i===0?"0 USD":`${(i/1e6).toFixed(4)} USD`,qi=i=>i==null?"Nedostupn\xE9":i<1e3?`${At.format(Math.round(i))} ms`:`${(i/1e3).toFixed(2)} s`,ii=i=>Number.isFinite(i)?`${Math.max(0,Math.floor(Date.now()/1e3-i))} s`:"Nedostupn\xE9",si=i=>Number.isFinite(i)?new Date(i*1e3).toLocaleString("cs-CZ",{day:"2-digit",month:"2-digit",hour:"2-digit",minute:"2-digit"}):"\u2014",$t=i=>Number.isFinite(i?.issue)?`#${i.issue}`:"bez issue",jr=i=>i.endsWith("-hermes")?"hermes":"codex",Vc=i=>jh[i]||jh.unknown,x_=i=>({green:"#6adf9a",red:"#ff7159",muted:"#716d66",amber:"#e49a34"})[i],Qh=(i,e="provider")=>{let t=i.filter(r=>typeof r[e]=="string"&&Number.isFinite(r.last_used_at)).sort((r,a)=>a.last_used_at-r.last_used_at||r[e].localeCompare(a[e])),n=t[0]?.[e]||null,s=[...new Set(t.map(r=>r[e]))].filter(r=>r!==n);return{currentProvider:n,historicalProviders:s}};function ed(i){let e=M=>document.querySelector(M),t={film:e("#film-view"),work:e("#work-view"),faceState:e("#face-state"),faceTask:e("#face-task"),faceSignal:e("#face-signal"),header:e("#header-status"),liveDot:e("#live-dot"),snapshotAge:e("#snapshot-age"),agentCount:e("#agent-count"),queueCount:e("#queue-count"),requestCount:e("#request-count"),searchCount:e("#search-count"),searchLatency:e("#search-latency"),costTotal:e("#cost-total"),attention:e("#attention-action"),coordinatorCurrent:e("#coordinator-current"),coordinatorNext:e("#coordinator-next"),demo:e("#demo-panel"),demoStates:e("#demo-states"),detail:e("#agent-detail"),backdrop:e("#drawer-backdrop"),canvas:e("#machine-scene"),fallback:e("#webgl-fallback"),swarmKpis:e("#swarm-kpis"),kpiActive:e("#kpi-active"),kpiRunning:e("#kpi-running"),kpiWaiting:e("#kpi-waiting"),kpiBlocked:e("#kpi-blocked"),kpiQueue:e("#kpi-queue"),kpiSuccess:e("#kpi-success"),kpiRetries:e("#kpi-retries"),kpiAvgTask:e("#kpi-avg-task"),kpiTokens:e("#kpi-tokens"),kpiCost:e("#kpi-cost"),dagStatus:e("#taskgraph-status"),dagNodes:e("#taskgraph-nodes"),analyticsGrid:e("#swarm-analytics-grid")},n=null,s=!1,r="idle",a="work",o=null,l=null,c="all",h=matchMedia("(prefers-reduced-motion: reduce)").matches,f=null,u=!1,d=null,_="",S=null,g=!1,p="Na\u010D\xEDt\xE1m skute\u010Dn\xE1 data";function w(){u=!0,t.fallback.hidden=!1;try{f?.setActive(!1)}catch{}Fn("work")}try{f=i(t.canvas,t.fallback),u=!f}catch{u=!0,t.fallback.hidden=!1}t.canvas.addEventListener("webglcontextlost",M=>{M.preventDefault(),w()}),t.canvas.addEventListener("scene-unavailable",w),t.canvas.addEventListener("swarm-task-hover",M=>{let R=e("#task-hover-label"),b=M.detail||{},G=we(b.taskId);if(!R||!G||a!=="film"){R&&(R.hidden=!0);return}R.textContent=`${$t(G)} \xB7 ${an[G.status]||G.status} \xB7 ${G.issue_title||G.task_id}`,R.style.left=`${Math.max(12,b.x+14)}px`,R.style.top=`${Math.max(72,b.y+14)}px`,R.hidden=!1}),t.canvas.addEventListener("swarm-task-focus-position",M=>{let R=e("#task-selected-label"),b=M.detail||{},G=we(b.taskId);if(!R||!G||a!=="film"||l!==G.task_id){R&&(R.hidden=!0);return}R.innerHTML=`<b>${ue($t(G))}</b><span>${ue(an[G.status]||G.status)}</span>`,R.style.left=`${Math.max(56,b.x)}px`,R.style.top=`${Math.max(110,b.y)}px`,R.hidden=!1});function I(M,...R){if(!(!f||u||typeof f[M]!="function"))try{return f[M](...R)}catch{w()}}function y(M,R){return n?.sources.find(b=>b.profile===M&&b.kind===R)}function A(){return rn.map(M=>y(M,"queue")).filter(Boolean)}function E(M=null){return(M?[y(M,"queue")].filter(Boolean):A()).flatMap(b=>b?.status==="available"?b.rows:[])}function D(M){return M?.repo==="Bbambaaamm/dotacni-majak"?"majak":"quantlab"}function v(M){return M==="majak-hermes"?"dotacni-majak-hermes":M}function C(M){return M==="dotacni-majak-hermes"?"majak-hermes":M}function O(){return y("quantlab","swarm")}function V(){let M=O();return M?.status==="available"&&M.rows.length===1?M.rows[0]:null}function q(){let M=V(),R=O();if(!M)return[];let b=/^\d+$/.test(M.issue)?Number(M.issue):null,G=R?.data_at??R?.observed_at??null;return M.tasks.map(m=>({task_id:m.task_id,status:Jh[m.state]||"blocked",raw_state:m.state,attempts:m.attempt,max_attempts:m.max_attempts,not_before:null,updated_at:G,agent:m.agent_id||null,kind:"herdr_swarm",blocker:m.blocker,pr_number:null,issue:b,issue_state:M.issue_state||"unknown",issue_title:`Herdr swarm \xB7 ${m.role}`,repo:M.repo,parent_task_id:m.parent_task_id,parent_agent_id:m.parent_agent_id,dependencies:m.dependencies,result_sha:m.result_sha,model:m.model,fallback_model:m.fallback_model,fencing_token:m.fencing_token,attempt_state:m.attempt_state,delivery_reconcile_count:m.delivery_reconcile_count}))}function j(M){return M?.issue_state==="closed"||M?.issue_open===!1&&M?.scheduler_state==="closed"}function z(M){return!j(M)||["running","pending"].includes(M.status)}function Y(M=null){return E(M).filter(z)}function te(){return q().filter(z)}function re(){return V()?.agents||[]}function Z(){let M=V();return M?.runtime_status==="available"?M.runtime_agents:null}function Q(){let M=Z();return M&&M.filter(b=>["working","blocked"].includes(b.status)&&b.task_id).map(b=>b.task_id).map(we).find(Boolean)||null}function le(){return V()?[...te(),...Y("majak")]:Y()}function se(){return Q()||le().filter(M=>M.status==="running").sort((M,R)=>(R.updated_at||0)-(M.updated_at||0)||M.task_id.localeCompare(R.task_id))[0]||le().find(M=>M.status==="blocked")||null}function Oe(){let M=V();return[...(Z()||[]).filter(R=>R.status==="blocked").map(R=>({...R,agent:R.agent_id,profile:"quantlab",runtime:!0})),...tt().filter(R=>R.status==="blocked"&&(!M||R.profile==="majak"))]}function Ie(M){M.task_id&&we(M.task_id)?Ci(M.task_id):ri(M.agent)}function it(){return V()?.edges||[]}function Ve(){return V()?[...q(),...E("majak")]:E()}function He(){return y("quantlab","admission")}function ee(){let M=He();return M?.status==="available"?M.rows:[]}function ae(){return ee().filter(M=>M.event==="deny")}function Me(){let M=y("quantlab","release");return M?.status==="available"&&M.rows.length===1?M.rows[0]:null}function Pe(){return Y().filter(M=>["pending","running","blocked"].includes(M.status))}function we(M){return Ve().find(R=>R.task_id===M)||E().find(R=>R.task_id===M)||null}let Ge=new Set(["user_action_required","agent_interactive_input_required","github_write_auth_required"]);function je(M=null){return Y(M).filter(R=>R.status==="blocked"&&Ge.has(R.blocker))}function Ze(M=null){return Y(M).filter(R=>R.status==="blocked"&&!Ge.has(R.blocker))}function Qe(M=null){let R={running:0,blocked:1};return Y().filter(b=>(!M||b.agent===M)&&Object.hasOwn(R,b.status)).sort((b,G)=>R[b.status]-R[G.status]||(G.updated_at||0)-(b.updated_at||0)||b.task_id.localeCompare(G.task_id))[0]}function ht(M=null){return Y().filter(R=>(!M||R.agent===M)&&R.status==="pending").sort((R,b)=>(R.not_before??Number.MAX_SAFE_INTEGER)-(b.not_before??Number.MAX_SAFE_INTEGER)||R.task_id.localeCompare(b.task_id))[0]}function Je(M){return M?`${$t(M)} \xB7 ${M.task_id}`:"\u017D\xE1dn\xE1"}function ft(M){return M?`${Tt(M.attempts)} / ${Tt(M.max_attempts)}`:"Nedostupn\xE9"}function Et(M){return Number.isFinite(M?.issue)?`https://github.com/${M.repo||Kh}/issues/${M.issue}`:null}function Lt(M){return Number.isFinite(M?.pr_number)?`https://github.com/${M.repo||Kh}/pull/${M.pr_number}`:null}function lt(M,R){return M?`<a href="${ue(M)}" target="_blank" rel="noopener noreferrer">${ue(R)}</a>`:""}function tt(){return rn.flatMap(M=>{let R=y(M,"herdr");return R?.status==="available"?R.rows.map(b=>({...b,profile:M})):[]})}function W(M){let R=tt().filter(b=>b.profile===M);return R.length?R:["hermes","codex"].map(b=>({agent:`${M}-${b}`,profile:M,status:"offline",unavailable:!0}))}function gt(M){let R=y(M,"router"),b=R?.status==="available",G=b?R.rows:[],m=b?G.reduce((Re,Te)=>Re+Te.requests,0):null,T=Re=>!b||G.some(Te=>!Number.isFinite(Te[Re]))?null:G.reduce((Te,ze)=>Te+ze[Re],0),P=Re=>{if(!b)return{known:null,knownRequests:null,unknownRequests:null,coverage:null};let Te=0,ze=0,Ke=0;for(let st of G)Number.isFinite(st[Re])?(Te+=st[Re],ze+=st.requests):Ke+=st.requests;return{known:Te,knownRequests:ze,unknownRequests:Ke,coverage:m===0?100:Math.round(ze/m*100)}},U=P("input_tokens"),N=P("output_tokens"),ne=P("cost_microusd"),he=b?G.filter(Re=>Number.isFinite(Re.input_tokens)&&Number.isFinite(Re.output_tokens)):[],k=b?he.reduce((Re,Te)=>Re+Te.requests,0):null,pe=b?he.reduce((Re,Te)=>Re+Te.input_tokens+Te.output_tokens,0):null,ge=b?G.filter(Re=>!Number.isFinite(Re.input_tokens)||!Number.isFinite(Re.output_tokens)).reduce((Re,Te)=>Re+Te.requests,0):null,xe=Qh(G);return{requests:m,input:T("input_tokens"),output:T("output_tokens"),cost:T("cost_microusd"),inputKnown:U.known,outputKnown:N.known,costKnown:ne.known,inputKnownRequests:U.knownRequests,outputKnownRequests:N.knownRequests,inputUnknownRequests:U.unknownRequests,outputUnknownRequests:N.unknownRequests,tokenKnownRequests:k,tokenKnownTotal:pe,tokenUnknownRequests:ge,costKnownRequests:ne.knownRequests,costUnknownRequests:ne.unknownRequests,inputCoverage:U.coverage,outputCoverage:N.coverage,costCoverage:ne.coverage,fallbacks:T("fallback_count"),models:[...new Set(G.map(Re=>Re.actual_model).filter(Re=>typeof Re=="string"))],providers:[...new Set(G.map(Re=>Re.provider).filter(Re=>typeof Re=="string"))],...xe,rows:G,router:R}}function et(M){let R=y(M,"search"),b=R?.status==="available",G=b?R.rows:[],m=he=>!b||G.some(k=>!Number.isFinite(k[he]))?null:G.reduce((k,pe)=>k+pe[he],0),T=b?m("searches"):null,P=b?m("duration_ms"):null,U=b?G.length?Math.max(...G.map(he=>he.max_duration_ms).filter(Number.isFinite)):0:null,N=Object.fromEntries(["fast","deep","browser"].map(he=>[he,b?G.filter(k=>k.route_mode===he).reduce((k,pe)=>k+(Number.isFinite(pe.searches)?pe.searches:0),0):null])),ne=Qh(G);return{searches:T,successful:b?m("successful_searches"):null,duration:P,avgLatency:T==null||P==null?null:T===0?0:P/T,maxLatency:U,fallbacks:b?m("fallback_count"):null,cost:b?m("cost_microusd"):null,results:b?m("result_count"):null,extracts:b?m("extract_count"):null,providers:[...new Set(G.map(he=>he.provider).filter(he=>typeof he=="string"))],fallbackProviders:[...new Set(G.map(he=>he.fallback_provider).filter(he=>typeof he=="string"))],...ne,routes:N,search:R}}function L(){let M=y("majak","codex");return{source:M,row:M?.status==="available"&&M.rows.length===1?M.rows[0]:null}}function x(){return rn.flatMap(M=>gt(M).rows.map(R=>({...R,profile:M})))}function X(){let M=new Map;for(let R of x()){let b=R.actual_model;M.has(b)||M.set(b,{model:b,requests:0,fallbacks:0,successes:0,durationMs:0,durationRequests:0,inputTokens:0,outputTokens:0,tokenKnownRequests:0,tokenUnknownRequests:0});let G=M.get(b);G.requests+=R.requests,G.fallbacks+=R.fallback_count,G.successes+=R.successful_requests,Number.isFinite(R.duration_ms)&&(G.durationMs+=R.duration_ms,G.durationRequests+=R.requests),Number.isFinite(R.input_tokens)&&Number.isFinite(R.output_tokens)?(G.inputTokens+=R.input_tokens,G.outputTokens+=R.output_tokens,G.tokenKnownRequests+=R.requests):G.tokenUnknownRequests+=R.requests}return[...M.values()].sort((R,b)=>b.requests-R.requests||R.model.localeCompare(b.model))}function K(){let M=V()?[...te(),...Y("majak")]:Y(),R=V()?[...q(),...E("majak")]:E(),b=ke=>M.filter(dt=>dt.status===ke).length,G=b("running"),m=b("pending"),T=b("blocked"),P=R.filter(ke=>ke.status==="failed").length,U=R.filter(ke=>ke.status==="done").length,N=T+P,ne=Z(),he=tt().filter(ke=>ke.profile==="majak"&&ke.status==="working").length,k=rn.filter(ke=>n.sources.some(dt=>dt.profile===ke)),pe=!k.includes("majak")||y("majak","herdr")?.status==="available",ge=V()?ne===null||!pe?null:ne.filter(ke=>ke.status==="working").length+he:k.every(ke=>y(ke,"herdr")?.status==="available")?tt().filter(ke=>ke.status==="working").length:null,xe=R.reduce((ke,dt)=>ke+(Number.isSafeInteger(dt.attempts)?Math.max(0,dt.attempts):0),0),Re=U+P,Te=Re?Math.round(U/Re*100):null,ze=rn.map(gt),Ke=ze.every(ke=>ke.router?.status==="available"),st=Ke?ze.reduce((ke,dt)=>ke+(dt.tokenKnownTotal||0),0):null,_t=Ke?ze.reduce((ke,dt)=>ke+(dt.tokenKnownRequests||0),0):null,Pt=Ke?ze.reduce((ke,dt)=>ke+(dt.tokenUnknownRequests||0),0):null,Ne=Ke?ze.reduce((ke,dt)=>ke+(dt.costKnown||0),0):null,Ct=Ke?ze.reduce((ke,dt)=>ke+(dt.costKnownRequests||0),0):null,We=Ke?ze.reduce((ke,dt)=>ke+(dt.costUnknownRequests||0),0):null,Rt=X(),Vt=Rt.reduce((ke,dt)=>ke+dt.durationMs,0),en=Rt.reduce((ke,dt)=>ke+dt.durationRequests,0),En=en?Vt/en:null,vt=ze.every(ke=>ke.fallbacks!=null)?ze.reduce((ke,dt)=>ke+dt.fallbacks,0):null;return{queue:M,running:G,waiting:m,blocked:N,blockedOnly:T,done:U,failed:P,activeAgents:ge,retries:xe,success:Te,activeQueue:G+m+T,tokenTotal:st,tokenKnownRequests:_t,tokenUnknownRequests:Pt,cost:Ne,costKnownRequests:Ct,costUnknownRequests:We,requestLatency:En,fallbacks:vt,models:Rt}}function oe(){let M=e("#swarm-kpis");if(!M)return;if(!n){M.innerHTML='<div class="swarm-kpi"><span>Swarm</span><b>\u2014</b><small>telemetrie nedostupn\xE1</small></div>';return}let R=K(),b=R.tokenTotal==null||!R.tokenKnownRequests?"\u2014":$i.format(R.tokenTotal),G=R.cost==null||!R.costKnownRequests?"\u2014":Ai(R.cost),m=[["Active",R.activeAgents==null?"\u2014":R.activeAgents,R.activeAgents==null?"live runtime nedostupn\xFD":"\u017Eiv\xED pracuj\xEDc\xED agenti",R.activeAgents?"running":""],["Running",R.running,"durable b\u011B\u017E\xEDc\xED tasky",R.running?"running":""],["Waiting",R.waiting,"durable pending",R.waiting?"waiting":""],["Blocked / Failed",`${R.blockedOnly} / ${R.failed}`,"blocked nyn\xED / failed historie",R.blocked?"blocked":""],["Queue",R.activeQueue,"netermin\xE1ln\xED durable tasky",""],["Durable success",R.success==null?"\u2014":`${R.success} %`,`${R.done} done \xB7 ${R.failed} failed v historii`,""],["Retries",R.retries,"durable retry counter",R.retries?"waiting":""],["Avg task","\u2014","task duration se nem\u011B\u0159\xED",""],["Tokens",b,R.tokenKnownRequests==null?"router telemetry nedostupn\xE1":`${R.tokenKnownRequests} req known \xB7 ${R.tokenUnknownRequests||0} unknown`,""],["Cost known",G,R.costKnownRequests==null?"router telemetry nedostupn\xE1":`${R.costKnownRequests} req ocen\u011Bno \xB7 ${R.costUnknownRequests||0} unknown`,""]];M.innerHTML=m.map(([T,P,U,N])=>`<article class="swarm-kpi" data-state="${N}"><span>${ue(T)}</span><b>${ue(String(P))}</b><small>${ue(U)}</small></article>`).join("")}function be(M){return[{running:0,blocked:1,failed:2,pending:3,done:4}[M.status]??9,-(M.updated_at||0),M.task_id]}function Ae(){return[...Ve()].sort((M,R)=>{let b=be(M),G=be(R);return b[0]-G[0]||b[1]-G[1]||String(b[2]).localeCompare(String(G[2]))})}function F(M){return c==="all"?!0:c==="blocked"?M.status==="blocked"||M.status==="failed":M.status===c}function $(M){let R=M.raw_state||an[M.status]||M.status,b=M.attempt_state&&M.attempt_state!==R?`${R} \xB7 ${M.attempt_state}`:R;return`<button type="button" class="taskgraph-node" role="option" aria-selected="${String(l===M.task_id)}" data-task-id="${ue(M.task_id)}" data-status="${ue(M.status)}"><b>${ue($t(M))} \xB7 ${ue(M.task_id)}</b><span>${ue(b)}</span><small>${ue(M.issue_title||M.kind)} \xB7 pokus ${ue(ft(M))}</small></button>`}function ie(M,R,b){if(!R.length)return"";let G=R.slice(0,b),m=R.length-G.length;return`<div class="taskgraph-lane" role="group" aria-label="${ue(M)}"><span class="taskgraph-lane-label">${ue(M)}</span><div class="taskgraph-lane-track">${G.map($).join("")}${m?`<div class="taskgraph-node taskgraph-cluster" data-status="pending"><b>+${m} uzl\u016F</b><span>LOD cluster</span><small>dal\u0161\xED sanitizovan\xE9 tasky</small></div>`:""}</div></div>`}function me(M,R){let b=M.filter(T=>R.has(T.from_task)&&R.has(T.to_task));if(!b.length)return"";let G=b.slice(0,16),m=b.length-G.length;return`<div class="taskgraph-edge-strip" aria-label="Autoritativn\xED DAG hrany">${G.map(T=>`<span class="taskgraph-edge" data-edge-kind="${ue(T.kind)}"><b>${ue(T.from_task)}</b><i>\u2192</i><b>${ue(T.to_task)}</b><small>${ue(T.kind)}</small></span>`).join("")}${m?`<span class="taskgraph-edge taskgraph-edge-overflow">+${m} hran</span>`:""}</div>`}function ce(){let M=e("#taskgraph-nodes"),R=e("#taskgraph-status");if(!M||!R)return;let b=O(),G=A().filter(k=>k.status==="available"),m=V()?b:G.length?{status:"available",observed_at:Math.max(...G.map(k=>k.observed_at||0))}:null;if(!m||m.status!=="available"){R.textContent="Task telemetry nen\xED dostupn\xE1.",M.innerHTML='<div class="obs-empty">TaskGraph nelze zobrazit bez durable queue.</div>',I("setTasks",[]);return}let T=Ae(),P=T.filter(F);document.querySelectorAll("[data-task-filter]").forEach(k=>k.setAttribute("aria-pressed",String(k.dataset.taskFilter===c)));let U=c==="all"?"v\u0161echny stavy":c==="pending"?"\u010Dekaj\xEDc\xED":c==="blocked"?"blocked + failed":c,N=it();if(R.textContent=V()?`Autoritativn\xED Herdr DAG \xB7 ${N.length} hran \xB7 filtr: ${U}.`:`Dependency telemetry nen\xED v aktu\xE1ln\xEDm kontraktu \xB7 hrany se nevym\xFD\u0161lej\xED \xB7 filtr: ${U}.`,!T.length){M.innerHTML='<div class="obs-empty">Durable queue je pr\xE1zdn\xE1.</div>',I("setTasks",[]);return}if(!P.length){M.innerHTML='<div class="obs-empty">Pro zvolen\xFD filtr nejsou \u017E\xE1dn\xE9 tasky.</div>',I("setTasks",T.filter(k=>k.status!=="done"));return}let ne=V()?me(N,new Set(P.map(k=>k.task_id))):"";if(c==="all"){let k=P.filter(ge=>["running","blocked","failed"].includes(ge.status)),pe=P.filter(ge=>!["running","blocked","failed"].includes(ge.status));M.innerHTML=ne+ie("Aktivn\xED / probl\xE9mov\xE9",k,10)+ie("\u010Cekaj\xEDc\xED / hotov\xE9",pe,14)}else M.innerHTML=ne+ie(U,P,18);let he=[...M.querySelectorAll("[data-task-id]")];he.forEach((k,pe)=>{k.addEventListener("click",()=>Ci(k.dataset.taskId)),k.addEventListener("keydown",ge=>{if(!["ArrowRight","ArrowLeft","ArrowDown","ArrowUp","Home","End","Enter"," "].includes(ge.key))return;if(ge.key==="Enter"||ge.key===" "){ge.preventDefault(),Ci(k.dataset.taskId);return}ge.preventDefault();let xe=ge.key==="ArrowDown"?2:ge.key==="ArrowUp"?-2:ge.key==="ArrowRight"?1:ge.key==="ArrowLeft"?-1:0,Re=ge.key==="Home"?0:ge.key==="End"?he.length-1:Math.max(0,Math.min(he.length-1,pe+xe));he[Re]?.focus()})}),I("setTasks",T.filter(k=>k.status!=="done"))}function fe(){let M=e("#swarm-analytics-grid");if(!M)return;if(!n){M.innerHTML='<article class="swarm-card"><header><h3>Swarm</h3></header><strong>\u2014</strong><p>\u017Div\xE1 telemetrie nen\xED dostupn\xE1.</p></article>';return}let R=K(),b=R.queue.length||1,G=`<div class="swarm-mini">${["running","pending","blocked","failed","done"].map(N=>{let ne=R.queue.filter(he=>he.status===N).length;return ne?`<i class="${N}" style="width:${(ne/b*100).toFixed(1)}%" title="${ue(an[N]||N)}: ${ne}"></i>`:""}).join("")}</div>`,m=R.tokenTotal==null||!R.tokenKnownRequests?"\u2014":$i.format(R.tokenTotal),T=R.cost==null||!R.costKnownRequests?"\u2014":Ai(R.cost),P=R.models.slice(0,4),U=P.length?P.map(N=>`${ue(N.model)} ${At.format(N.requests)}`).join(" \xB7 "):"Model telemetry nen\xED dostupn\xE1.";M.innerHTML=['<article class="swarm-card"><header><h3>Throughput</h3><span>tasks / time</span></header><strong>\u2014</strong><p>\u010Casov\xE1 \u0159ada dokon\u010Den\xFDch task\u016F nen\xED v autoritativn\xEDm kontraktu; hodnotu neodhadujeme.</p></article>',`<article class="swarm-card"><header><h3>Queue depth</h3><span>snapshot</span></header><strong>${At.format(R.activeQueue)}</strong>${G}<p>${R.running} running \xB7 ${R.waiting} waiting \xB7 ${R.blockedOnly} blocked \xB7 ${R.failed} failed \xB7 ${R.done} done</p></article>`,`<article class="swarm-card"><header><h3>Latency</h3><span>router request avg</span></header><strong>${ue(qi(R.requestLatency))}</strong><p>Task queue/review p50+p95 nejsou dostupn\xE9; zobrazen je pouze m\u011B\u0159en\xFD router request pr\u016Fm\u011Br.</p></article>`,`<article class="swarm-card"><header><h3>Tokens & cost</h3><span>known telemetry</span></header><strong>${ue(m)}</strong><p>${ue(T)} known \xB7 ${R.costUnknownRequests||0} req unknown \xB7 ${R.tokenUnknownRequests||0} token fields unknown.</p></article>`,`<article class="swarm-card"><header><h3>Model mix</h3><span>requests</span></header><strong>${At.format(R.models.reduce((N,ne)=>N+ne.requests,0))}</strong><p>${U}</p></article>`,`<article class="swarm-card"><header><h3>Reliability</h3><span>snapshot</span></header><strong>${At.format(R.retries)}</strong><p>true retries \xB7 ${R.blockedOnly} blocked \xB7 ${R.failed} failed \xB7 ${Tt(R.fallbacks)} model fallback\u016F.</p></article>`].join("")}function ye(){oe(),ce(),fe()}function Ee(M){return Number.isFinite(M)?new Date(M*1e3).toLocaleString("cs-CZ",{day:"2-digit",month:"2-digit",hour:"2-digit",minute:"2-digit"}):"Nezn\xE1m\xFD"}function Fe(M){if(!Number.isFinite(M))return"\u010Das resetu nen\xED dostupn\xFD";let R=Math.max(0,M-Date.now()/1e3),b=Math.ceil(R/3600);return b<48?`za ${b} h`:`za ${Math.ceil(b/24)} dn\xED`}function H(M,R,{id:b,suffix:G="",maxValue:m=null}={}){if(!M.length)return'<div class="obs-empty">Zat\xEDm bez \u010Dasov\xE9 \u0159ady.</div>';let T=680,P=178,U=42,N=12,ne=12,he=26,k=M.map(We=>Number(We[R])).filter(Number.isFinite);if(!k.length)return'<div class="obs-empty">Zat\xEDm bez m\u011B\u0159en\xFDch hodnot.</div>';let pe=Math.max(m??0,...k,1),ge=We=>M.length===1?(U+T-N)/2:U+We/(M.length-1)*(T-U-N),xe=We=>ne+(1-Math.max(0,We)/pe)*(P-ne-he),Re=M.map((We,Rt)=>[ge(Rt),xe(Number(We[R]))]),Te=Re.map(([We,Rt],Vt)=>`${Vt?"L":"M"}${We.toFixed(1)},${Rt.toFixed(1)}`).join(" "),ze=`${Te} L${ge(M.length-1).toFixed(1)},${P-he} L${ge(0).toFixed(1)},${P-he} Z`,Ke=M[0].day||si(M[0].at),st=M[Math.floor((M.length-1)/2)],_t=st.day||si(st.at),Pt=M[M.length-1],Ne=Pt.day||si(Pt.at),Ct=ue(b||"obs");return`<svg class="obs-chart" viewBox="0 0 ${T} ${P}" role="img">
      <defs><linearGradient id="${Ct}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#70ddd0"/><stop offset="1" stop-color="#70ddd0" stop-opacity="0"/></linearGradient></defs>
      ${[0,.25,.5,.75,1].map(We=>`<line class="grid" x1="${U}" y1="${(ne+We*(P-ne-he)).toFixed(1)}" x2="${T-N}" y2="${(ne+We*(P-ne-he)).toFixed(1)}"/>`).join("")}
      <path class="area" style="fill:url(#${Ct})" d="${ze}"/><path class="line" d="${Te}"/>
      ${Re.slice(-12).map(([We,Rt])=>`<circle class="point" cx="${We.toFixed(1)}" cy="${Rt.toFixed(1)}" r="2.1"/>`).join("")}
      <text class="axis" x="2" y="${ne+4}">${ue($i.format(pe)+G)}</text><text class="axis" x="2" y="${P-he+3}">0${ue(G)}</text>
      <text class="axis" x="${U}" y="${P-7}">${ue(Ke)}</text><text class="axis" text-anchor="middle" x="${(T/2).toFixed(1)}" y="${P-7}">${ue(_t)}</text><text class="axis" text-anchor="end" x="${T-N}" y="${P-7}">${ue(Ne)}</text>
    </svg>`}function Se(M,R,b,{percent:G=!1,alert:m=!1}={}){if(!M.length)return'<div class="obs-empty">\u017D\xE1dn\xE1 m\u011B\u0159en\xE1 data.</div>';let T=Math.max(...M.map(R),G?100:1);return`<div class="obs-bars">${M.map(P=>{let U=R(P),N=T?Math.max(1,U/T*100):0;return`<div class="obs-bar" data-alert="${m?String(m(P)):"false"}"><label title="${ue(P.model||P.label)}">${ue(P.model||P.label)}</label><div class="obs-bar-track"><i class="obs-bar-fill" style="--bar:${N.toFixed(1)}%"></i></div><strong>${ue(b(U,P))}</strong></div>`}).join("")}</div>`}function J(){if(s)return r;if(!n)return"offline";let M=V(),R=tt();if(M){let m=te(),T=m.filter(xe=>xe.status==="blocked"),P=Z(),U=R.filter(xe=>xe.profile==="majak"),N=Y("majak"),ne=y("majak","herdr"),he=n.sources.some(xe=>xe.profile==="majak");if(T.some(xe=>Ge.has(xe.blocker))||(P?.some(xe=>xe.status==="blocked")??!1)||U.some(xe=>xe.status==="blocked")||je("quantlab").length||je("majak").length)return"waiting_user";if(he&&(!ne||ne.status!=="available"))return m.length||R.length?"error":"offline";if((P?.some(xe=>xe.status==="working")??!1)||re().length||m.some(xe=>xe.status==="running")||U.some(xe=>xe.status==="working")||N.some(xe=>xe.status==="running"))return"working";if(T.length||Ze("majak").length)return"waiting_result";let ge=N.some(xe=>xe.status!=="done");return m.length&&m.every(xe=>xe.raw_state==="done")&&!ge?"complete":(U.some(xe=>xe.status==="idle"),"idle")}let b=R.filter(m=>jr(m.agent)==="hermes"),G=Y();return R.some(m=>m.status==="blocked")||je().length?"waiting_user":n.sources.some(m=>m.kind==="herdr"&&m.status!=="available")?R.length?"error":"offline":b.some(m=>m.status==="working")||G.some(m=>m.status==="running")?"working":Ze().length?"waiting_result":b.some(m=>m.status==="idle")?"idle":b.length&&b.every(m=>m.status==="done")?"complete":"offline"}function ve(){return Yh.has(o)?o:"majak-codex"}function Ce(M){if(s)return`DEMO \xB7 ${zs[M].copy}`;let R=V(),b=tt(),G=Z(),m=R?[...(G||[]).filter(P=>P.status==="working").map(P=>P.agent_id),...b.filter(P=>P.profile==="majak"&&P.status==="working").map(P=>P.agent)]:b.filter(P=>P.status==="working").map(P=>P.agent),T=se();if(M==="working"&&T){let P=T.repo==="Bbambaaamm/dotacni-majak"?"Maj\xE1k":T.repo==="Bbambaaamm/herdr"?"Herdr":"QuantLab",U=T.raw_state||T.status,N=T.attempt_state&&T.attempt_state!==U?` / ${T.attempt_state}`:"";if(!(T.repo==="Bbambaaamm/herdr"?G?.some(k=>k.status==="working"&&k.task_id===T.task_id)??!1:b.some(k=>k.profile===(T.repo==="Bbambaaamm/dotacni-majak"?"majak":"quantlab")&&k.status==="working"&&k.agent===C(T.agent))))return`${P} ${$t(T)} \xB7 ${T.task_id} \xB7 durable ${U}${N} \xB7 \u017Eiv\xFD runtime nepotvrzen.`;let he=N?` \xB7 durable ${U}${N}`:"";return`${P} ${$t(T)} \xB7 ${T.task_id} \xB7 live pr\xE1ce prob\xEDh\xE1${he}.`}if(M==="working"||M==="idle"&&m.length)return`Pracuj\xED: ${m.join(", ")}. P\u0159esn\xFD \xFAkol zdroj neposkytuje.`;if(M==="waiting_user"){let P=[...new Set([...(G||[]).filter(ne=>ne.status==="blocked").map(ne=>ne.agent_id),...tt().filter(ne=>ne.status==="blocked"&&(!R||ne.profile==="majak")).map(ne=>ne.agent)])],U=R?[...te(),...je()]:je(),N=[...new Map(U.map(ne=>[ne.task_id,ne])).values()].filter(ne=>ne.status==="blocked"&&Ge.has(ne.blocker)).map(ne=>`${$t(ne)} ${ne.task_id}`);return`Zkontrolujte: ${[...P,...N].join(", ")||"blokovanou \xFAlohu"}.`}return M==="waiting_result"?`Technicky blokov\xE1no: ${(R?te():Ze()).filter(U=>U.status==="blocked"&&!Ge.has(U.blocker)).map(U=>`${$t(U)} ${U.blocker||U.task_id}`).join(", ")||"intern\xED kontrola"}.`:M==="offline"?p:M==="error"?n.sources.filter(P=>P.status==="unavailable"&&P.reason!=="not_configured").map(P=>`${P.profile}/${P.kind}: ${P.reason}`).join(" \xB7 ")||"\u017Div\xFD stav jednoho projektu nen\xED dostupn\xFD.":zs[M].copy}function de(){let M=J(),R=zs[M],b=x_(R.tone),G=se(),m=le().filter(xe=>xe.status==="pending"&&(!G?.agent||xe.agent===G.agent)).sort((xe,Re)=>(xe.not_before??Number.MAX_SAFE_INTEGER)-(Re.not_before??Number.MAX_SAFE_INTEGER)||xe.task_id.localeCompare(Re.task_id))[0],T=m?.task_id===G?.task_id?null:m;t.faceState.textContent=R.label,t.faceTask.textContent=Ce(M),t.coordinatorCurrent.textContent=s?`DEMO \xB7 ${zs[M].label}`:Je(G),t.coordinatorNext.textContent=s?`DEMO \xB7 ${ve()}`:Je(T),t.coordinatorCurrent.title=t.coordinatorCurrent.textContent,t.coordinatorNext.title=t.coordinatorNext.textContent,t.faceSignal.style.background=b,t.faceSignal.style.color=b,t.faceSignal.style.boxShadow=h?"none":`0 0 13px ${b}`,M!==d&&(I("setState",M),d=M);let P=V(),U=P?[...te(),...Y("majak")]:Y(),N=tt().filter(xe=>xe.status==="working"),ne=N.filter(xe=>xe.profile==="majak"),k=(P?Z():null)?.filter(xe=>xe.status==="working")||null;I("setActivity",{running:U.filter(xe=>xe.status==="running").length,pending:U.filter(xe=>xe.status==="pending").length,blocked:U.filter(xe=>xe.status==="blocked").length,userBlocked:je().length,workingAgents:P?(k?.length||0)+ne.length:N.length,activeAgent:P?k?.[0]?.agent_id||ne[0]?.agent||null:C(G?.agent)||N[0]?.agent||null});let pe=ve(),ge=`${s}:${r}:${pe}`;ge!==_&&(I("setDemo",{enabled:s,state:r,target:pe}),_=ge),t.attention.hidden=s||!["waiting_user","error","offline"].includes(M),t.attention.textContent=M==="offline"?"Obnovit data":M==="waiting_user"?"Otev\u0159\xEDt blokovan\xE9ho agenta":"Zkontrolovat zdroje"}function Be(M){let R=jr(M.agent),b=s?"Uk\xE1zkov\xFD stroj \xB7 syntetick\xFD":M.unavailable?"Stav nen\xED dostupn\xFD":R==="hermes"?"Koordin\xE1tor":"V\xFDvojov\xFD agent",G=s?M.agent===ve()?r:"idle":M.status,m=s?`DEMO \xB7 ${zs[G].label}`:Vc(G);return`<button class="agent-node" data-agent="${ue(M.agent)}" data-state="${ue(G)}" aria-label="${ue(`${M.agent}: ${m}`)}"><span class="agent-copy"><b>${ue(M.agent)}</b><small>${b}</small></span><span class="state-chip">${ue(m)}</span></button>`}function Ue(){let M=[],R=0;for(let b of rn){let G=tt().filter(k=>k.profile===b),m=["hermes","codex"].map(k=>G.find(pe=>pe.agent===`${b}-${k}`)||{agent:`${b}-${k}`,profile:b,status:"offline",unavailable:!0}),T=G.filter(k=>!Yh.has(k.agent));R+=T.length;let P=T.length?`<button type="button" class="scene-overflow" data-overflow-profile="${b}">+${T.length} dal\u0161\xEDch agent\u016F \u2014 pracovn\xED p\u0159ehled</button>`:"";e(`#${b}-agents`).innerHTML=m.map(Be).join("")+P;let U=G.length?G:m,N=E(b),ne=je(b).length,he=Ze(b).length;e(`#${b}-project-state`).textContent=U.some(k=>k.status==="blocked")||ne?"z\xE1sah":U.some(k=>k.status==="working")||N.some(k=>k.status==="running")?"pracuje":he?"\u010Dek\xE1":U.every(k=>k.unavailable)?"bez dat":"klid",M.push(...m.map(k=>({...k,id:k.agent,role:jr(k.agent),visible:!e(`#${b}-agents`).hidden})))}t.film.querySelectorAll("[data-agent]").forEach(b=>b.addEventListener("click",()=>ri(b.dataset.agent))),t.film.querySelectorAll("[data-overflow-profile]").forEach(b=>b.addEventListener("click",()=>Fn("work"))),e("#data-caveat").textContent=R?`3D sc\xE9na zobrazuje \u010Dty\u0159i zn\xE1m\xE9 stroje. Dal\u0161\xEDch ${R} agent\u016F je v pracovn\xEDm p\u0159ehledu. Nezn\xE1m\xE9 metriky nejsou odhady.`:"Nezn\xE1m\xE9 hodnoty z\u016Fst\xE1vaj\xED nezn\xE1m\xE9.",I("setAgents",M),e("#link-layer").replaceChildren()}function bt(){if(!n){t.snapshotAge.textContent="Nedostupn\xE9",t.agentCount.textContent="Nezn\xE1m\xE9",t.queueCount.textContent="Nedostupn\xE9",t.requestCount.textContent="Nedostupn\xE9",t.searchCount.textContent="Nedostupn\xE9",t.searchLatency.textContent="Nedostupn\xE9",t.costTotal.textContent="Nedostupn\xE9",e("#work-freshness").textContent=p;return}let M=rn.map(gt),R=k=>M.every(pe=>pe[k]!=null)?M.reduce((pe,ge)=>pe+ge[k],0):null,b=rn.map(et),G=k=>b.every(pe=>pe[k]!=null)?b.reduce((pe,ge)=>pe+ge[k],0):null,m=G("searches"),T=G("duration");t.snapshotAge.textContent=ii(n.generated_at);let P=rn.every(k=>y(k,"herdr")?.status==="available");t.agentCount.textContent=P?String(tt().length):`${tt().length} ov\u011B\u0159eno \xB7 \u010D\xE1st nedostupn\xE1`;let U=[...new Set(n.sources.map(k=>k.profile))],N=A(),ne=U.length>0&&U.every(k=>y(k,"queue")?.status==="available");t.queueCount.textContent=ne?String(Pe().length):"Nedostupn\xE9",t.requestCount.textContent=Tt(R("requests")),t.searchCount.textContent=Tt(m),t.searchLatency.textContent=qi(m==null||T==null?null:m===0?0:T/m);let he=L().row;t.costTotal.textContent=he?`${100-he.used_percent} %`:"Nedostupn\xE9",t.costTotal.title=he?`Reset ${Ee(he.resets_at)}`:"Codex usage snapshot nen\xED dostupn\xFD",e("#work-freshness").textContent=`\u017Div\xFD snapshot p\u0159ed ${ii(n.generated_at)}`}function xt(){let M=e("#observability-kpis"),R=e("#observability-grid");if(!n){M.innerHTML="",R.innerHTML='<article class="obs-panel full"><div class="obs-empty">\u017Div\xE1 telemetrie nen\xED dostupn\xE1.</div></article>';return}let b=L().row,G=b?.routing_status==="available",m=G?[{label:"FREE",value:b.routing_free},{label:"Sol",value:b.routing_sol},{label:"Astra",value:b.routing_astra}]:[],T=rn.map(gt),P=T.every(_e=>_e.router?.status==="available"),U=P?T.reduce((_e,ct)=>_e+ct.requests,0):null,N=P?T.reduce((_e,ct)=>_e+ct.costKnown,0):null,ne=P?T.reduce((_e,ct)=>_e+(ct.costKnownRequests||0),0):null,he=P?T.reduce((_e,ct)=>_e+ct.costUnknownRequests,0):null,k=K(),pe=k.activeAgents,ge=k.activeQueue,xe=b?100-b.used_percent:null,Re=xe==null?"warn":xe<=5?"critical":xe<=25?"warn":"ok",Te=N==null?"Nedostupn\xE9":ne?he?`${Ai(N)} zn\xE1m\xE9 \xB7 ${At.format(he)} req bez ceny`:Ai(N):`0 req ocen\u011Bno \xB7 ${At.format(he||0)} unknown`;M.innerHTML=[`<article class="obs-kpi" data-severity="${Re}"><span>Codex allowance \xB7 zb\xFDv\xE1</span><b>${xe==null?"\u2014":xe+" %"}</b><div class="obs-gauge"><i style="--gauge:${b?b.used_percent:0}%"></i></div><small>${b?b.ordinary_usage_allowed?"B\u011B\u017En\xE9 pou\u017Eit\xED povoleno":"Limit vy\u010Derp\xE1n":"Zdroj nedostupn\xFD"}</small></article>`,`<article class="obs-kpi"><span>Dal\u0161\xED reset Codex</span><b>${b?ue(Ee(b.resets_at)):"\u2014"}</b><small>${b?ue(Fe(b.resets_at)):"\u010Cas resetu nen\xED dostupn\xFD"}</small></article>`,`<article class="obs-kpi"><span>Codex lifetime tokeny</span><b>${b?.lifetime_tokens==null?"\u2014":ue($i.format(b.lifetime_tokens))}</b><small>Peak/day: ${b?.peak_daily_tokens==null?"\u2014":ue($i.format(b.peak_daily_tokens))}</small></article>`,`<article class="obs-kpi"><span>Router po\u017Eadavky</span><b>${Tt(U)}</b><small>${P?`${At.format(T.reduce((_e,ct)=>_e+(ct.fallbacks||0),0))} fallback\u016F${G?` \xB7 Astra eskalace ${At.format(b.routing_astra_escalations)}`:""}`:"\u010D\xE1st router\u016F nedostupn\xE1"}</small></article>`,`<article class="obs-kpi"><span>Variabiln\xED n\xE1klady</span><b>${N==null||!ne?"\u2014":ue(Ai(N))}</b><small>${ue(Te)}</small></article>`,`<article class="obs-kpi" data-severity="${ge?"warn":"ok"}"><span>Aktivn\xED pr\xE1ce</span><b>${pe==null?"\u2014":At.format(pe)} agent \xB7 ${At.format(ge)} fronta</b><small>${pe==null?"Live runtime nedostupn\xFD \xB7 ":""}${ge?"Durable fronta m\xE1 netermin\xE1ln\xED \xFAlohy":"Durable fronta bez aktivn\xEDch polo\u017Eek"}</small></article>`].join("");let ze=X(),Ke=ze.slice(0,8),st=ze.filter(_e=>_e.requests>0).map(_e=>({..._e,rate:_e.fallbacks/_e.requests*100})).sort((_e,ct)=>ct.rate-_e.rate||ct.requests-_e.requests).slice(0,8),_t=ze.filter(_e=>_e.durationRequests>0).map(_e=>({..._e,avg:_e.durationMs/_e.durationRequests})).sort((_e,ct)=>ct.avg-_e.avg).slice(0,8),Pt=ze.filter(_e=>_e.tokenKnownRequests>0).map(_e=>({..._e,tokens:_e.inputTokens+_e.outputTokens})).sort((_e,ct)=>ct.tokens-_e.tokens||ct.requests-_e.requests).slice(0,8),Ne=T.every(_e=>_e.requests!=null)?T.reduce((_e,ct)=>_e+ct.requests,0):0,Ct=(_e,ct)=>{let ea=T.reduce((xl,vl)=>xl+(vl[_e]??0),0),td=T.reduce((xl,vl)=>xl+(vl[ct]??0),0),Gc=ea+td;return Gc?Math.round(ea/Gc*100):Ne===0?100:0},We=[["Input tokeny",Ct("inputKnownRequests","inputUnknownRequests")],["Output tokeny",Ct("outputKnownRequests","outputUnknownRequests")],["USD n\xE1klady",Ct("costKnownRequests","costUnknownRequests")]],Rt=E(),Vt=Object.fromEntries(Object.keys(an).map(_e=>[_e,Rt.filter(ct=>ct.status===_e).length])),en=Object.values(Vt).reduce((_e,ct)=>_e+ct,0),En=He(),vt=ee(),ke=ae(),dt=vt.filter(_e=>_e.event==="allow"),Mt=[...new Map(ke.slice().reverse().map(_e=>[_e.reason,_e])).values()].slice(0,6),wn=rn.map(et),li=["fast","deep","browser"].map(_e=>({label:_e.toUpperCase(),value:wn.every(ct=>ct.routes[_e]!=null)?wn.reduce((ct,ea)=>ct+ea.routes[_e],0):0})),ji=(b?.daily||[]).map(_e=>({day:_e.day.slice(5),tokens:_e.tokens})),Hc=b?.limit_history||[];R.innerHTML=[`<article class="obs-panel wide"><header><div><h3>Codex tokeny po dnech</h3><span>45 posledn\xEDch m\u011B\u0159en\xFDch dn\xED</span></div><span>${ji.length?"peak "+ue($i.format(Math.max(...ji.map(_e=>_e.tokens)))):"bez dat"}</span></header>${H(ji,"tokens",{id:"codexTokensArea"})}<p class="obs-note">Account-wide token activity z Codex app-serveru. Nen\xED p\u0159ev\xE1d\u011Bna na API cenu.</p></article>`,`<article class="obs-panel"><header><div><h3>Codex allowance</h3><span>\u010Dasov\xE1 \u0159ada vyu\u017Eit\xED</span></div><span>${b?b.used_percent+" % pou\u017Eito":"nedostupn\xE9"}</span></header>${H(Hc,"used_percent",{id:"codexLimitArea",suffix:" %",maxValue:100})}<p class="obs-note">${Hc.length<2?"Historii jsme pr\xE1v\u011B za\u010Dali sb\xEDrat; graf se bude plnit automaticky.":"Snapshot ka\u017Ed\xFDch p\u0159ibli\u017En\u011B 5 minut."}${G?` \xB7 Router soft ${At.format(b.routing_soft_limit_pct)} % / hard ${At.format(b.routing_hard_limit_pct)} %.`:""}</p></article>`,`<article class="obs-panel"><header><div><h3>Cost-aware router</h3><span>FREE / Sol / Astra \xB7 task decisions</span></div><span>${G?ue(b.routing_policy_version):"nedostupn\xE9"}</span></header>${Se(m,_e=>_e.value,_e=>At.format(_e))}<div class="obs-legend"><span>Astra eskalace: ${G?At.format(b.routing_astra_escalations):"\u2014"}</span><span>Premium blokov\xE1no: ${G?At.format(b.routing_premium_denied):"\u2014"}</span></div><p class="obs-note">${G?`Posledn\xED route: ${ue(b.last_route_model||"\u2014")} \xB7 ${ue(b.last_route_reason||"\u2014")}`:"Routing telemetry nen\xED dostupn\xE1."}</p></article>`,`<article class="obs-panel"><header><div><h3>Model traffic</h3><span>po\u010Det skute\u010Dn\xFDch provider request\u016F</span></div><span>top 8</span></header>${Se(Ke,_e=>_e.requests,_e=>At.format(_e))}</article>`,`<article class="obs-panel"><header><div><h3>Model tokeny</h3><span>skute\u010Dn\u011B zm\u011B\u0159en\xE9 router requesty</span></div><span>top 8</span></header>${Se(Pt,_e=>_e.tokens,_e=>$i.format(_e))}<p class="obs-note">Per-model tokeny jsou autoritativn\xED pro Hermes router. Codex Sol/Astra zde nejsou odhadov\xE1ny; jejich account-wide tokeny z\u016Fst\xE1vaj\xED v samostatn\xE9m grafu.</p></article>`,`<article class="obs-panel"><header><div><h3>Fallback pressure</h3><span>fallbacky / po\u017Eadavky</span></div><span>vy\u0161\u0161\xED = hor\u0161\xED</span></header>${Se(st,_e=>_e.rate,_e=>_e.toFixed(1)+" %",{percent:!0,alert:_e=>_e.rate>=25})}</article>`,`<article class="obs-panel"><header><div><h3>Model latency</h3><span>pr\u016Fm\u011Br na request</span></div><span>jen zn\xE1m\xE1 latence</span></header>${Se(_t,_e=>_e.avg,_e=>qi(_e))}</article>`,`<article class="obs-panel"><header><div><h3>Data coverage</h3><span>request-weighted completeness</span></div><span>fail-closed</span></header>${We.map(([_e,ct])=>`<div class="coverage-row"><span>${ue(_e)}</span><div class="coverage-track"><i style="width:${ct}%"></i></div><strong>${ct} %</strong></div>`).join("")}<p class="obs-note">100 % znamen\xE1, \u017Ee ka\u017Ed\xE9mu requestu odpov\xEDd\xE1 m\u011B\u0159en\xE1 hodnota. Chyb\u011Bj\xEDc\xED hodnoty nejsou dopo\u010D\xEDt\xE1ny.</p></article>`,`<article class="obs-panel"><header><div><h3>Durable queue</h3><span>stav pr\xE1ce QuantLab</span></div><span>${en} z\xE1znam\u016F</span></header>${en?`<div class="queue-strip">${Object.entries(Vt).filter(([,_e])=>_e).map(([_e,ct])=>`<i class="${_e}" style="width:${(ct/en*100).toFixed(1)}%" title="${ue(an[_e])}: ${ct}"></i>`).join("")}</div><div class="obs-legend">${Object.entries(Vt).map(([_e,ct])=>`<span>${ue(an[_e])}: ${ct}</span>`).join("")}</div>`:'<div class="obs-empty">Fronta je pr\xE1zdn\xE1.</div>'}</article>`,`<article class="obs-panel"><header><div><h3>Swarm admission</h3><span>ALLOW / DENY p\u0159ed spawnem</span></div><span>${En?.status==="available"?`${dt.length} / ${ke.length}`:"nedostupn\xE9"}</span></header>${En?.status==="available"?`<div class="obs-legend"><span>ALLOW: ${dt.length}</span><span>DENY: ${ke.length}</span></div>${Mt.length?`<div class="admission-reasons">${Mt.map(_e=>`<span><b>${ue(_e.reason)}</b> \xB7 ${ue(_e.repo)} #${ue(_e.issue)} \xB7 ${ue(ii(_e.observed_at))}</span>`).join("")}</div>`:'<p class="obs-note">V aktu\xE1ln\xEDm bounded tail nejsou \u017E\xE1dn\xE9 denialy.</p>'}<p class="obs-note">Zobrazeny jsou pouze sanitizovan\xE9 reason codes a DAG scope. Prompt, detail toolu ani secrets se neexportuj\xED.</p>`:'<div class="obs-empty">Admission audit nen\xED v aktu\xE1ln\xEDm snapshotu dostupn\xFD.</div>'}</article>`,`<article class="obs-panel"><header><div><h3>Search route mix</h3><span>Fast / Deep / Browser</span></div><span>aktu\xE1ln\xED snapshot</span></header>${Se(li,_e=>_e.value,_e=>At.format(_e))}</article>`,`<article class="obs-panel"><header><div><h3>Codex \xFA\u010Det</h3><span>read-only stav</span></div><span>data p\u0159ed ${L().source?ue(ii(L().source.observed_at)):"\u2014"}</span></header><div class="obs-legend"><span>Kredity: ${b?ue(b.credits_balance??"nezn\xE1m\xE9"):"\u2014"}</span><span>Reset kredity: ${b?At.format(b.reset_credits_available):"\u2014"}</span><span>Streak: ${b?.current_streak_days==null?"\u2014":At.format(b.current_streak_days)+" dn\xED"}</span><span>Max streak: ${b?.longest_streak_days==null?"\u2014":At.format(b.longest_streak_days)+" dn\xED"}</span></div><p class="obs-note">USD odhad se zobraz\xED jen pokud jej billing route skute\u010Dn\u011B poskytne. Subscription allowance se nep\u0159epo\u010D\xEDt\xE1v\xE1 na API cen\xEDk.</p></article>`].join("")}function hn(){return(n?.sources||[]).find(M=>M.kind==="metrics")||null}function gn(M){return M.value==null?"Nezn\xE1m\xE9":`${At.format(M.value)} ${ue(M.unit)}`}function ml(M){return ue(p_[M]||`${M} s`)}function gl(){let M=e("#metrics-fabric-grid"),R=hn();if(!n||!R){M.innerHTML='<article class="obs-panel full"><div class="obs-empty">Metriky nejsou v snapshotu dostupn\xE9.</div></article>';return}if(R.status!=="available"){M.innerHTML=`<article class="obs-panel full"><header><div><h3>Metriky #77 \xB7 work / cost / context / execution</h3><span>read model</span></div><span>${ue(R.status)} \xB7 ${ue(R.reason)}</span></header><div class="obs-empty">Producent t\u011Bchto metrik nen\xED integrov\xE1n. Nedostupn\xE1 hodnota nen\xED zobrazena jako nula ani jako z\xE1ruka \xFAspory.</div></article>`;return}let b=R.rows[0],G=b.measured||[],m=b.unavailable||[],T=[...G.slice(0,12),...m.slice(0,12)];M.innerHTML=`<article class="obs-panel full"><header><div><h3>Metriky #77 \xB7 work / cost / context / execution</h3><span>jednotka \xB7 okno \xB7 jmenovatel \xB7 zdroj \xB7 coverage</span></div><span>${G.length} m\u011B\u0159en\xFDch \xB7 ${m.length} nedostupn\xFDch</span></header><div class="metric-fabric">${T.map(P=>`<div class="metric-entry" data-state="${P.value==null?"unavailable":"measured"}"><b>${ue(P.label)}</b><span>${ue(gn(P))}</span><small>${ue(P.unit)} \xB7 ${ml(P.window)} \xB7 jmenovatel ${ue(P.denominator)} \xB7 ${ue(P.source)} \xB7 coverage ${P.coverage==null?"\u2014":P.coverage+" %"} \xB7 ${ue(P.freshness)}</small>${P.value==null?`<small class="metric-reason">${ue(P.note||"Producent neintegrov\xE1n.")}</small>`:""}</div>`).join("")}</div><p class="obs-note">Nezn\xE1m\xE1 hodnota nen\xED nulov\xE1 spot\u0159eba ani garantovan\xE1 \xFAspora. Za jmenovatelem ${ue(String(b.denominator??"\u2014"))}.</p></article>`}function Jr(){let M=e("#route-lifecycle-grid"),R=(n?.sources||[]).filter(b=>b.kind==="route"||b.kind==="lifecycle");if(!n||!R.length){M.innerHTML='<article class="obs-panel full"><div class="obs-empty">\u017Divotn\xED cyklus a d\u016Fvody routen\xED nejsou v snapshotu dostupn\xE9.</div></article>';return}M.innerHTML=R.map(b=>{if(b.status!=="available")return`<article class="obs-panel"><header><div><h3>${ue(b.kind==="route"?"Route decisions":"Work lifecycle")} \xB7 ${ue(b.profile)}</h3><span>read model</span></div><span>${ue(b.status)} \xB7 ${ue(b.reason)}</span></header><div class="obs-empty">Producent nen\xED integrov\xE1n. Nedostupn\xFD stav nen\xED zobrazen jako odhad.</div></article>`;let G=b.rows.slice(0,8),m=b.kind==="route"?G.map(T=>`<div class="metric-entry" data-state="measured"><b>${ue(T.model)} \xB7 ${ue(T.tier)}</b><span>${ue(T.reason)}</span><small>politika ${ue(T.policy_version||"\u2014")} \xB7 ${ue(T.policy_freshness)} \xB7 rozhodnut\xED ${ue(String(T.decisions))}</small></div>`).join(""):G.map(T=>`<div class="metric-entry" data-state="${T.evidence_state==="verified"&&T.artifact_state==="unchanged"?"measured":"unavailable"}"><b>${ue(T.phase)}</b><span>${ue(T.plan_gate)} \xB7 ${ue(T.gate_kind)}</span><small>artefakt ${ue(T.artifact_state)} \xB7 d\u016Fkaz ${ue(T.evidence_state)} \xB7 runtime ${ue(T.runtime_status)}/${ue(T.runtime_freshness)}${T.calls_after_pass?` \xB7 vol\xE1n\xED po PASS ${ue(String(T.calls_after_pass))}`:""}</small></div>`).join("");return`<article class="obs-panel"><header><div><h3>${ue(b.kind==="route"?"Route decisions":"Work lifecycle")} \xB7 ${ue(b.profile)}</h3><span>read only</span></div><span>${b.rows.length} z\xE1znam\u016F</span></header><div class="metric-fabric">${m||'<div class="obs-empty">\u017D\xE1dn\xE9 z\xE1znamy v okn\u011B.</div>'}</div><p class="obs-note">Runtime health je odd\u011Blen od durable f\xE1ze. D\u016Fkaz je uv\xE1d\u011Bn jen u ov\u011B\u0159en\xE9ho artefaktu.</p></article>`}).join("")}function Vs(){let M=A(),R=e("#queue-summary"),b=e("#queue-list");if(!M.some(P=>P.status==="available")){R.innerHTML="",b.innerHTML='<p class="queue-empty">Stav durable fronty nen\xED v aktu\xE1ln\xEDm snapshotu dostupn\xFD.</p>';return}let G=E(),m=Object.fromEntries(Object.keys(an).map(P=>[P,G.filter(U=>U.status===P).length]));R.innerHTML=Object.entries(an).map(([P,U])=>`<div class="queue-stat" data-status="${ue(P)}"><span>${ue(U)}</span><b>${Tt(m[P])}</b></div>`).join("");let T=G.slice(0,12);b.innerHTML=T.length?T.map(P=>{let U=P.blocker||"\u2014",N=P.status==="pending"?`od ${si(P.not_before)}`:`zm\u011Bna ${si(P.updated_at)}`,ne=P.issue_title||P.kind;return`<article class="queue-task" data-status="${ue(P.status)}"><div class="queue-task-main"><b>${ue($t(P))} \xB7 <code>${ue(P.task_id)}</code></b><small>${ue(ne)} \xB7 ${ue(P.kind)} \xB7 ${ue(P.agent)}</small></div><span class="queue-status">${ue(an[P.status]||P.status)}</span><span class="queue-attempt">Pokus ${ue(ft(P))}</span><time>${ue(N)}</time><span class="queue-blocker">${ue(U)}</span></article>`}).join(""):'<p class="queue-empty">Fronta je pr\xE1zdn\xE1.</p>',G.length>T.length&&b.insertAdjacentHTML("beforeend",`<p class="queue-empty">+${G.length-T.length} dal\u0161\xEDch z\xE1znam\u016F v sanitizovan\xE9m snapshotu.</p>`)}function _l(){let M=e("#search-grid");M.innerHTML=rn.map(R=>{let b=et(R);if(b.search?.status!=="available")return`<article class="search-card is-unavailable"><header><div><span>${ue(R.toUpperCase())}</span><b>Search telemetry</b></div><span class="search-health">Nedostupn\xE9</span></header><p>Zdroj Search Routeru nen\xED v aktu\xE1ln\xEDm snapshotu dostupn\xFD.</p></article>`;let G=b.searches===0?"\u2014":b.successful==null||b.searches==null?"Nedostupn\xE9":`${Math.round(b.successful/b.searches*100)} %`,m=b.currentProvider||"Zat\xEDm bez provozu",T=b.historicalProviders.join(", ")||"\u2014",P=b.fallbackProviders.join(", ")||"\u2014";return`<article class="search-card"><header><div><span>${ue(R.toUpperCase())}</span><b>Search Router</b></div><span class="search-health">${Tt(b.searches)} hled\xE1n\xED</span></header><div class="search-metrics"><div><span>\xDAsp\u011B\u0161nost</span><b>${ue(G)}</b></div><div><span>Latence avg / max</span><b>${ue(`${qi(b.avgLatency)} / ${qi(b.maxLatency)}`)}</b></div><div><span>Fallbacky</span><b>${Tt(b.fallbacks)}</b></div><div><span>N\xE1klady</span><b>${ue(Ai(b.cost))}</b></div></div><div class="search-routes"><span>FAST <b>${Tt(b.routes.fast)}</b></span><span>DEEP <b>${Tt(b.routes.deep)}</b></span><span>BROWSER <b>${Tt(b.routes.browser)}</b></span></div><p><span>Aktu\xE1ln\xED provider (posledn\xED b\u011Bh):</span> ${ue(m)}</p><p><span>Historick\xE9 providery:</span> ${ue(T)}</p><p><span>Pozorovan\xE9 fallback providery:</span> ${ue(P)}</p><p><span>V\xFDsledky / extrakce:</span> ${Tt(b.results)} / ${Tt(b.extracts)} \xB7 data p\u0159ed ${ue(ii(b.search.data_at))}</p></article>`}).join("")}function Kr(){e("#project-grid").innerHTML=rn.map(T=>{let P=tt().filter(k=>k.profile===T),U=gt(T),N=U.inputCoverage==null||U.outputCoverage==null?null:Math.min(U.inputCoverage,U.outputCoverage),ne=U.inputKnown==null?"Nedostupn\xE9":`${Tt(U.inputKnown)} / ${Tt(U.outputKnown)}${N<100?` \xB7 ${N} % req`:""}`,he=U.costKnown==null?"Nedostupn\xE9":`${Ai(U.costKnown)} zn\xE1m\xE9${U.costUnknownRequests?` + ${At.format(U.costUnknownRequests)} bez ceny`:""}`;return`<article class="work-project"><h2>${T.toUpperCase()}</h2>${P.length?P.map(k=>`<button class="work-agent" data-agent="${ue(k.agent)}"><b>${ue(k.agent)}</b><span>${Vc(k.status)}</span><small>${Zh[jr(k.agent)]}</small></button>`).join(""):"<p>\u017Div\xFD stav agent\u016F nen\xED dostupn\xFD.</p>"}<p class="work-models">Modely profilu: ${ue(U.models.join(", ")||"Nedostupn\xE9")}</p><p class="work-models">Aktu\xE1ln\xED provider (posledn\xED b\u011Bh): ${ue(U.currentProvider||"Nedostupn\xE9")}</p><p class="work-models">Historick\xE9 providery: ${ue(U.historicalProviders.join(", ")||"\u2014")}</p><div class="work-totals"><div><span>Po\u017Eadavky</span><b>${Tt(U.requests)}</b></div><div><span>Tokeny vstup/v\xFDstup</span><b>${ue(ne)}</b></div><div><span>Zn\xE1m\xE9 n\xE1klady / fallbacky</span><b>${ue(he)} \xB7 ${Tt(U.fallbacks)}</b></div></div></article>`}).join(""),e("#project-grid").querySelectorAll("[data-agent]").forEach(T=>T.addEventListener("click",()=>ri(T.dataset.agent))),xt(),Vs(),_l(),e("#source-grid").innerHTML=(n?.sources||[]).map(T=>{let P=T.kind==="codex"?"CODEX / \xDA\u010CET":`${T.profile} / ${T.kind}`;return`<article class="source-card" data-status="${ue(T.status)}"><b>${ue(P)}</b><span>${ue(T.status)} \xB7 ${ue(T.reason)}</span><span>${T.status==="available"?`${T.rows.length} z\xE1znam\u016F`:"bez dat"}</span></article>`}).join("");let M=new Set(["user_action_required","auth_required","credentials_missing","permission_required"]),R=(n?.sources||[]).filter(T=>T.status==="unavailable"&&M.has(T.reason)),b=Oe(),G=je(),m=e("#attention-summary");if(m.hidden=!!n&&!R.length&&!b.length&&!G.length,m.textContent=n?`Vy\u017Eaduje v\xE1\u0161 z\xE1sah: ${[...b.map(T=>T.agent),...G.map(T=>`${$t(T)} ${T.task_id}`),...R.map(T=>`${T.profile}/${T.kind} (${T.reason})`)].join(", ")}`:p,!m.hidden){let T=document.createElement("button");T.type="button",T.className="attention-action",T.textContent=b.length?"Otev\u0159\xEDt blokovan\xE9ho agenta":G.length?"Otev\u0159\xEDt frontu":"Obnovit data",T.addEventListener("click",()=>b.length?Ie(b[0]):G.length?e("#queue-title").scrollIntoView({behavior:h?"auto":"smooth"}):oi(!0)),m.append(" ",T)}}function Hs(){let M=we(l),R=M?.kind==="herdr_swarm",b=M?.raw_state||(M?an[M.status]||M.status:null),G=M?R?[M.parent_task_id?`parent ${M.parent_task_id}`:"root task",M.dependencies?.length?`depends on ${M.dependencies.join(", ")}`:"no dependencies"].join(" \xB7 "):"Nedostupn\xE9 v telemetry kontraktu \xB7 \u017E\xE1dn\xE1 hrana nebyla odvozena":null,m=M?R?`${M.model||"model nehl\xE1\u0161en"} \xB7 fallback ${M.fallback_model||"\u2014"}`:"Nedostupn\xE9 v telemetry kontraktu":null,T=M?R?`result ${M.result_sha||"\u2014"} \xB7 branch/base nejsou v kontraktu`:"Nedostupn\xE9 v telemetry kontraktu":null;e("#detail-profile").textContent="SWARM TASK",e("#detail-title").textContent=M?`${$t(M)} \xB7 ${M.task_id}`:l||"Task",e("#detail-role").textContent="Durable task node \xB7 read only",e("#detail-status").textContent=M?`Stav: ${b}`:"Task u\u017E nen\xED v aktu\xE1ln\xEDm snapshotu",e("#detail-links").innerHTML=M?[lt(Et(M),`Otev\u0159\xEDt Issue ${$t(M)}`),lt(Lt(M),M.pr_number?`Otev\u0159\xEDt PR #${M.pr_number}`:"")].filter(Boolean).join(""):"";let P=M?[["Task ID",M.task_id],["Issue / n\xE1zev",`${$t(M)} \xB7 ${M.issue_title||M.kind}`],["Stav / scheduler",`${b} \xB7 ${R?"authoritative swarm":M.scheduler_state||"nehl\xE1\u0161eno"}`],["Pokus / maximum",ft(M)],["Agent",M.agent||"\u2014"],["Typ",M.kind],["PR",M.pr_number?`#${M.pr_number}`:"Nen\xED hl\xE1\u0161eno"],["Blocker",M.blocker||"\u2014"],["\u010Cas",M.status==="pending"?`nejd\u0159\xEDve ${si(M.not_before)}`:`zm\u011Bna ${si(M.updated_at)}`],["Dependency edges",G],["Model / fallback",m],["Fencing token",R?Tt(M.fencing_token):"Nedostupn\xE9 v telemetry kontraktu"],["Runtime / queue wait","Nedostupn\xE9 v telemetry kontraktu"],["Branch / base / result SHA",T],["Test / reviewer","Nedostupn\xE9 v telemetry kontraktu"]]:[["Stav","Task u\u017E nen\xED v aktu\xE1ln\xEDm snapshotu"]];e("#detail-metrics").innerHTML=P.map(([N,ne])=>`<div><dt>${ue(N)}</dt><dd>${ue(ne)}</dd></div>`).join("");let U=M?[`Durable queue: ${$t(M)} \xB7 ${M.task_id} \xB7 ${b}`,`Scheduler: ${R?"authoritative swarm":M.scheduler_state||"nehl\xE1\u0161eno"} \xB7 pokus ${ft(M)}`,M.blocker?`Blocker: ${M.blocker}`:"Bez hl\xE1\u0161en\xE9ho blockeru",R?`Autoritativn\xED DAG: ${G}.`:"Dependency telemetry nen\xED sou\u010D\xE1st\xED aktu\xE1ln\xEDho snapshotu; DAG hrany nejsou odhadov\xE1ny.","Prompt, intern\xED my\u0161lenky a raw log nejsou v dashboardu zobrazov\xE1ny."]:["Task nen\xED v aktu\xE1ln\xEDm snapshotu."];e("#detail-events").innerHTML=U.map(N=>`<li>${ue(N)}</li>`).join("")}function _n(){if(l){Hs();return}if(!o)return;let M=Z()?.find(Ke=>Ke.agent_id===o),R=M?{...M,agent:M.agent_id,profile:"quantlab",runtime:!0}:tt().find(Ke=>Ke.agent===o),b=R?.profile||(o.startsWith("majak-")?"majak":"quantlab"),G=gt(b),m=et(b),T=y(b,"herdr"),P=o.endsWith("-hermes"),U=v(o),N=M?.task_id?we(M.task_id):P?Qe(U)||ht(U):null,ne=P?N?`${$t(N)} \xB7 ${N.task_id} \xB7 ${an[N.status]||N.status}`:"\u017D\xE1dn\xE1 \xFAloha v durable queue":"Nedostupn\xE9 v datov\xE9m kontraktu",he=N?.issue_title||"Nedostupn\xE9 v telemetry kontraktu",k=N?`${an[N.status]||N.status} \xB7 scheduler ${N.scheduler_state||"nehl\xE1\u0161eno"}`:"Nedostupn\xE9 v telemetry kontraktu",pe=N?`${N.status==="pending"?"nejd\u0159\xEDve "+si(N.not_before):"zm\u011Bna "+si(N.updated_at)}`:"Nedostupn\xE9 v telemetry kontraktu",ge=G.inputCoverage==null||G.outputCoverage==null?null:Math.min(G.inputCoverage,G.outputCoverage),xe=G.inputKnown==null?"Nedostupn\xE9":`${Tt(G.inputKnown)} / ${Tt(G.outputKnown)}${ge<100?` \xB7 coverage ${ge} % req`:""}`,Re=G.costKnown==null?"Nedostupn\xE9":`${Ai(G.costKnown)} zn\xE1m\xE9${G.costUnknownRequests?` + ${At.format(G.costUnknownRequests)} req bez ceny`:""}`;e("#detail-profile").textContent=R?.runtime?"HERDR":b.toUpperCase(),e("#detail-title").textContent=o,e("#detail-role").textContent=R?.runtime?"Runtime agent \xB7 read only":Zh[jr(o)],e("#detail-status").textContent=`\u017Div\xFD stav: ${R?Vc(R.status):"Odpojeno / nezn\xE1m\xE9"}`,e("#detail-links").innerHTML=[lt(Et(N),N?`Otev\u0159\xEDt Issue ${$t(N)}`:""),lt(Lt(N),N?.pr_number?`Otev\u0159\xEDt PR #${N.pr_number}`:"")].filter(Boolean).join("");let Te=[["Aktu\xE1ln\xED \xFAkol",ne],["Issue / n\xE1zev",N?`${$t(N)} \xB7 ${he}`:"Nedostupn\xE9 v telemetry kontraktu"],["Task stav",k],["Pokus / maximum",ft(N)],["\u010Cas fronty",pe],["PR",N?.pr_number?`#${N.pr_number}`:"Nen\xED hl\xE1\u0161eno"],["Blocker",N?.blocker||"\u2014"],["Modely profilu",G.models.join(", ")||"Nedostupn\xE9 v aktu\xE1ln\xEDm snapshotu"],["Aktu\xE1ln\xED model provider / fallbacky",`${G.currentProvider||"Nedostupn\xE9"} \xB7 ${Tt(G.fallbacks)}`],["Historick\xE9 model providery",G.historicalProviders.join(", ")||"\u2014"],["Tokeny vstup / v\xFDstup",xe],["Zn\xE1m\xE9 n\xE1klady profilu",Re],["Aktu\xE1ln\xED search provider / fallbacky",`${m.currentProvider||"Nedostupn\xE9"} \xB7 ${Tt(m.fallbacks)}`],["Historick\xE9 search providery",m.historicalProviders.join(", ")||"\u2014"],["Search / avg latence",`${Tt(m.searches)} \xB7 ${qi(m.avgLatency)}`],["Runtime / queue wait","Nedostupn\xE9 v telemetry kontraktu"],["Branch / base / result SHA","Nedostupn\xE9 v telemetry kontraktu"],["Test / reviewer","Nedostupn\xE9 v telemetry kontraktu"]];e("#detail-metrics").innerHTML=Te.map(([Ke,st])=>`<div><dt>${ue(Ke)}</dt><dd>${ue(st)}</dd></div>`).join("");let ze=[];R&&ze.push(`Herdr hl\xE1s\xED stav \u201E${R.status}\u201C \xB7 pozorov\xE1no p\u0159ed ${ii(R.runtime?O()?.observed_at:T?.observed_at)}`),N&&ze.push(`Durable queue: ${$t(N)} \xB7 ${N.task_id} \xB7 ${an[N.status]||N.status} \xB7 pokus ${ft(N)} \xB7 scheduler ${N.scheduler_state||"nehl\xE1\u0161eno"}`),N?.blocker&&ze.push(`Blocker: ${N.blocker}`),G.router?.status==="available"&&ze.push(`Router profilu: ${Tt(G.requests)} po\u017Eadavk\u016F \xB7 data p\u0159ed ${ii(G.router.data_at)}`),m.search?.status==="available"&&ze.push(`Search Router: ${Tt(m.searches)} hled\xE1n\xED \xB7 ${qi(m.avgLatency)} pr\u016Fm\u011Br \xB7 ${Tt(m.fallbacks)} fallback\u016F \xB7 data p\u0159ed ${ii(m.search.data_at)}`),ze.push("Runtime, branch/SHA, test a reviewer data se nezobrazuj\xED, dokud je autoritativn\xED telemetry kontrakt neposkytuje."),ze.push("Zdroj neposkytuje prompt, historii n\xE1stroj\u016F, intern\xED my\u0161lenky ani surov\xE9 provozn\xED z\xE1znamy \xFAlohy."),s&&ze.unshift("DEMO: pohyb 3D sc\xE9ny je syntetick\xFD. Tento detail st\xE1le zobrazuje skute\u010Dn\xFD snapshot."),e("#detail-events").innerHTML=ze.map(Ke=>`<li>${ue(Ke)}</li>`).join("")}function ri(M){!rn.flatMap(W).some(R=>R.agent===M)&&!Z()?.some(R=>R.agent_id===M)||(S=document.activeElement,l=null,o=M,_n(),t.detail.hidden=!1,t.backdrop.hidden=!1,document.body.style.overflow="hidden",e("#detail-close").focus(),I("focusTask",null),I("focusAgent",M),s&&Ue(),ce(),de())}function Ci(M){we(M)&&(S=document.activeElement,o=null,l=M,Hs(),t.detail.hidden=!1,t.backdrop.hidden=!1,document.body.style.overflow="hidden",e("#detail-close").focus(),I("focusAgent",null),I("focusTask",M),ce(),de())}function Xi(){t.detail.hidden=!0,t.backdrop.hidden=!0,document.body.style.overflow="",I("focusAgent",null),I("focusTask",l||null),S?.isConnected?S.focus():l?document.querySelector(`[data-task-id="${CSS.escape(l)}"]`)?.focus():document.querySelector(`[data-agent="${CSS.escape(o||"")}"]`)?.focus()}function Fn(M){a=M,t.film.hidden=M!=="film",t.work.hidden=M!=="work",document.querySelectorAll("[data-view]").forEach(R=>{let b=R.dataset.view===M;R.classList.toggle("is-active",b),R.setAttribute("aria-pressed",String(b))}),I("setActive",M==="film"&&!document.hidden),u&&(t.fallback.hidden=!1)}function Yi(){document.documentElement.dataset.motion=h?"reduced":"full";let M=e("#motion-toggle");M.setAttribute("aria-pressed",String(h)),M.textContent=h?"Povolit pohyb":"Omezit pohyb",I("setReduced",h),de()}function ai(){let M=Me(),R=M?` \xB7 ${M.tag} @ ${M.commit.slice(0,12)}`:"";t.header.textContent=s?"DEMO \xB7 sc\xE9na syntetick\xE1, metriky skute\u010Dn\xE9":n?`\u017Div\xE1 data \xB7 ${ii(n.generated_at)}${R}`:p;let b=s?"#e49a34":n?"#6adf9a":"#ff7159";t.liveDot.style.background=b,t.liveDot.style.color=b}function Zi(){ai(),Ue(),bt(),ye(),Kr(),de(),gl(),Jr(),t.detail.hidden||_n()}function Qr(M){if(!M||!Number.isFinite(M.generated_at)||!Array.isArray(M.sources))throw new Error("invalid");if(Date.now()/1e3-M.generated_at>90||M.generated_at>Date.now()/1e3+5)throw new Error("stale");for(let R of M.sources){if(!R||!rn.includes(R.profile)||typeof R.kind!="string"||!Array.isArray(R.rows))throw new Error("invalid");if(R.kind==="herdr"&&R.rows.some(b=>typeof b.agent!="string"||typeof b.status!="string"))throw new Error("invalid");if(["router","search"].includes(R.kind)&&R.rows.some(b=>typeof b.provider!="string"||!Number.isFinite(b.last_used_at)))throw new Error("invalid");if(R.kind==="queue"){let b=R.profile==="majak"?{repo:"Bbambaaamm/dotacni-majak",agent:"dotacni-majak-hermes"}:{repo:"Bbambaaamm/Autonomous-Quant-Lab",agent:"quantlab-hermes"};if(R.rows.some(G=>typeof G.task_id!="string"||G.repo!=null&&typeof G.repo!="string"||R.profile==="majak"&&G.repo!==b.repo||R.profile==="quantlab"&&G.repo!=null&&G.repo!==b.repo||G.issue!=null&&(!Number.isSafeInteger(G.issue)||G.issue<0)||G.issue_title!=null&&(typeof G.issue_title!="string"||G.issue_title.length>160)||typeof G.issue_open!="boolean"||G.scheduler_state!=null&&typeof G.scheduler_state!="string"||G.agent!==b.agent||typeof G.kind!="string"||!Object.hasOwn(an,G.status)||!Number.isSafeInteger(G.attempts)||G.attempts<0||!Number.isSafeInteger(G.max_attempts)||G.max_attempts<0||G.not_before!=null&&!Number.isFinite(G.not_before)||!Number.isFinite(G.updated_at)||G.blocker!=null&&typeof G.blocker!="string"||G.pr_number!=null&&(!Number.isSafeInteger(G.pr_number)||G.pr_number<1)))throw new Error("invalid")}if(R.kind==="admission"){if(R.profile!=="quantlab")throw new Error("invalid");if(R.rows.some(b=>!["allow","deny"].includes(b.event)||b.reason!=null&&typeof b.reason!="string"||typeof b.role!="string"||typeof b.repo!="string"||typeof b.issue!="string"||!Number.isSafeInteger(b.node_count)||b.node_count<0||!Number.isSafeInteger(b.max_depth)||b.max_depth<0||!Number.isSafeInteger(b.max_fanout)||b.max_fanout<0||!Number.isSafeInteger(b.child_tools_count)||b.child_tools_count<0||b.agents_after!=null&&(!Number.isSafeInteger(b.agents_after)||b.agents_after<0)||!Number.isFinite(b.observed_at)||b.event==="deny"&&(b.reason==null||b.agents_after!=null)||b.event==="allow"&&(b.reason!=null||b.agents_after==null)))throw new Error("invalid")}if(R.kind==="swarm"){if(R.profile!=="quantlab"||R.status==="available"&&R.rows.length!==1)throw new Error("invalid");for(let b of R.rows){let G=b.runtime_status??"unavailable",m=b.runtime_agents??[];if(b.version!==1||typeof b.repo!="string"||typeof b.issue!="string"||b.issue_state!=null&&!["open","closed","unknown"].includes(b.issue_state)||typeof b.paper_only!="boolean"||!Array.isArray(b.policy_profiles)||!Array.isArray(b.agents)||!Array.isArray(b.tasks)||!Array.isArray(b.edges)||!["available","unavailable","not_applicable"].includes(G)||!Array.isArray(m)||G!=="available"&&m.length||b.repo==="Bbambaaamm/Autonomous-Quant-Lab"&&b.paper_only!==!0)throw new Error("invalid");let T=new Set;for(let k of b.tasks){if(!k||typeof k.task_id!="string"||T.has(k.task_id)||!Object.hasOwn(Jh,k.state)||typeof k.role!="string"||!Number.isSafeInteger(k.attempt)||k.attempt<0||!Number.isSafeInteger(k.max_attempts)||k.max_attempts<k.attempt||k.attempt_state!=null&&!["dispatching","accepted","working","delivery_uncertain","verifying","completed","done","blocked","failed","retry_scheduled","verification_pending"].includes(k.attempt_state)||k.delivery_reconcile_count!=null&&(!Number.isSafeInteger(k.delivery_reconcile_count)||k.delivery_reconcile_count<0)||!Number.isSafeInteger(k.fencing_token)||k.fencing_token<0||!Array.isArray(k.dependencies)||k.dependencies.some(pe=>typeof pe!="string")||k.parent_task_id!=null&&typeof k.parent_task_id!="string"||k.parent_agent_id!=null&&typeof k.parent_agent_id!="string"||k.agent_id!=null&&typeof k.agent_id!="string"||k.result_sha!=null&&(typeof k.result_sha!="string"||!/^[0-9a-f]{64}$/.test(k.result_sha)))throw new Error("invalid");T.add(k.task_id)}let P=new Map(b.tasks.map(k=>[k.task_id,k])),U=new Set;for(let k of m){if(!k||typeof k.agent_id!="string"||U.has(k.agent_id)||!["idle","working","blocked","done","unknown"].includes(k.status)||k.task_id!=null&&!P.has(k.task_id))throw new Error("invalid");let pe=b.tasks.filter(ge=>ge.agent_id===k.agent_id&&["pending","ready","running","blocked","review"].includes(ge.state));if(k.task_id!=null&&(pe.length!==1||pe[0].task_id!==k.task_id))throw new Error("invalid");U.add(k.agent_id)}let N=new Set,ne=new Set;for(let k of b.agents){if(!k||typeof k.agent_id!="string"||N.has(k.agent_id)||typeof k.task_id!="string"||ne.has(k.task_id)||k.state!=="running"||k.parent_task_id!=null&&typeof k.parent_task_id!="string"||k.parent_agent_id!=null&&typeof k.parent_agent_id!="string"||!Number.isSafeInteger(k.fencing_token)||k.fencing_token<0)throw new Error("invalid");let pe=P.get(k.task_id);if(!pe||pe.state!=="running"||pe.agent_id!==k.agent_id||pe.parent_task_id!==k.parent_task_id||pe.parent_agent_id!==k.parent_agent_id||pe.fencing_token!==k.fencing_token)throw new Error("invalid");N.add(k.agent_id),ne.add(k.task_id)}let he=new Set(b.tasks.filter(k=>k.state==="running"&&k.agent_id!=null).map(k=>k.task_id));if(he.size!==ne.size||[...he].some(k=>!ne.has(k)))throw new Error("invalid");for(let k of b.edges)if(!k||!["parent","dependency"].includes(k.kind)||typeof k.from_task!="string"||typeof k.to_task!="string"||!T.has(k.from_task)||!T.has(k.to_task))throw new Error("invalid")}}if(R.kind==="metrics"){if(R.profile!=="quantlab"||R.status==="available"&&R.rows.length!==1)throw new Error("invalid");for(let b of R.rows){if(!Array.isArray(b.measured)||!Array.isArray(b.unavailable)||b.denominator!=null&&(!Number.isSafeInteger(b.denominator)||b.denominator<0))throw new Error("invalid");if(b.measured.length>64||b.unavailable.length>64)throw new Error("invalid");let G=new Set;for(let m of[...b.measured,...b.unavailable]){if(!m||typeof m.id!="string"||G.has(m.id))throw new Error("invalid");if(G.add(m.id),!l_.includes(m.unit)||!c_.includes(m.source)||!u_.includes(m.freshness)||!h_.includes(m.window)||!d_.includes(m.denominator)||typeof m.label!="string"||!m.label||!f_.includes(m.category))throw new Error("invalid");if(m.value!=null&&(!Number.isSafeInteger(m.value)||m.value<0))throw new Error("invalid");if(m.coverage!=null&&(!Number.isSafeInteger(m.coverage)||m.coverage<0||m.coverage>100))throw new Error("invalid");if(m.value==null&&m.coverage===100)throw new Error("invalid")}if(b.measured.some(m=>m.value==null))throw new Error("invalid")}}if(R.kind==="route"){if(R.profile!=="quantlab"||R.status==="available"&&R.rows.length>50)throw new Error("invalid");for(let b of R.rows)if(typeof b.route_id!="string"||!Number.isFinite(b.observed_at)||!["free","sol","astra","browser","direct","unknown"].includes(b.tier)||typeof b.model!="string"||!m_.includes(b.reason)||!["fresh","stale","unknown"].includes(b.policy_freshness)||b.policy_version!=null&&typeof b.policy_version!="string"||!Number.isSafeInteger(b.decisions)||b.decisions<0)throw new Error("invalid")}if(R.kind==="lifecycle"){if(R.profile!=="quantlab"||R.status==="available"&&R.rows.length>50)throw new Error("invalid");for(let b of R.rows)if(typeof b.work_id!="string"||!g_.includes(b.phase)||!Number.isFinite(b.observed_at)||!Number.isSafeInteger(b.entered_at)||!__.includes(b.plan_gate)||!["auto","human","credential","privilege","unknown"].includes(b.gate_kind)||!["unchanged","changed","missing","unverified"].includes(b.artifact_state)||!["verified","unverified","unavailable","uncertain"].includes(b.evidence_state)||b.artifact_hash!=null&&!/^[0-9a-f]{64}$/.test(b.artifact_hash)||b.skill_bundle!=null&&(typeof b.skill_bundle!="object"||!("version"in b.skill_bundle)||!("hash"in b.skill_bundle))||!["available","unavailable","not_applicable"].includes(b.runtime_status)||!["fresh","stale","unknown"].includes(b.runtime_freshness))throw new Error("invalid")}if(R.kind==="release"){if(R.profile!=="quantlab"||R.status==="available"&&R.rows.length!==1)throw new Error("invalid");if(R.rows.some(b=>typeof b.tag!="string"||!/^v[A-Za-z0-9._-]{1,62}$/.test(b.tag)||typeof b.commit!="string"||!/^[0-9a-f]{40}$/.test(b.commit)||typeof b.config_sha256!="string"||!/^[0-9a-f]{64}$/.test(b.config_sha256)||!Number.isSafeInteger(b.deployed_at)||b.deployed_at<0))throw new Error("invalid")}if(R.kind==="codex"){if(R.profile!=="majak"||R.status==="available"&&R.rows.length!==1)throw new Error("invalid");if(R.rows.some(b=>!Number.isFinite(b.used_percent)||b.used_percent<0||b.used_percent>100||!Array.isArray(b.daily)||!Array.isArray(b.limit_history)||!["available","unavailable"].includes(b.routing_status)))throw new Error("invalid");for(let b of R.rows){if(b.routing_status!=="available")continue;let G=["routing_observed_at","routing_soft_limit_pct","routing_hard_limit_pct","routing_decisions","routing_free","routing_sol","routing_astra","routing_astra_escalations","routing_premium_denied"];if(typeof b.routing_policy_version!="string"||b.routing_policy_version.length>64||G.some(m=>!Number.isSafeInteger(b[m])||b[m]<0)||b.routing_soft_limit_pct>=b.routing_hard_limit_pct||b.routing_hard_limit_pct>100||b.routing_free+b.routing_sol+b.routing_astra>b.routing_decisions||b.routing_astra_escalations>b.routing_astra||b.last_route_at!=null&&!Number.isFinite(b.last_route_at)||b.last_route_tier!=null&&!["free","sol","astra"].includes(b.last_route_tier)||b.last_route_model!=null&&typeof b.last_route_model!="string"||b.last_route_reason!=null&&typeof b.last_route_reason!="string")throw new Error("invalid")}}}return M}async function oi(M=!1){if(g||!M&&document.hidden)return;g=!0;let R=new AbortController,b=setTimeout(()=>R.abort(),1e4);try{let G=await fetch("/agent-platform/api/v1/overview",{cache:"no-store",headers:{Accept:"application/json"},signal:R.signal});if(!G.ok)throw new Error(`HTTP ${G.status}`);n=Qr(await G.json()),p="\u010Cerstv\xFD \u017Eiv\xFD stav nen\xED dostupn\xFD",e("#server-fallback-details").removeAttribute("open")}catch(G){n=null,p=G.message==="stale"?"Snapshot je star\u0161\xED ne\u017E 90 s \xB7 obnovte data":"\u017Div\xE1 data nejsou dostupn\xE1 \xB7 ov\u011B\u0159te p\u0159ipojen\xED nebo p\u0159ihl\xE1\u0161en\xED"}finally{clearTimeout(b),g=!1,Zi()}}for(let[M,R]of Object.entries(zs)){let b=document.createElement("button");b.type="button",b.dataset.demoState=M,b.textContent=R.label,b.addEventListener("click",()=>{r=M,t.demoStates.querySelectorAll("button").forEach(G=>{let m=G.dataset.demoState===M;G.classList.toggle("is-active",m),G.setAttribute("aria-pressed",String(m))}),Ue(),de()}),t.demoStates.append(b)}return document.querySelectorAll("[data-view]").forEach(M=>M.addEventListener("click",()=>Fn(M.dataset.view))),document.querySelectorAll("[data-task-filter]").forEach(M=>M.addEventListener("click",()=>{c=M.dataset.taskFilter||"all",ce()})),e("#demo-toggle").addEventListener("click",M=>{s=!s,document.documentElement.dataset.mode=s?"demo":"live",M.currentTarget.setAttribute("aria-pressed",String(s)),M.currentTarget.textContent=s?"Ukon\u010Dit demo":"Demo re\u017Eim",t.demo.hidden=!s,s&&(r="idle",t.demoStates.querySelectorAll("button").forEach(R=>{let b=R.dataset.demoState==="idle";R.classList.toggle("is-active",b),R.setAttribute("aria-pressed",String(b))})),ai(),Ue(),de(),t.detail.hidden||_n(),s||oi(!0)}),e("#demo-panel > div:first-child > span").textContent="Pouze animace jsou syntetick\xE9. Metriky a detaily z\u016Fst\xE1vaj\xED skute\u010Dn\xE9.",e("#motion-toggle").addEventListener("click",()=>{h=!h,Yi()}),matchMedia("(prefers-reduced-motion: reduce)").addEventListener("change",M=>{h=M.matches,Yi()}),e("#detail-close").addEventListener("click",Xi),t.backdrop.addEventListener("click",Xi),t.detail.setAttribute("role","dialog"),t.detail.setAttribute("aria-modal","true"),document.addEventListener("keydown",M=>{if(!t.detail.hidden&&(M.key==="Escape"&&Xi(),M.key==="Tab")){let R=[...t.detail.querySelectorAll('button:not([disabled]),a[href],[tabindex="0"]')],b=R[0],G=R[R.length-1];M.shiftKey&&document.activeElement===b?(M.preventDefault(),G?.focus()):!M.shiftKey&&document.activeElement===G&&(M.preventDefault(),b?.focus())}}),t.attention.addEventListener("click",()=>{if(!n){oi(!0);return}let M=Oe()[0];M?Ie(M):Fn("work")}),document.querySelectorAll("[data-project-toggle]").forEach(M=>M.addEventListener("click",()=>{let R=M.closest(".project").querySelector(".agent-list"),b=M.getAttribute("aria-expanded")==="true";M.setAttribute("aria-expanded",String(!b)),R.hidden=b,Ue()})),document.addEventListener("visibilitychange",()=>{I("setActive",!document.hidden&&a==="film"),document.hidden||oi(!0)}),I("onSelect",ri),I("onTaskSelect",Ci),Yi(),Fn(u?"work":"film"),Zi(),oi(!0),setInterval(oi,3e4),setInterval(()=>{document.hidden||(n&&Date.now()/1e3-n.generated_at>90?(n=null,p="Snapshot je star\u0161\xED ne\u017E 90 s \xB7 obnovte data",Zi()):(bt(),ai(),t.detail.hidden||_n()))},1e3),Object.freeze({diagnostics:()=>({view:a,mode:s?"demo":"live",state:J(),reduced:h,selectedAgent:o,selectedTask:l,sceneAvailable:!!f&&!u,freshSnapshot:!!n,agentCount:tt().length,queueActive:Pe().length})})}ed(Xh);document.documentElement.dataset.preview==="true"&&document.querySelector("#demo-toggle").click();})();
/*! Bundled license information:

three/build/three.core.js:
three/build/three.module.js:
  (**
   * @license
   * Copyright 2010-2026 Three.js Authors
   * SPDX-License-Identifier: MIT
   *)
*/
