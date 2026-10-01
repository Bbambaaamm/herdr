(()=>{var Qr=new Uint32Array(256),pl=Qr.length;function ut(){let i=globalThis.crypto;if(!i||typeof i.getRandomValues!="function")throw new Error("secure_random_unavailable");return pl>=Qr.length&&(i.getRandomValues(Qr),pl=0),Qr[pl++]/4294967296}var gu=0,jl=1,_u=2;var Rr=1,xu=2,Ps=3,Ti=0,en=1,Yn=2,Cn=0,Is=1,Wi=2,Jl=3,Kl=4,vu=5;var qi=100,yu=101,Mu=102,bu=103,Su=104,Tu=200,Eu=201,wu=202,Au=203,Ql=204,ec=205,Cu=206,Ru=207,Pu=208,Iu=209,Lu=210,Nu=211,Du=212,Uu=213,Fu=214,wa=0,Aa=1,Ca=2,gs=3,Ra=4,Pa=5,Ia=6,La=7,co=0,ku=1,Ou=2,On=0,Pr=1,Ir=2,Lr=3,Xi=4,Nr=5,Dr=6,Ur=7;var tc=300,Ei=301,$i=302,uo=303,ho=304,Fr=306,Na=1e3,Hn=1001,Da=1002,Zt=1003,Bu=1004;var kr=1005;var Qt=1006,fo=1007;var wi=1008;var xn=1009,nc=1010,ic=1011,Ls=1012,po=1013,Bn=1014,Rn=1015,tn=1016,mo=1017,go=1018,Ns=1020,sc=35902,rc=35899,ac=1021,oc=1022,Pn=1023,Gn=1026,Ai=1027,_o=1028,xo=1029,Ci=1030,vo=1031;var yo=1033,Or=33776,Br=33777,zr=33778,Vr=33779,Mo=35840,bo=35841,So=35842,To=35843,Eo=36196,wo=37492,Ao=37496,Co=37488,Ro=37489,Hr=37490,Po=37491,Io=37808,Lo=37809,No=37810,Do=37811,Uo=37812,Fo=37813,ko=37814,Oo=37815,Bo=37816,zo=37817,Vo=37818,Ho=37819,Go=37820,Wo=37821,qo=36492,Xo=36494,$o=36495,Yo=36283,Zo=36284,Gr=36285,jo=36286;var nr=2300,Ua=2301,Ta=2302,zl=2303,Vl=2400,Hl=2401,Gl=2402;var zu=3200;var Wr=0,Vu=1,oi="",dn="srgb",ir="srgb-linear",sr="linear",bt="srgb";var Ea=7680;var Hu=519,Gu=512,Wu=513,qu=514,Jo=515,Xu=516,$u=517,Ko=518,Yu=519,Zu=35044,lc=35048;var cc="300 es",Un=2e3,_s=2001;function Yh(i){for(let e=i.length-1;e>=0;--e)if(i[e]>=65535)return!0;return!1}function Zh(i){return ArrayBuffer.isView(i)&&!(i instanceof DataView)}function rr(i){return document.createElementNS("http://www.w3.org/1999/xhtml",i)}function ju(){let i=rr("canvas");return i.style.display="block",i}var kc={},xs=null;function uc(...i){let e="THREE."+i.shift();xs?xs("log",e,...i):console.log(e,...i)}function Ju(i){let e=i[0];if(typeof e=="string"&&e.startsWith("TSL:")){let t=i[1];t&&t.isStackTrace?i[0]+=" "+t.getLocation():i[1]='Stack trace not available. Enable "THREE.Node.captureStackTrace" to capture stack traces.'}return i}function Je(...i){i=Ju(i);let e="THREE."+i.shift();if(xs)xs("warn",e,...i);else{let t=i[0];t&&t.isStackTrace?console.warn(t.getError(e)):console.warn(e,...i)}}function et(...i){i=Ju(i);let e="THREE."+i.shift();if(xs)xs("error",e,...i);else{let t=i[0];t&&t.isStackTrace?console.error(t.getError(e)):console.error(e,...i)}}function Oi(...i){let e=i.join(" ");e in kc||(kc[e]=!0,Je(...i))}function Ku(i,e,t){return new Promise(function(n,s){function r(){switch(i.clientWaitSync(e,i.SYNC_FLUSH_COMMANDS_BIT,0)){case i.WAIT_FAILED:s();break;case i.TIMEOUT_EXPIRED:setTimeout(r,t);break;default:n()}}setTimeout(r,t)})}var Qu={[wa]:Aa,[Ca]:Ia,[Ra]:La,[gs]:Pa,[Aa]:wa,[Ia]:Ca,[La]:Ra,[Pa]:gs},Wn=class{addEventListener(e,t){this._listeners===void 0&&(this._listeners={});let n=this._listeners;n[e]===void 0&&(n[e]=[]),n[e].indexOf(t)===-1&&n[e].push(t)}hasEventListener(e,t){let n=this._listeners;return n===void 0?!1:n[e]!==void 0&&n[e].indexOf(t)!==-1}removeEventListener(e,t){let n=this._listeners;if(n===void 0)return;let s=n[e];if(s!==void 0){let r=s.indexOf(t);r!==-1&&s.splice(r,1)}}dispatchEvent(e){let t=this._listeners;if(t===void 0)return;let n=t[e.type];if(n!==void 0){e.target=this;let s=n.slice(0);for(let r=0,a=s.length;r<a;r++)s[r].call(this,e);e.target=null}}},sn=["00","01","02","03","04","05","06","07","08","09","0a","0b","0c","0d","0e","0f","10","11","12","13","14","15","16","17","18","19","1a","1b","1c","1d","1e","1f","20","21","22","23","24","25","26","27","28","29","2a","2b","2c","2d","2e","2f","30","31","32","33","34","35","36","37","38","39","3a","3b","3c","3d","3e","3f","40","41","42","43","44","45","46","47","48","49","4a","4b","4c","4d","4e","4f","50","51","52","53","54","55","56","57","58","59","5a","5b","5c","5d","5e","5f","60","61","62","63","64","65","66","67","68","69","6a","6b","6c","6d","6e","6f","70","71","72","73","74","75","76","77","78","79","7a","7b","7c","7d","7e","7f","80","81","82","83","84","85","86","87","88","89","8a","8b","8c","8d","8e","8f","90","91","92","93","94","95","96","97","98","99","9a","9b","9c","9d","9e","9f","a0","a1","a2","a3","a4","a5","a6","a7","a8","a9","aa","ab","ac","ad","ae","af","b0","b1","b2","b3","b4","b5","b6","b7","b8","b9","ba","bb","bc","bd","be","bf","c0","c1","c2","c3","c4","c5","c6","c7","c8","c9","ca","cb","cc","cd","ce","cf","d0","d1","d2","d3","d4","d5","d6","d7","d8","d9","da","db","dc","dd","de","df","e0","e1","e2","e3","e4","e5","e6","e7","e8","e9","ea","eb","ec","ed","ee","ef","f0","f1","f2","f3","f4","f5","f6","f7","f8","f9","fa","fb","fc","fd","fe","ff"],Oc=1234567,Ks=Math.PI/180,vs=180/Math.PI;function Ds(){let i=ut()*4294967295|0,e=ut()*4294967295|0,t=ut()*4294967295|0,n=ut()*4294967295|0;return(sn[i&255]+sn[i>>8&255]+sn[i>>16&255]+sn[i>>24&255]+"-"+sn[e&255]+sn[e>>8&255]+"-"+sn[e>>16&15|64]+sn[e>>24&255]+"-"+sn[t&63|128]+sn[t>>8&255]+"-"+sn[t>>16&255]+sn[t>>24&255]+sn[n&255]+sn[n>>8&255]+sn[n>>16&255]+sn[n>>24&255]).toLowerCase()}function ft(i,e,t){return Math.max(e,Math.min(t,i))}function hc(i,e){return(i%e+e)%e}function jh(i,e,t,n,s){return n+(i-e)*(s-n)/(t-e)}function Jh(i,e,t){return i!==e?(t-i)/(e-i):0}function Qs(i,e,t){return(1-t)*i+t*e}function Kh(i,e,t,n){return Qs(i,e,1-Math.exp(-t*n))}function Qh(i,e=1){return e-Math.abs(hc(i,e*2)-e)}function ed(i,e,t){return i<=e?0:i>=t?1:(i=(i-e)/(t-e),i*i*(3-2*i))}function td(i,e,t){return i<=e?0:i>=t?1:(i=(i-e)/(t-e),i*i*i*(i*(i*6-15)+10))}function nd(i,e){return i+Math.floor(ut()*(e-i+1))}function id(i,e){return i+ut()*(e-i)}function sd(i){return i*(.5-ut())}function rd(i){i!==void 0&&(Oc=i);let e=Oc+=1831565813;return e=Math.imul(e^e>>>15,e|1),e^=e+Math.imul(e^e>>>7,e|61),((e^e>>>14)>>>0)/4294967296}function ad(i){return i*Ks}function od(i){return i*vs}function ld(i){return i>0&&Number.isInteger(i)&&2**Math.round(Math.log2(i))===i}function cd(i){return Math.pow(2,Math.ceil(Math.log(i)/Math.LN2))}function ud(i){return Math.pow(2,Math.floor(Math.log(i)/Math.LN2))}function hd(i,e,t,n,s){let r=Math.cos,a=Math.sin,o=r(t/2),l=a(t/2),c=r((e+n)/2),h=a((e+n)/2),f=r((e-n)/2),u=a((e-n)/2),d=r((n-e)/2),g=a((n-e)/2);switch(s){case"XYX":i.set(o*h,l*f,l*u,o*c);break;case"YZY":i.set(l*u,o*h,l*f,o*c);break;case"ZXZ":i.set(l*f,l*u,o*h,o*c);break;case"XZX":i.set(o*h,l*g,l*d,o*c);break;case"YXY":i.set(l*d,o*h,l*g,o*c);break;case"ZYZ":i.set(l*g,l*d,o*h,o*c);break;default:Je("MathUtils: .setQuaternionFromProperEuler() encountered an unknown order: "+s)}}function ps(i,e){switch(e.constructor){case Float32Array:return i;case Uint32Array:return i/4294967295;case Uint16Array:return i/65535;case Uint8Array:case Uint8ClampedArray:return i/255;case Int32Array:return Math.max(i/2147483647,-1);case Int16Array:return Math.max(i/32767,-1);case Int8Array:return Math.max(i/127,-1);default:throw new Error("THREE.MathUtils: Invalid component type.")}}function hn(i,e){switch(e.constructor){case Float32Array:return i;case Uint32Array:return Math.round(i*4294967295);case Uint16Array:return Math.round(i*65535);case Uint8Array:case Uint8ClampedArray:return Math.round(i*255);case Int32Array:return Math.round(i*2147483647);case Int16Array:return Math.round(i*32767);case Int8Array:return Math.round(i*127);default:throw new Error("THREE.MathUtils: Invalid component type.")}}var Qo={DEG2RAD:Ks,RAD2DEG:vs,generateUUID:Ds,clamp:ft,euclideanModulo:hc,mapLinear:jh,inverseLerp:Jh,lerp:Qs,damp:Kh,pingpong:Qh,smoothstep:ed,smootherstep:td,randInt:nd,randFloat:id,randFloatSpread:sd,seededRandom:rd,degToRad:ad,radToDeg:od,isPowerOfTwo:ld,ceilPowerOfTwo:cd,floorPowerOfTwo:ud,setQuaternionFromProperEuler:hd,normalize:hn,denormalize:ps},Ue=class i{static{i.prototype.isVector2=!0}constructor(e=0,t=0){this.x=e,this.y=t}get width(){return this.x}set width(e){this.x=e}get height(){return this.y}set height(e){this.y=e}set(e,t){return this.x=e,this.y=t,this}setScalar(e){return this.x=e,this.y=e,this}setX(e){return this.x=e,this}setY(e){return this.y=e,this}setComponent(e,t){switch(e){case 0:this.x=t;break;case 1:this.y=t;break;default:throw new Error("THREE.Vector2: index is out of range: "+e)}return this}getComponent(e){switch(e){case 0:return this.x;case 1:return this.y;default:throw new Error("THREE.Vector2: index is out of range: "+e)}}clone(){return new this.constructor(this.x,this.y)}copy(e){return this.x=e.x,this.y=e.y,this}add(e){return this.x+=e.x,this.y+=e.y,this}addScalar(e){return this.x+=e,this.y+=e,this}addVectors(e,t){return this.x=e.x+t.x,this.y=e.y+t.y,this}addScaledVector(e,t){return this.x+=e.x*t,this.y+=e.y*t,this}sub(e){return this.x-=e.x,this.y-=e.y,this}subScalar(e){return this.x-=e,this.y-=e,this}subVectors(e,t){return this.x=e.x-t.x,this.y=e.y-t.y,this}multiply(e){return this.x*=e.x,this.y*=e.y,this}multiplyScalar(e){return this.x*=e,this.y*=e,this}divide(e){return this.x/=e.x,this.y/=e.y,this}divideScalar(e){return this.multiplyScalar(1/e)}applyMatrix3(e){let t=this.x,n=this.y,s=e.elements;return this.x=s[0]*t+s[3]*n+s[6],this.y=s[1]*t+s[4]*n+s[7],this}min(e){return this.x=Math.min(this.x,e.x),this.y=Math.min(this.y,e.y),this}max(e){return this.x=Math.max(this.x,e.x),this.y=Math.max(this.y,e.y),this}clamp(e,t){return this.x=ft(this.x,e.x,t.x),this.y=ft(this.y,e.y,t.y),this}clampScalar(e,t){return this.x=ft(this.x,e,t),this.y=ft(this.y,e,t),this}clampLength(e,t){let n=this.length();return this.divideScalar(n||1).multiplyScalar(ft(n,e,t))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this}negate(){return this.x=-this.x,this.y=-this.y,this}dot(e){return this.x*e.x+this.y*e.y}cross(e){return this.x*e.y-this.y*e.x}lengthSq(){return this.x*this.x+this.y*this.y}length(){return Math.sqrt(this.x*this.x+this.y*this.y)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)}normalize(){return this.divideScalar(this.length()||1)}angle(){return Math.atan2(-this.y,-this.x)+Math.PI}angleTo(e){let t=Math.sqrt(this.lengthSq()*e.lengthSq());if(t===0)return Math.PI/2;let n=this.dot(e)/t;return Math.acos(ft(n,-1,1))}distanceTo(e){return Math.sqrt(this.distanceToSquared(e))}distanceToSquared(e){let t=this.x-e.x,n=this.y-e.y;return t*t+n*n}manhattanDistanceTo(e){return Math.abs(this.x-e.x)+Math.abs(this.y-e.y)}setLength(e){return this.normalize().multiplyScalar(e)}lerp(e,t){return this.x+=(e.x-this.x)*t,this.y+=(e.y-this.y)*t,this}lerpVectors(e,t,n){return this.x=e.x+(t.x-e.x)*n,this.y=e.y+(t.y-e.y)*n,this}equals(e){return e.x===this.x&&e.y===this.y}fromArray(e,t=0){return this.x=e[t],this.y=e[t+1],this}toArray(e=[],t=0){return e[t]=this.x,e[t+1]=this.y,e}fromBufferAttribute(e,t){return this.x=e.getX(t),this.y=e.getY(t),this}rotateAround(e,t){let n=Math.cos(t),s=Math.sin(t),r=this.x-e.x,a=this.y-e.y;return this.x=r*n-a*s+e.x,this.y=r*s+a*n+e.y,this}random(){return this.x=ut(),this.y=ut(),this}*[Symbol.iterator](){yield this.x,yield this.y}},Gt=class{constructor(e=0,t=0,n=0,s=1){this.isQuaternion=!0,this._x=e,this._y=t,this._z=n,this._w=s}static slerpFlat(e,t,n,s,r,a,o){let l=n[s+0],c=n[s+1],h=n[s+2],f=n[s+3],u=r[a+0],d=r[a+1],g=r[a+2],M=r[a+3];if(f!==M||l!==u||c!==d||h!==g){let m=l*u+c*d+h*g+f*M;m<0&&(u=-u,d=-d,g=-g,M=-M,m=-m);let p=1-o;if(m<.9995){let T=Math.acos(m),C=Math.sin(T);p=Math.sin(p*T)/C,o=Math.sin(o*T)/C,l=l*p+u*o,c=c*p+d*o,h=h*p+g*o,f=f*p+M*o}else{l=l*p+u*o,c=c*p+d*o,h=h*p+g*o,f=f*p+M*o;let T=1/Math.sqrt(l*l+c*c+h*h+f*f);l*=T,c*=T,h*=T,f*=T}}e[t]=l,e[t+1]=c,e[t+2]=h,e[t+3]=f}static multiplyQuaternionsFlat(e,t,n,s,r,a){let o=n[s],l=n[s+1],c=n[s+2],h=n[s+3],f=r[a],u=r[a+1],d=r[a+2],g=r[a+3];return e[t]=o*g+h*f+l*d-c*u,e[t+1]=l*g+h*u+c*f-o*d,e[t+2]=c*g+h*d+o*u-l*f,e[t+3]=h*g-o*f-l*u-c*d,e}get x(){return this._x}set x(e){this._x=e,this._onChangeCallback()}get y(){return this._y}set y(e){this._y=e,this._onChangeCallback()}get z(){return this._z}set z(e){this._z=e,this._onChangeCallback()}get w(){return this._w}set w(e){this._w=e,this._onChangeCallback()}set(e,t,n,s){return this._x=e,this._y=t,this._z=n,this._w=s,this._onChangeCallback(),this}clone(){return new this.constructor(this._x,this._y,this._z,this._w)}copy(e){return this._x=e.x,this._y=e.y,this._z=e.z,this._w=e.w,this._onChangeCallback(),this}setFromEuler(e,t=!0){let n=e._x,s=e._y,r=e._z,a=e._order,o=Math.cos,l=Math.sin,c=o(n/2),h=o(s/2),f=o(r/2),u=l(n/2),d=l(s/2),g=l(r/2);switch(a){case"XYZ":this._x=u*h*f+c*d*g,this._y=c*d*f-u*h*g,this._z=c*h*g+u*d*f,this._w=c*h*f-u*d*g;break;case"YXZ":this._x=u*h*f+c*d*g,this._y=c*d*f-u*h*g,this._z=c*h*g-u*d*f,this._w=c*h*f+u*d*g;break;case"ZXY":this._x=u*h*f-c*d*g,this._y=c*d*f+u*h*g,this._z=c*h*g+u*d*f,this._w=c*h*f-u*d*g;break;case"ZYX":this._x=u*h*f-c*d*g,this._y=c*d*f+u*h*g,this._z=c*h*g-u*d*f,this._w=c*h*f+u*d*g;break;case"YZX":this._x=u*h*f+c*d*g,this._y=c*d*f+u*h*g,this._z=c*h*g-u*d*f,this._w=c*h*f-u*d*g;break;case"XZY":this._x=u*h*f-c*d*g,this._y=c*d*f-u*h*g,this._z=c*h*g+u*d*f,this._w=c*h*f+u*d*g;break;default:Je("Quaternion: .setFromEuler() encountered an unknown order: "+a)}return t===!0&&this._onChangeCallback(),this}setFromAxisAngle(e,t){let n=t/2,s=Math.sin(n);return this._x=e.x*s,this._y=e.y*s,this._z=e.z*s,this._w=Math.cos(n),this._onChangeCallback(),this}setFromRotationMatrix(e){let t=e.elements,n=t[0],s=t[4],r=t[8],a=t[1],o=t[5],l=t[9],c=t[2],h=t[6],f=t[10],u=n+o+f;if(u>0){let d=.5/Math.sqrt(u+1);this._w=.25/d,this._x=(h-l)*d,this._y=(r-c)*d,this._z=(a-s)*d}else if(n>o&&n>f){let d=2*Math.sqrt(1+n-o-f);this._w=(h-l)/d,this._x=.25*d,this._y=(s+a)/d,this._z=(r+c)/d}else if(o>f){let d=2*Math.sqrt(1+o-n-f);this._w=(r-c)/d,this._x=(s+a)/d,this._y=.25*d,this._z=(l+h)/d}else{let d=2*Math.sqrt(1+f-n-o);this._w=(a-s)/d,this._x=(r+c)/d,this._y=(l+h)/d,this._z=.25*d}return this._onChangeCallback(),this}setFromUnitVectors(e,t){let n=e.dot(t)+1;return n<1e-8?(n=0,Math.abs(e.x)>Math.abs(e.z)?(this._x=-e.y,this._y=e.x,this._z=0,this._w=n):(this._x=0,this._y=-e.z,this._z=e.y,this._w=n)):(this._x=e.y*t.z-e.z*t.y,this._y=e.z*t.x-e.x*t.z,this._z=e.x*t.y-e.y*t.x,this._w=n),this.normalize()}angleTo(e){return 2*Math.acos(Math.abs(ft(this.dot(e),-1,1)))}rotateTowards(e,t){let n=this.angleTo(e);if(n===0)return this;let s=Math.min(1,t/n);return this.slerp(e,s),this}identity(){return this.set(0,0,0,1)}invert(){return this.conjugate()}conjugate(){return this._x*=-1,this._y*=-1,this._z*=-1,this._onChangeCallback(),this}dot(e){return this._x*e._x+this._y*e._y+this._z*e._z+this._w*e._w}lengthSq(){return this._x*this._x+this._y*this._y+this._z*this._z+this._w*this._w}length(){return Math.sqrt(this._x*this._x+this._y*this._y+this._z*this._z+this._w*this._w)}normalize(){let e=this.length();return e===0?(this._x=0,this._y=0,this._z=0,this._w=1):(e=1/e,this._x=this._x*e,this._y=this._y*e,this._z=this._z*e,this._w=this._w*e),this._onChangeCallback(),this}multiply(e){return this.multiplyQuaternions(this,e)}premultiply(e){return this.multiplyQuaternions(e,this)}multiplyQuaternions(e,t){let n=e._x,s=e._y,r=e._z,a=e._w,o=t._x,l=t._y,c=t._z,h=t._w;return this._x=n*h+a*o+s*c-r*l,this._y=s*h+a*l+r*o-n*c,this._z=r*h+a*c+n*l-s*o,this._w=a*h-n*o-s*l-r*c,this._onChangeCallback(),this}slerp(e,t){let n=e._x,s=e._y,r=e._z,a=e._w,o=this.dot(e);o<0&&(n=-n,s=-s,r=-r,a=-a,o=-o);let l=1-t;if(o<.9995){let c=Math.acos(o),h=Math.sin(c);l=Math.sin(l*c)/h,t=Math.sin(t*c)/h,this._x=this._x*l+n*t,this._y=this._y*l+s*t,this._z=this._z*l+r*t,this._w=this._w*l+a*t,this._onChangeCallback()}else this._x=this._x*l+n*t,this._y=this._y*l+s*t,this._z=this._z*l+r*t,this._w=this._w*l+a*t,this.normalize();return this}slerpQuaternions(e,t,n){return this.copy(e).slerp(t,n)}random(){let e=2*Math.PI*ut(),t=2*Math.PI*ut(),n=ut(),s=Math.sqrt(1-n),r=Math.sqrt(n);return this.set(s*Math.sin(e),s*Math.cos(e),r*Math.sin(t),r*Math.cos(t))}equals(e){return e._x===this._x&&e._y===this._y&&e._z===this._z&&e._w===this._w}fromArray(e,t=0){return this._x=e[t],this._y=e[t+1],this._z=e[t+2],this._w=e[t+3],this._onChangeCallback(),this}toArray(e=[],t=0){return e[t]=this._x,e[t+1]=this._y,e[t+2]=this._z,e[t+3]=this._w,e}fromBufferAttribute(e,t){return this._x=e.getX(t),this._y=e.getY(t),this._z=e.getZ(t),this._w=e.getW(t),this._onChangeCallback(),this}toJSON(){return this.toArray()}_onChange(e){return this._onChangeCallback=e,this}_onChangeCallback(){}*[Symbol.iterator](){yield this._x,yield this._y,yield this._z,yield this._w}},D=class i{static{i.prototype.isVector3=!0}constructor(e=0,t=0,n=0){this.x=e,this.y=t,this.z=n}set(e,t,n){return n===void 0&&(n=this.z),this.x=e,this.y=t,this.z=n,this}setScalar(e){return this.x=e,this.y=e,this.z=e,this}setX(e){return this.x=e,this}setY(e){return this.y=e,this}setZ(e){return this.z=e,this}setComponent(e,t){switch(e){case 0:this.x=t;break;case 1:this.y=t;break;case 2:this.z=t;break;default:throw new Error("THREE.Vector3: index is out of range: "+e)}return this}getComponent(e){switch(e){case 0:return this.x;case 1:return this.y;case 2:return this.z;default:throw new Error("THREE.Vector3: index is out of range: "+e)}}clone(){return new this.constructor(this.x,this.y,this.z)}copy(e){return this.x=e.x,this.y=e.y,this.z=e.z,this}add(e){return this.x+=e.x,this.y+=e.y,this.z+=e.z,this}addScalar(e){return this.x+=e,this.y+=e,this.z+=e,this}addVectors(e,t){return this.x=e.x+t.x,this.y=e.y+t.y,this.z=e.z+t.z,this}addScaledVector(e,t){return this.x+=e.x*t,this.y+=e.y*t,this.z+=e.z*t,this}sub(e){return this.x-=e.x,this.y-=e.y,this.z-=e.z,this}subScalar(e){return this.x-=e,this.y-=e,this.z-=e,this}subVectors(e,t){return this.x=e.x-t.x,this.y=e.y-t.y,this.z=e.z-t.z,this}multiply(e){return this.x*=e.x,this.y*=e.y,this.z*=e.z,this}multiplyScalar(e){return this.x*=e,this.y*=e,this.z*=e,this}multiplyVectors(e,t){return this.x=e.x*t.x,this.y=e.y*t.y,this.z=e.z*t.z,this}applyEuler(e){return this.applyQuaternion(Bc.setFromEuler(e))}applyAxisAngle(e,t){return this.applyQuaternion(Bc.setFromAxisAngle(e,t))}applyMatrix3(e){let t=this.x,n=this.y,s=this.z,r=e.elements;return this.x=r[0]*t+r[3]*n+r[6]*s,this.y=r[1]*t+r[4]*n+r[7]*s,this.z=r[2]*t+r[5]*n+r[8]*s,this}applyNormalMatrix(e){return this.applyMatrix3(e).normalize()}applyMatrix4(e){let t=this.x,n=this.y,s=this.z,r=e.elements,a=1/(r[3]*t+r[7]*n+r[11]*s+r[15]);return this.x=(r[0]*t+r[4]*n+r[8]*s+r[12])*a,this.y=(r[1]*t+r[5]*n+r[9]*s+r[13])*a,this.z=(r[2]*t+r[6]*n+r[10]*s+r[14])*a,this}applyQuaternion(e){let t=this.x,n=this.y,s=this.z,r=e.x,a=e.y,o=e.z,l=e.w,c=2*(a*s-o*n),h=2*(o*t-r*s),f=2*(r*n-a*t);return this.x=t+l*c+a*f-o*h,this.y=n+l*h+o*c-r*f,this.z=s+l*f+r*h-a*c,this}project(e){return this.applyMatrix4(e.matrixWorldInverse).applyMatrix4(e.projectionMatrix)}unproject(e){return this.applyMatrix4(e.projectionMatrixInverse).applyMatrix4(e.matrixWorld)}transformDirection(e){let t=this.x,n=this.y,s=this.z,r=e.elements;return this.x=r[0]*t+r[4]*n+r[8]*s,this.y=r[1]*t+r[5]*n+r[9]*s,this.z=r[2]*t+r[6]*n+r[10]*s,this.normalize()}divide(e){return this.x/=e.x,this.y/=e.y,this.z/=e.z,this}divideScalar(e){return this.multiplyScalar(1/e)}min(e){return this.x=Math.min(this.x,e.x),this.y=Math.min(this.y,e.y),this.z=Math.min(this.z,e.z),this}max(e){return this.x=Math.max(this.x,e.x),this.y=Math.max(this.y,e.y),this.z=Math.max(this.z,e.z),this}clamp(e,t){return this.x=ft(this.x,e.x,t.x),this.y=ft(this.y,e.y,t.y),this.z=ft(this.z,e.z,t.z),this}clampScalar(e,t){return this.x=ft(this.x,e,t),this.y=ft(this.y,e,t),this.z=ft(this.z,e,t),this}clampLength(e,t){let n=this.length();return this.divideScalar(n||1).multiplyScalar(ft(n,e,t))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this.z=Math.floor(this.z),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this.z=Math.ceil(this.z),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this.z=Math.round(this.z),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this.z=Math.trunc(this.z),this}negate(){return this.x=-this.x,this.y=-this.y,this.z=-this.z,this}dot(e){return this.x*e.x+this.y*e.y+this.z*e.z}lengthSq(){return this.x*this.x+this.y*this.y+this.z*this.z}length(){return Math.sqrt(this.x*this.x+this.y*this.y+this.z*this.z)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)+Math.abs(this.z)}normalize(){return this.divideScalar(this.length()||1)}setLength(e){return this.normalize().multiplyScalar(e)}lerp(e,t){return this.x+=(e.x-this.x)*t,this.y+=(e.y-this.y)*t,this.z+=(e.z-this.z)*t,this}lerpVectors(e,t,n){return this.x=e.x+(t.x-e.x)*n,this.y=e.y+(t.y-e.y)*n,this.z=e.z+(t.z-e.z)*n,this}cross(e){return this.crossVectors(this,e)}crossVectors(e,t){let n=e.x,s=e.y,r=e.z,a=t.x,o=t.y,l=t.z;return this.x=s*l-r*o,this.y=r*a-n*l,this.z=n*o-s*a,this}projectOnVector(e){let t=e.lengthSq();if(t===0)return this.set(0,0,0);let n=e.dot(this)/t;return this.copy(e).multiplyScalar(n)}projectOnPlane(e){return ml.copy(this).projectOnVector(e),this.sub(ml)}reflect(e){return this.sub(ml.copy(e).multiplyScalar(2*this.dot(e)))}angleTo(e){let t=Math.sqrt(this.lengthSq()*e.lengthSq());if(t===0)return Math.PI/2;let n=this.dot(e)/t;return Math.acos(ft(n,-1,1))}distanceTo(e){return Math.sqrt(this.distanceToSquared(e))}distanceToSquared(e){let t=this.x-e.x,n=this.y-e.y,s=this.z-e.z;return t*t+n*n+s*s}manhattanDistanceTo(e){return Math.abs(this.x-e.x)+Math.abs(this.y-e.y)+Math.abs(this.z-e.z)}setFromSpherical(e){return this.setFromSphericalCoords(e.radius,e.phi,e.theta)}setFromSphericalCoords(e,t,n){let s=Math.sin(t)*e;return this.x=s*Math.sin(n),this.y=Math.cos(t)*e,this.z=s*Math.cos(n),this}setFromCylindrical(e){return this.setFromCylindricalCoords(e.radius,e.theta,e.y)}setFromCylindricalCoords(e,t,n){return this.x=e*Math.sin(t),this.y=n,this.z=e*Math.cos(t),this}setFromMatrixPosition(e){let t=e.elements;return this.x=t[12],this.y=t[13],this.z=t[14],this}setFromMatrixScale(e){let t=this.setFromMatrixColumn(e,0).length(),n=this.setFromMatrixColumn(e,1).length(),s=this.setFromMatrixColumn(e,2).length();return this.x=t,this.y=n,this.z=s,this}setFromMatrixColumn(e,t){return this.fromArray(e.elements,t*4)}setFromMatrix3Column(e,t){return this.fromArray(e.elements,t*3)}setFromEuler(e){return this.x=e._x,this.y=e._y,this.z=e._z,this}setFromColor(e){return this.x=e.r,this.y=e.g,this.z=e.b,this}equals(e){return e.x===this.x&&e.y===this.y&&e.z===this.z}fromArray(e,t=0){return this.x=e[t],this.y=e[t+1],this.z=e[t+2],this}toArray(e=[],t=0){return e[t]=this.x,e[t+1]=this.y,e[t+2]=this.z,e}fromBufferAttribute(e,t){return this.x=e.getX(t),this.y=e.getY(t),this.z=e.getZ(t),this}random(){return this.x=ut(),this.y=ut(),this.z=ut(),this}randomDirection(){let e=ut()*Math.PI*2,t=ut()*2-1,n=Math.sqrt(1-t*t);return this.x=n*Math.cos(e),this.y=t,this.z=n*Math.sin(e),this}*[Symbol.iterator](){yield this.x,yield this.y,yield this.z}},ml=new D,Bc=new Gt,nt=class i{static{i.prototype.isMatrix3=!0}constructor(e,t,n,s,r,a,o,l,c){this.elements=[1,0,0,0,1,0,0,0,1],e!==void 0&&this.set(e,t,n,s,r,a,o,l,c)}set(e,t,n,s,r,a,o,l,c){let h=this.elements;return h[0]=e,h[1]=s,h[2]=o,h[3]=t,h[4]=r,h[5]=l,h[6]=n,h[7]=a,h[8]=c,this}identity(){return this.set(1,0,0,0,1,0,0,0,1),this}copy(e){let t=this.elements,n=e.elements;return t[0]=n[0],t[1]=n[1],t[2]=n[2],t[3]=n[3],t[4]=n[4],t[5]=n[5],t[6]=n[6],t[7]=n[7],t[8]=n[8],this}extractBasis(e,t,n){return e.setFromMatrix3Column(this,0),t.setFromMatrix3Column(this,1),n.setFromMatrix3Column(this,2),this}setFromMatrix4(e){let t=e.elements;return this.set(t[0],t[4],t[8],t[1],t[5],t[9],t[2],t[6],t[10]),this}multiply(e){return this.multiplyMatrices(this,e)}premultiply(e){return this.multiplyMatrices(e,this)}multiplyMatrices(e,t){let n=e.elements,s=t.elements,r=this.elements,a=n[0],o=n[3],l=n[6],c=n[1],h=n[4],f=n[7],u=n[2],d=n[5],g=n[8],M=s[0],m=s[3],p=s[6],T=s[1],C=s[4],v=s[7],w=s[2],S=s[5],I=s[8];return r[0]=a*M+o*T+l*w,r[3]=a*m+o*C+l*S,r[6]=a*p+o*v+l*I,r[1]=c*M+h*T+f*w,r[4]=c*m+h*C+f*S,r[7]=c*p+h*v+f*I,r[2]=u*M+d*T+g*w,r[5]=u*m+d*C+g*S,r[8]=u*p+d*v+g*I,this}multiplyScalar(e){let t=this.elements;return t[0]*=e,t[3]*=e,t[6]*=e,t[1]*=e,t[4]*=e,t[7]*=e,t[2]*=e,t[5]*=e,t[8]*=e,this}determinant(){let e=this.elements,t=e[0],n=e[1],s=e[2],r=e[3],a=e[4],o=e[5],l=e[6],c=e[7],h=e[8];return t*a*h-t*o*c-n*r*h+n*o*l+s*r*c-s*a*l}invert(){let e=this.elements,t=e[0],n=e[1],s=e[2],r=e[3],a=e[4],o=e[5],l=e[6],c=e[7],h=e[8],f=h*a-o*c,u=o*l-h*r,d=c*r-a*l,g=t*f+n*u+s*d;if(g===0)return this.set(0,0,0,0,0,0,0,0,0);let M=1/g;return e[0]=f*M,e[1]=(s*c-h*n)*M,e[2]=(o*n-s*a)*M,e[3]=u*M,e[4]=(h*t-s*l)*M,e[5]=(s*r-o*t)*M,e[6]=d*M,e[7]=(n*l-c*t)*M,e[8]=(a*t-n*r)*M,this}transpose(){let e,t=this.elements;return e=t[1],t[1]=t[3],t[3]=e,e=t[2],t[2]=t[6],t[6]=e,e=t[5],t[5]=t[7],t[7]=e,this}getNormalMatrix(e){return this.setFromMatrix4(e).invert().transpose()}transposeIntoArray(e){let t=this.elements;return e[0]=t[0],e[1]=t[3],e[2]=t[6],e[3]=t[1],e[4]=t[4],e[5]=t[7],e[6]=t[2],e[7]=t[5],e[8]=t[8],this}setUvTransform(e,t,n,s,r,a,o){let l=Math.cos(r),c=Math.sin(r);return this.set(n*l,n*c,-n*(l*a+c*o)+a+e,-s*c,s*l,-s*(-c*a+l*o)+o+t,0,0,1),this}scale(e,t){return Oi("Matrix3: .scale() is deprecated. Use .makeScale() instead."),this.premultiply(gl.makeScale(e,t)),this}rotate(e){return Oi("Matrix3: .rotate() is deprecated. Use .makeRotation() instead."),this.premultiply(gl.makeRotation(-e)),this}translate(e,t){return Oi("Matrix3: .translate() is deprecated. Use .makeTranslation() instead."),this.premultiply(gl.makeTranslation(e,t)),this}makeTranslation(e,t){return e.isVector2?this.set(1,0,e.x,0,1,e.y,0,0,1):this.set(1,0,e,0,1,t,0,0,1),this}makeRotation(e){let t=Math.cos(e),n=Math.sin(e);return this.set(t,-n,0,n,t,0,0,0,1),this}makeScale(e,t){return this.set(e,0,0,0,t,0,0,0,1),this}equals(e){let t=this.elements,n=e.elements;for(let s=0;s<9;s++)if(t[s]!==n[s])return!1;return!0}fromArray(e,t=0){for(let n=0;n<9;n++)this.elements[n]=e[n+t];return this}toArray(e=[],t=0){let n=this.elements;return e[t]=n[0],e[t+1]=n[1],e[t+2]=n[2],e[t+3]=n[3],e[t+4]=n[4],e[t+5]=n[5],e[t+6]=n[6],e[t+7]=n[7],e[t+8]=n[8],e}clone(){return new this.constructor().fromArray(this.elements)}},gl=new nt,zc=new nt().set(.4123908,.3575843,.1804808,.212639,.7151687,.0721923,.0193308,.1191948,.9505322),Vc=new nt().set(3.2409699,-1.5373832,-.4986108,-.9692436,1.8759675,.0415551,.0556301,-.203977,1.0569715);function dd(){let i={enabled:!0,workingColorSpace:ir,spaces:{},convert:function(s,r,a){return this.enabled===!1||r===a||!r||!a||(this.spaces[r].transfer===bt&&(s.r=si(s.r),s.g=si(s.g),s.b=si(s.b)),this.spaces[r].primaries!==this.spaces[a].primaries&&(s.applyMatrix3(this.spaces[r].toXYZ),s.applyMatrix3(this.spaces[a].fromXYZ)),this.spaces[a].transfer===bt&&(s.r=ms(s.r),s.g=ms(s.g),s.b=ms(s.b))),s},workingToColorSpace:function(s,r){return this.convert(s,this.workingColorSpace,r)},colorSpaceToWorking:function(s,r){return this.convert(s,r,this.workingColorSpace)},getPrimaries:function(s){return this.spaces[s].primaries},getTransfer:function(s){return s===oi?sr:this.spaces[s].transfer},getToneMappingMode:function(s){return this.spaces[s].outputColorSpaceConfig.toneMappingMode||"standard"},getLuminanceCoefficients:function(s,r=this.workingColorSpace){return s.fromArray(this.spaces[r].luminanceCoefficients)},define:function(s){Object.assign(this.spaces,s)},_getMatrix:function(s,r,a){return s.copy(this.spaces[r].toXYZ).multiply(this.spaces[a].fromXYZ)},_getDrawingBufferColorSpace:function(s){return this.spaces[s].outputColorSpaceConfig.drawingBufferColorSpace},_getUnpackColorSpace:function(s=this.workingColorSpace){return this.spaces[s].workingColorSpaceConfig.unpackColorSpace},fromWorkingColorSpace:function(s,r){return Oi("ColorManagement: .fromWorkingColorSpace() has been renamed to .workingToColorSpace()."),i.workingToColorSpace(s,r)},toWorkingColorSpace:function(s,r){return Oi("ColorManagement: .toWorkingColorSpace() has been renamed to .colorSpaceToWorking()."),i.colorSpaceToWorking(s,r)}},e=[.64,.33,.3,.6,.15,.06],t=[.2126,.7152,.0722],n=[.3127,.329];return i.define({[ir]:{primaries:e,whitePoint:n,transfer:sr,toXYZ:zc,fromXYZ:Vc,luminanceCoefficients:t,workingColorSpaceConfig:{unpackColorSpace:dn},outputColorSpaceConfig:{drawingBufferColorSpace:dn}},[dn]:{primaries:e,whitePoint:n,transfer:bt,toXYZ:zc,fromXYZ:Vc,luminanceCoefficients:t,outputColorSpaceConfig:{drawingBufferColorSpace:dn}}}),i}var dt=dd();function si(i){return i<.04045?i*.0773993808:Math.pow(i*.9478672986+.0521327014,2.4)}function ms(i){return i<.0031308?i*12.92:1.055*Math.pow(i,.41666)-.055}var es,Fa=class{static getDataURL(e,t="image/png"){if(/^data:/i.test(e.src)||typeof HTMLCanvasElement>"u")return e.src;let n;if(e instanceof HTMLCanvasElement)n=e;else{es===void 0&&(es=rr("canvas")),es.width=e.width,es.height=e.height;let s=es.getContext("2d");e instanceof ImageData?s.putImageData(e,0,0):s.drawImage(e,0,0,e.width,e.height),n=es}return n.toDataURL(t)}static sRGBToLinear(e){if(typeof HTMLImageElement<"u"&&e instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&e instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&e instanceof ImageBitmap){let t=rr("canvas");t.width=e.width,t.height=e.height;let n=t.getContext("2d");n.drawImage(e,0,0,e.width,e.height);let s=n.getImageData(0,0,e.width,e.height),r=s.data;for(let a=0;a<r.length;a++)r[a]=si(r[a]/255)*255;return n.putImageData(s,0,0),t}else if(e.data){let t=e.data.slice(0);for(let n=0;n<t.length;n++)t instanceof Uint8Array||t instanceof Uint8ClampedArray?t[n]=Math.floor(si(t[n]/255)*255):t[n]=si(t[n]);return{data:t,width:e.width,height:e.height}}else return Je("ImageUtils.sRGBToLinear(): Unsupported image type. No color space conversion applied."),e}},fd=0,ys=class{constructor(e=null){this.isTextureSource=!0,Object.defineProperty(this,"id",{value:fd++}),this.uuid=Ds(),this.data=e,this.dataReady=!0,this.version=0}getSize(e){let t=this.data;return typeof HTMLVideoElement<"u"&&t instanceof HTMLVideoElement?e.set(t.videoWidth,t.videoHeight,0):typeof VideoFrame<"u"&&t instanceof VideoFrame?e.set(t.displayWidth,t.displayHeight,0):t!==null?e.set(t.width,t.height,t.depth||0):e.set(0,0,0),e}set needsUpdate(e){e===!0&&this.version++}toJSON(e){let t=e===void 0||typeof e=="string";if(!t&&e.images[this.uuid]!==void 0)return e.images[this.uuid];let n={uuid:this.uuid,url:""},s=this.data;if(s!==null){let r;if(Array.isArray(s)){r=[];for(let a=0,o=s.length;a<o;a++)s[a].isDataTexture?r.push(_l(s[a].image)):r.push(_l(s[a]))}else r=_l(s);n.url=r}return t||(e.images[this.uuid]=n),n}};function _l(i){return typeof HTMLImageElement<"u"&&i instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&i instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&i instanceof ImageBitmap?Fa.getDataURL(i):i.data?{data:Array.from(i.data),width:i.width,height:i.height,type:i.data.constructor.name}:(Je("Texture: Unable to serialize Texture."),{})}var pd=0,xl=new D,mn=class i extends Wn{constructor(e=i.DEFAULT_IMAGE,t=i.DEFAULT_MAPPING,n=Hn,s=Hn,r=Qt,a=wi,o=Pn,l=xn,c=i.DEFAULT_ANISOTROPY,h=oi){super(),this.isTexture=!0,Object.defineProperty(this,"id",{value:pd++}),this.uuid=Ds(),this.name="",this.source=new ys(e),this.mipmaps=[],this.mapping=t,this.channel=0,this.wrapS=n,this.wrapT=s,this.magFilter=r,this.minFilter=a,this.anisotropy=c,this.format=o,this.internalFormat=null,this.type=l,this.offset=new Ue(0,0),this.repeat=new Ue(1,1),this.center=new Ue(0,0),this.rotation=0,this.matrixAutoUpdate=!0,this.matrix=new nt,this.generateMipmaps=!0,this.premultiplyAlpha=!1,this.flipY=!0,this.unpackAlignment=4,this.colorSpace=h,this.userData={},this.updateRanges=[],this.version=0,this.onUpdate=null,this.renderTarget=null,this.isRenderTargetTexture=!1,this.isArrayTexture=!!(e&&e.depth&&e.depth>1),this.pmremVersion=0,this.normalized=!1}get width(){return this.source.getSize(xl).x}get height(){return this.source.getSize(xl).y}get depth(){return this.source.getSize(xl).z}get image(){return this.source.data}set image(e){this.source.data=e}updateMatrix(){this.matrix.setUvTransform(this.offset.x,this.offset.y,this.repeat.x,this.repeat.y,this.rotation,this.center.x,this.center.y)}addUpdateRange(e,t){this.updateRanges.push({start:e,count:t})}clearUpdateRanges(){this.updateRanges.length=0}clone(){return new this.constructor().copy(this)}copy(e){return this.name=e.name,this.source=e.source,this.mipmaps=e.mipmaps.slice(0),this.mapping=e.mapping,this.channel=e.channel,this.wrapS=e.wrapS,this.wrapT=e.wrapT,this.magFilter=e.magFilter,this.minFilter=e.minFilter,this.anisotropy=e.anisotropy,this.format=e.format,this.internalFormat=e.internalFormat,this.type=e.type,this.normalized=e.normalized,this.offset.copy(e.offset),this.repeat.copy(e.repeat),this.center.copy(e.center),this.rotation=e.rotation,this.matrixAutoUpdate=e.matrixAutoUpdate,this.matrix.copy(e.matrix),this.generateMipmaps=e.generateMipmaps,this.premultiplyAlpha=e.premultiplyAlpha,this.flipY=e.flipY,this.unpackAlignment=e.unpackAlignment,this.colorSpace=e.colorSpace,this.renderTarget=e.renderTarget,this.isRenderTargetTexture=e.isRenderTargetTexture,this.isArrayTexture=e.isArrayTexture,this.userData=JSON.parse(JSON.stringify(e.userData)),this.needsUpdate=!0,this}setValues(e){for(let t in e){let n=e[t];if(n===void 0){Je(`Texture.setValues(): parameter '${t}' has value of undefined.`);continue}let s=this[t];if(s===void 0){Je(`Texture.setValues(): property '${t}' does not exist.`);continue}s&&n&&s.isVector2&&n.isVector2||s&&n&&s.isVector3&&n.isVector3||s&&n&&s.isMatrix3&&n.isMatrix3?s.copy(n):this[t]=n}}toJSON(e){let t=e===void 0||typeof e=="string";if(!t&&e.textures[this.uuid]!==void 0)return e.textures[this.uuid];let n={metadata:{version:4.7,type:"Texture",generator:"Texture.toJSON"},uuid:this.uuid,name:this.name,image:this.source.toJSON(e).uuid,mapping:this.mapping,channel:this.channel,repeat:[this.repeat.x,this.repeat.y],offset:[this.offset.x,this.offset.y],center:[this.center.x,this.center.y],rotation:this.rotation,wrap:[this.wrapS,this.wrapT],format:this.format,internalFormat:this.internalFormat,type:this.type,normalized:this.normalized,colorSpace:this.colorSpace,minFilter:this.minFilter,magFilter:this.magFilter,anisotropy:this.anisotropy,flipY:this.flipY,generateMipmaps:this.generateMipmaps,premultiplyAlpha:this.premultiplyAlpha,unpackAlignment:this.unpackAlignment};return Object.keys(this.userData).length>0&&(n.userData=this.userData),t||(e.textures[this.uuid]=n),n}dispose(){this.dispatchEvent({type:"dispose"})}transformUv(e){if(this.mapping!==tc)return e;if(e.applyMatrix3(this.matrix),e.x<0||e.x>1)switch(this.wrapS){case Na:e.x=e.x-Math.floor(e.x);break;case Hn:e.x=e.x<0?0:1;break;case Da:Math.abs(Math.floor(e.x)%2)===1?e.x=Math.ceil(e.x)-e.x:e.x=e.x-Math.floor(e.x);break}if(e.y<0||e.y>1)switch(this.wrapT){case Na:e.y=e.y-Math.floor(e.y);break;case Hn:e.y=e.y<0?0:1;break;case Da:Math.abs(Math.floor(e.y)%2)===1?e.y=Math.ceil(e.y)-e.y:e.y=e.y-Math.floor(e.y);break}return this.flipY&&(e.y=1-e.y),e}set needsUpdate(e){e===!0&&(this.version++,this.source.needsUpdate=!0)}set needsPMREMUpdate(e){e===!0&&this.pmremVersion++}};mn.DEFAULT_IMAGE=null;mn.DEFAULT_MAPPING=tc;mn.DEFAULT_ANISOTROPY=1;var Dt=class i{static{i.prototype.isVector4=!0}constructor(e=0,t=0,n=0,s=1){this.x=e,this.y=t,this.z=n,this.w=s}get width(){return this.z}set width(e){this.z=e}get height(){return this.w}set height(e){this.w=e}set(e,t,n,s){return this.x=e,this.y=t,this.z=n,this.w=s,this}setScalar(e){return this.x=e,this.y=e,this.z=e,this.w=e,this}setX(e){return this.x=e,this}setY(e){return this.y=e,this}setZ(e){return this.z=e,this}setW(e){return this.w=e,this}setComponent(e,t){switch(e){case 0:this.x=t;break;case 1:this.y=t;break;case 2:this.z=t;break;case 3:this.w=t;break;default:throw new Error("THREE.Vector4: index is out of range: "+e)}return this}getComponent(e){switch(e){case 0:return this.x;case 1:return this.y;case 2:return this.z;case 3:return this.w;default:throw new Error("THREE.Vector4: index is out of range: "+e)}}clone(){return new this.constructor(this.x,this.y,this.z,this.w)}copy(e){return this.x=e.x,this.y=e.y,this.z=e.z,this.w=e.w!==void 0?e.w:1,this}add(e){return this.x+=e.x,this.y+=e.y,this.z+=e.z,this.w+=e.w,this}addScalar(e){return this.x+=e,this.y+=e,this.z+=e,this.w+=e,this}addVectors(e,t){return this.x=e.x+t.x,this.y=e.y+t.y,this.z=e.z+t.z,this.w=e.w+t.w,this}addScaledVector(e,t){return this.x+=e.x*t,this.y+=e.y*t,this.z+=e.z*t,this.w+=e.w*t,this}sub(e){return this.x-=e.x,this.y-=e.y,this.z-=e.z,this.w-=e.w,this}subScalar(e){return this.x-=e,this.y-=e,this.z-=e,this.w-=e,this}subVectors(e,t){return this.x=e.x-t.x,this.y=e.y-t.y,this.z=e.z-t.z,this.w=e.w-t.w,this}multiply(e){return this.x*=e.x,this.y*=e.y,this.z*=e.z,this.w*=e.w,this}multiplyScalar(e){return this.x*=e,this.y*=e,this.z*=e,this.w*=e,this}applyMatrix4(e){let t=this.x,n=this.y,s=this.z,r=this.w,a=e.elements;return this.x=a[0]*t+a[4]*n+a[8]*s+a[12]*r,this.y=a[1]*t+a[5]*n+a[9]*s+a[13]*r,this.z=a[2]*t+a[6]*n+a[10]*s+a[14]*r,this.w=a[3]*t+a[7]*n+a[11]*s+a[15]*r,this}divide(e){return this.x/=e.x,this.y/=e.y,this.z/=e.z,this.w/=e.w,this}divideScalar(e){return this.multiplyScalar(1/e)}setAxisAngleFromQuaternion(e){this.w=2*Math.acos(e.w);let t=Math.sqrt(1-e.w*e.w);return t<1e-4?(this.x=1,this.y=0,this.z=0):(this.x=e.x/t,this.y=e.y/t,this.z=e.z/t),this}setAxisAngleFromRotationMatrix(e){let t,n,s,r,l=e.elements,c=l[0],h=l[4],f=l[8],u=l[1],d=l[5],g=l[9],M=l[2],m=l[6],p=l[10];if(Math.abs(h-u)<.01&&Math.abs(f-M)<.01&&Math.abs(g-m)<.01){if(Math.abs(h+u)<.1&&Math.abs(f+M)<.1&&Math.abs(g+m)<.1&&Math.abs(c+d+p-3)<.1)return this.set(1,0,0,0),this;t=Math.PI;let C=(c+1)/2,v=(d+1)/2,w=(p+1)/2,S=(h+u)/4,I=(f+M)/4,x=(g+m)/4;return C>v&&C>w?C<.01?(n=0,s=.707106781,r=.707106781):(n=Math.sqrt(C),s=S/n,r=I/n):v>w?v<.01?(n=.707106781,s=0,r=.707106781):(s=Math.sqrt(v),n=S/s,r=x/s):w<.01?(n=.707106781,s=.707106781,r=0):(r=Math.sqrt(w),n=I/r,s=x/r),this.set(n,s,r,t),this}let T=Math.sqrt((m-g)*(m-g)+(f-M)*(f-M)+(u-h)*(u-h));return Math.abs(T)<.001&&(T=1),this.x=(m-g)/T,this.y=(f-M)/T,this.z=(u-h)/T,this.w=Math.acos((c+d+p-1)/2),this}setFromMatrixPosition(e){let t=e.elements;return this.x=t[12],this.y=t[13],this.z=t[14],this.w=t[15],this}min(e){return this.x=Math.min(this.x,e.x),this.y=Math.min(this.y,e.y),this.z=Math.min(this.z,e.z),this.w=Math.min(this.w,e.w),this}max(e){return this.x=Math.max(this.x,e.x),this.y=Math.max(this.y,e.y),this.z=Math.max(this.z,e.z),this.w=Math.max(this.w,e.w),this}clamp(e,t){return this.x=ft(this.x,e.x,t.x),this.y=ft(this.y,e.y,t.y),this.z=ft(this.z,e.z,t.z),this.w=ft(this.w,e.w,t.w),this}clampScalar(e,t){return this.x=ft(this.x,e,t),this.y=ft(this.y,e,t),this.z=ft(this.z,e,t),this.w=ft(this.w,e,t),this}clampLength(e,t){let n=this.length();return this.divideScalar(n||1).multiplyScalar(ft(n,e,t))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this.z=Math.floor(this.z),this.w=Math.floor(this.w),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this.z=Math.ceil(this.z),this.w=Math.ceil(this.w),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this.z=Math.round(this.z),this.w=Math.round(this.w),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this.z=Math.trunc(this.z),this.w=Math.trunc(this.w),this}negate(){return this.x=-this.x,this.y=-this.y,this.z=-this.z,this.w=-this.w,this}dot(e){return this.x*e.x+this.y*e.y+this.z*e.z+this.w*e.w}lengthSq(){return this.x*this.x+this.y*this.y+this.z*this.z+this.w*this.w}length(){return Math.sqrt(this.x*this.x+this.y*this.y+this.z*this.z+this.w*this.w)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)+Math.abs(this.z)+Math.abs(this.w)}normalize(){return this.divideScalar(this.length()||1)}setLength(e){return this.normalize().multiplyScalar(e)}lerp(e,t){return this.x+=(e.x-this.x)*t,this.y+=(e.y-this.y)*t,this.z+=(e.z-this.z)*t,this.w+=(e.w-this.w)*t,this}lerpVectors(e,t,n){return this.x=e.x+(t.x-e.x)*n,this.y=e.y+(t.y-e.y)*n,this.z=e.z+(t.z-e.z)*n,this.w=e.w+(t.w-e.w)*n,this}equals(e){return e.x===this.x&&e.y===this.y&&e.z===this.z&&e.w===this.w}fromArray(e,t=0){return this.x=e[t],this.y=e[t+1],this.z=e[t+2],this.w=e[t+3],this}toArray(e=[],t=0){return e[t]=this.x,e[t+1]=this.y,e[t+2]=this.z,e[t+3]=this.w,e}fromBufferAttribute(e,t){return this.x=e.getX(t),this.y=e.getY(t),this.z=e.getZ(t),this.w=e.getW(t),this}random(){return this.x=ut(),this.y=ut(),this.z=ut(),this.w=ut(),this}*[Symbol.iterator](){yield this.x,yield this.y,yield this.z,yield this.w}},ka=class extends Wn{constructor(e=1,t=1,n={}){super(),n=Object.assign({generateMipmaps:!1,internalFormat:null,minFilter:Qt,depthBuffer:!0,stencilBuffer:!1,resolveColorBuffer:!0,resolveDepthBuffer:!0,resolveStencilBuffer:!0,storeMultisampledColorBuffer:!0,storeMultisampledDepthBuffer:!0,storeMultisampledStencilBuffer:!0,depthTexture:null,samples:0,count:1,depth:1,multiview:!1,useArrayDepthTexture:!1},n),this.isRenderTarget=!0,this.width=e,this.height=t,this.depth=n.depth,this.scissor=new Dt(0,0,e,t),this.scissorTest=!1,this.viewport=new Dt(0,0,e,t),this.textures=[];let s={width:e,height:t,depth:n.depth},r=new mn(s),a=n.count;for(let o=0;o<a;o++)this.textures[o]=r.clone(),this.textures[o].isRenderTargetTexture=!0,this.textures[o].renderTarget=this;this._setTextureOptions(n),this.depthBuffer=n.depthBuffer,this.stencilBuffer=n.stencilBuffer,this.resolveColorBuffer=n.resolveColorBuffer,this.resolveDepthBuffer=n.resolveDepthBuffer,this.resolveStencilBuffer=n.resolveStencilBuffer,this.storeMultisampledColorBuffer=n.storeMultisampledColorBuffer,this.storeMultisampledDepthBuffer=n.storeMultisampledDepthBuffer,this.storeMultisampledStencilBuffer=n.storeMultisampledStencilBuffer,this._depthTexture=null,this.depthTexture=n.depthTexture,this.samples=n.samples,this.multiview=n.multiview,this.useArrayDepthTexture=n.useArrayDepthTexture}_setTextureOptions(e={}){let t={minFilter:Qt,generateMipmaps:!1,flipY:!1,internalFormat:null};e.mapping!==void 0&&(t.mapping=e.mapping),e.wrapS!==void 0&&(t.wrapS=e.wrapS),e.wrapT!==void 0&&(t.wrapT=e.wrapT),e.wrapR!==void 0&&(t.wrapR=e.wrapR),e.magFilter!==void 0&&(t.magFilter=e.magFilter),e.minFilter!==void 0&&(t.minFilter=e.minFilter),e.format!==void 0&&(t.format=e.format),e.type!==void 0&&(t.type=e.type),e.anisotropy!==void 0&&(t.anisotropy=e.anisotropy),e.colorSpace!==void 0&&(t.colorSpace=e.colorSpace),e.flipY!==void 0&&(t.flipY=e.flipY),e.generateMipmaps!==void 0&&(t.generateMipmaps=e.generateMipmaps),e.internalFormat!==void 0&&(t.internalFormat=e.internalFormat);for(let n=0;n<this.textures.length;n++)this.textures[n].setValues(t)}get texture(){return this.textures[0]}set texture(e){this.textures[0]=e}set depthTexture(e){this._depthTexture!==null&&this._depthTexture.renderTarget===this&&(this._depthTexture.renderTarget=null),e!==null&&e.renderTarget===null&&(e.renderTarget=this),this._depthTexture=e}get depthTexture(){return this._depthTexture}setSize(e,t,n=1){if(this.width!==e||this.height!==t||this.depth!==n){this.width=e,this.height=t,this.depth=n;for(let s=0,r=this.textures.length;s<r;s++)this.textures[s].image.width=e,this.textures[s].image.height=t,this.textures[s].image.depth=n,this.textures[s].isData3DTexture!==!0&&(this.textures[s].isArrayTexture=this.textures[s].image.depth>1);this.dispose()}this.viewport.set(0,0,e,t),this.scissor.set(0,0,e,t)}clone(){return new this.constructor().copy(this)}copy(e){this.width=e.width,this.height=e.height,this.depth=e.depth,this.scissor.copy(e.scissor),this.scissorTest=e.scissorTest,this.viewport.copy(e.viewport),this.textures.length=0;for(let t=0,n=e.textures.length;t<n;t++){this.textures[t]=e.textures[t].clone(),this.textures[t].isRenderTargetTexture=!0,this.textures[t].renderTarget=this;let s=Object.assign({},e.textures[t].image);this.textures[t].source=new ys(s)}if(this.depthBuffer=e.depthBuffer,this.stencilBuffer=e.stencilBuffer,this.resolveColorBuffer=e.resolveColorBuffer,this.resolveDepthBuffer=e.resolveDepthBuffer,this.resolveStencilBuffer=e.resolveStencilBuffer,this.storeMultisampledColorBuffer=e.storeMultisampledColorBuffer,this.storeMultisampledDepthBuffer=e.storeMultisampledDepthBuffer,this.storeMultisampledStencilBuffer=e.storeMultisampledStencilBuffer,e.depthTexture!==null)if(e.depthTexture.renderTarget===e){let t=e.depthTexture.clone();t.renderTarget=null,this.depthTexture=t}else this.depthTexture=e.depthTexture;return this.samples=e.samples,this.multiview=e.multiview,this.useArrayDepthTexture=e.useArrayDepthTexture,this}dispose(){this.dispatchEvent({type:"dispose"})}},Vt=class extends ka{constructor(e=1,t=1,n={}){super(e,t,n),this.isWebGLRenderTarget=!0}},ar=class extends mn{constructor(e=null,t=1,n=1,s=1){super(null),this.isDataArrayTexture=!0,this.image={data:e,width:t,height:n,depth:s},this.magFilter=Zt,this.minFilter=Zt,this.wrapR=Hn,this.generateMipmaps=!1,this.flipY=!1,this.unpackAlignment=1,this.layerUpdates=new Set}copy(e){return super.copy(e),this.wrapR=e.wrapR,this}addLayerUpdate(e){this.layerUpdates.add(e)}clearLayerUpdates(){this.layerUpdates.clear()}};var Oa=class extends mn{constructor(e=null,t=1,n=1,s=1){super(null),this.isData3DTexture=!0,this.image={data:e,width:t,height:n,depth:s},this.magFilter=Zt,this.minFilter=Zt,this.wrapR=Hn,this.generateMipmaps=!1,this.flipY=!1,this.unpackAlignment=1}copy(e){return super.copy(e),this.wrapR=e.wrapR,this}};var pt=class i{static{i.prototype.isMatrix4=!0}constructor(e,t,n,s,r,a,o,l,c,h,f,u,d,g,M,m){this.elements=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1],e!==void 0&&this.set(e,t,n,s,r,a,o,l,c,h,f,u,d,g,M,m)}set(e,t,n,s,r,a,o,l,c,h,f,u,d,g,M,m){let p=this.elements;return p[0]=e,p[4]=t,p[8]=n,p[12]=s,p[1]=r,p[5]=a,p[9]=o,p[13]=l,p[2]=c,p[6]=h,p[10]=f,p[14]=u,p[3]=d,p[7]=g,p[11]=M,p[15]=m,this}identity(){return this.set(1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1),this}clone(){return new i().fromArray(this.elements)}copy(e){let t=this.elements,n=e.elements;return t[0]=n[0],t[1]=n[1],t[2]=n[2],t[3]=n[3],t[4]=n[4],t[5]=n[5],t[6]=n[6],t[7]=n[7],t[8]=n[8],t[9]=n[9],t[10]=n[10],t[11]=n[11],t[12]=n[12],t[13]=n[13],t[14]=n[14],t[15]=n[15],this}copyPosition(e){let t=this.elements,n=e.elements;return t[12]=n[12],t[13]=n[13],t[14]=n[14],this}setFromMatrix3(e){let t=e.elements;return this.set(t[0],t[3],t[6],0,t[1],t[4],t[7],0,t[2],t[5],t[8],0,0,0,0,1),this}extractBasis(e,t,n){return this.determinantAffine()===0?(e.set(1,0,0),t.set(0,1,0),n.set(0,0,1),this):(e.setFromMatrixColumn(this,0),t.setFromMatrixColumn(this,1),n.setFromMatrixColumn(this,2),this)}makeBasis(e,t,n){return this.set(e.x,t.x,n.x,0,e.y,t.y,n.y,0,e.z,t.z,n.z,0,0,0,0,1),this}extractRotation(e){if(e.determinantAffine()===0)return this.identity();let t=this.elements,n=e.elements,s=1/ts.setFromMatrixColumn(e,0).length(),r=1/ts.setFromMatrixColumn(e,1).length(),a=1/ts.setFromMatrixColumn(e,2).length();return t[0]=n[0]*s,t[1]=n[1]*s,t[2]=n[2]*s,t[3]=0,t[4]=n[4]*r,t[5]=n[5]*r,t[6]=n[6]*r,t[7]=0,t[8]=n[8]*a,t[9]=n[9]*a,t[10]=n[10]*a,t[11]=0,t[12]=0,t[13]=0,t[14]=0,t[15]=1,this}makeRotationFromEuler(e){let t=this.elements,n=e.x,s=e.y,r=e.z,a=Math.cos(n),o=Math.sin(n),l=Math.cos(s),c=Math.sin(s),h=Math.cos(r),f=Math.sin(r);if(e.order==="XYZ"){let u=a*h,d=a*f,g=o*h,M=o*f;t[0]=l*h,t[4]=-l*f,t[8]=c,t[1]=d+g*c,t[5]=u-M*c,t[9]=-o*l,t[2]=M-u*c,t[6]=g+d*c,t[10]=a*l}else if(e.order==="YXZ"){let u=l*h,d=l*f,g=c*h,M=c*f;t[0]=u+M*o,t[4]=g*o-d,t[8]=a*c,t[1]=a*f,t[5]=a*h,t[9]=-o,t[2]=d*o-g,t[6]=M+u*o,t[10]=a*l}else if(e.order==="ZXY"){let u=l*h,d=l*f,g=c*h,M=c*f;t[0]=u-M*o,t[4]=-a*f,t[8]=g+d*o,t[1]=d+g*o,t[5]=a*h,t[9]=M-u*o,t[2]=-a*c,t[6]=o,t[10]=a*l}else if(e.order==="ZYX"){let u=a*h,d=a*f,g=o*h,M=o*f;t[0]=l*h,t[4]=g*c-d,t[8]=u*c+M,t[1]=l*f,t[5]=M*c+u,t[9]=d*c-g,t[2]=-c,t[6]=o*l,t[10]=a*l}else if(e.order==="YZX"){let u=a*l,d=a*c,g=o*l,M=o*c;t[0]=l*h,t[4]=M-u*f,t[8]=g*f+d,t[1]=f,t[5]=a*h,t[9]=-o*h,t[2]=-c*h,t[6]=d*f+g,t[10]=u-M*f}else if(e.order==="XZY"){let u=a*l,d=a*c,g=o*l,M=o*c;t[0]=l*h,t[4]=-f,t[8]=c*h,t[1]=u*f+M,t[5]=a*h,t[9]=d*f-g,t[2]=g*f-d,t[6]=o*h,t[10]=M*f+u}return t[3]=0,t[7]=0,t[11]=0,t[12]=0,t[13]=0,t[14]=0,t[15]=1,this}makeRotationFromQuaternion(e){return this.compose(md,e,gd)}lookAt(e,t,n){let s=this.elements;return yn.subVectors(e,t),yn.lengthSq()===0&&(yn.z=1),yn.normalize(),fi.crossVectors(n,yn),fi.lengthSq()===0&&(Math.abs(n.z)===1?yn.x+=1e-4:yn.z+=1e-4,yn.normalize(),fi.crossVectors(n,yn)),fi.normalize(),ea.crossVectors(yn,fi),s[0]=fi.x,s[4]=ea.x,s[8]=yn.x,s[1]=fi.y,s[5]=ea.y,s[9]=yn.y,s[2]=fi.z,s[6]=ea.z,s[10]=yn.z,this}multiply(e){return this.multiplyMatrices(this,e)}premultiply(e){return this.multiplyMatrices(e,this)}multiplyMatrices(e,t){let n=e.elements,s=t.elements,r=this.elements,a=n[0],o=n[4],l=n[8],c=n[12],h=n[1],f=n[5],u=n[9],d=n[13],g=n[2],M=n[6],m=n[10],p=n[14],T=n[3],C=n[7],v=n[11],w=n[15],S=s[0],I=s[4],x=s[8],A=s[12],N=s[1],k=s[5],V=s[9],$=s[13],U=s[2],W=s[6],ee=s[10],ie=s[14],Z=s[3],Q=s[7],ue=s[11],se=s[15];return r[0]=a*S+o*N+l*U+c*Z,r[4]=a*I+o*k+l*W+c*Q,r[8]=a*x+o*V+l*ee+c*ue,r[12]=a*A+o*$+l*ie+c*se,r[1]=h*S+f*N+u*U+d*Z,r[5]=h*I+f*k+u*W+d*Q,r[9]=h*x+f*V+u*ee+d*ue,r[13]=h*A+f*$+u*ie+d*se,r[2]=g*S+M*N+m*U+p*Z,r[6]=g*I+M*k+m*W+p*Q,r[10]=g*x+M*V+m*ee+p*ue,r[14]=g*A+M*$+m*ie+p*se,r[3]=T*S+C*N+v*U+w*Z,r[7]=T*I+C*k+v*W+w*Q,r[11]=T*x+C*V+v*ee+w*ue,r[15]=T*A+C*$+v*ie+w*se,this}multiplyScalar(e){let t=this.elements;return t[0]*=e,t[4]*=e,t[8]*=e,t[12]*=e,t[1]*=e,t[5]*=e,t[9]*=e,t[13]*=e,t[2]*=e,t[6]*=e,t[10]*=e,t[14]*=e,t[3]*=e,t[7]*=e,t[11]*=e,t[15]*=e,this}determinant(){let e=this.elements,t=e[0],n=e[4],s=e[8],r=e[12],a=e[1],o=e[5],l=e[9],c=e[13],h=e[2],f=e[6],u=e[10],d=e[14],g=e[3],M=e[7],m=e[11],p=e[15],T=l*d-c*u,C=o*d-c*f,v=o*u-l*f,w=a*d-c*h,S=a*u-l*h,I=a*f-o*h;return t*(M*T-m*C+p*v)-n*(g*T-m*w+p*S)+s*(g*C-M*w+p*I)-r*(g*v-M*S+m*I)}determinantAffine(){let e=this.elements,t=e[0],n=e[4],s=e[8],r=e[1],a=e[5],o=e[9],l=e[2],c=e[6],h=e[10];return t*(a*h-o*c)-n*(r*h-o*l)+s*(r*c-a*l)}transpose(){let e=this.elements,t;return t=e[1],e[1]=e[4],e[4]=t,t=e[2],e[2]=e[8],e[8]=t,t=e[6],e[6]=e[9],e[9]=t,t=e[3],e[3]=e[12],e[12]=t,t=e[7],e[7]=e[13],e[13]=t,t=e[11],e[11]=e[14],e[14]=t,this}setPosition(e,t,n){let s=this.elements;return e.isVector3?(s[12]=e.x,s[13]=e.y,s[14]=e.z):(s[12]=e,s[13]=t,s[14]=n),this}invert(){let e=this.elements,t=e[0],n=e[1],s=e[2],r=e[3],a=e[4],o=e[5],l=e[6],c=e[7],h=e[8],f=e[9],u=e[10],d=e[11],g=e[12],M=e[13],m=e[14],p=e[15],T=t*o-n*a,C=t*l-s*a,v=t*c-r*a,w=n*l-s*o,S=n*c-r*o,I=s*c-r*l,x=h*M-f*g,A=h*m-u*g,N=h*p-d*g,k=f*m-u*M,V=f*p-d*M,$=u*p-d*m,U=T*$-C*V+v*k+w*N-S*A+I*x;if(U===0)return this.set(0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0);let W=1/U;return e[0]=(o*$-l*V+c*k)*W,e[1]=(s*V-n*$-r*k)*W,e[2]=(M*I-m*S+p*w)*W,e[3]=(u*S-f*I-d*w)*W,e[4]=(l*N-a*$-c*A)*W,e[5]=(t*$-s*N+r*A)*W,e[6]=(m*v-g*I-p*C)*W,e[7]=(h*I-u*v+d*C)*W,e[8]=(a*V-o*N+c*x)*W,e[9]=(n*N-t*V-r*x)*W,e[10]=(g*S-M*v+p*T)*W,e[11]=(f*v-h*S-d*T)*W,e[12]=(o*A-a*k-l*x)*W,e[13]=(t*k-n*A+s*x)*W,e[14]=(M*C-g*w-m*T)*W,e[15]=(h*w-f*C+u*T)*W,this}scale(e){let t=this.elements,n=e.x,s=e.y,r=e.z;return t[0]*=n,t[4]*=s,t[8]*=r,t[1]*=n,t[5]*=s,t[9]*=r,t[2]*=n,t[6]*=s,t[10]*=r,t[3]*=n,t[7]*=s,t[11]*=r,this}getMaxScaleOnAxis(){let e=this.elements,t=e[0]*e[0]+e[1]*e[1]+e[2]*e[2],n=e[4]*e[4]+e[5]*e[5]+e[6]*e[6],s=e[8]*e[8]+e[9]*e[9]+e[10]*e[10];return Math.sqrt(Math.max(t,n,s))}makeTranslation(e,t,n){return e.isVector3?this.set(1,0,0,e.x,0,1,0,e.y,0,0,1,e.z,0,0,0,1):this.set(1,0,0,e,0,1,0,t,0,0,1,n,0,0,0,1),this}makeRotationX(e){let t=Math.cos(e),n=Math.sin(e);return this.set(1,0,0,0,0,t,-n,0,0,n,t,0,0,0,0,1),this}makeRotationY(e){let t=Math.cos(e),n=Math.sin(e);return this.set(t,0,n,0,0,1,0,0,-n,0,t,0,0,0,0,1),this}makeRotationZ(e){let t=Math.cos(e),n=Math.sin(e);return this.set(t,-n,0,0,n,t,0,0,0,0,1,0,0,0,0,1),this}makeRotationAxis(e,t){let n=Math.cos(t),s=Math.sin(t),r=1-n,a=e.x,o=e.y,l=e.z,c=r*a,h=r*o;return this.set(c*a+n,c*o-s*l,c*l+s*o,0,c*o+s*l,h*o+n,h*l-s*a,0,c*l-s*o,h*l+s*a,r*l*l+n,0,0,0,0,1),this}makeScale(e,t,n){return this.set(e,0,0,0,0,t,0,0,0,0,n,0,0,0,0,1),this}makeShear(e,t,n,s,r,a){return this.set(1,n,r,0,e,1,a,0,t,s,1,0,0,0,0,1),this}compose(e,t,n){let s=this.elements,r=t._x,a=t._y,o=t._z,l=t._w,c=r+r,h=a+a,f=o+o,u=r*c,d=r*h,g=r*f,M=a*h,m=a*f,p=o*f,T=l*c,C=l*h,v=l*f,w=n.x,S=n.y,I=n.z;return s[0]=(1-(M+p))*w,s[1]=(d+v)*w,s[2]=(g-C)*w,s[3]=0,s[4]=(d-v)*S,s[5]=(1-(u+p))*S,s[6]=(m+T)*S,s[7]=0,s[8]=(g+C)*I,s[9]=(m-T)*I,s[10]=(1-(u+M))*I,s[11]=0,s[12]=e.x,s[13]=e.y,s[14]=e.z,s[15]=1,this}decompose(e,t,n){let s=this.elements;e.x=s[12],e.y=s[13],e.z=s[14];let r=this.determinantAffine();if(r===0)return n.set(1,1,1),t.identity(),this;let a=ts.set(s[0],s[1],s[2]).length(),o=ts.set(s[4],s[5],s[6]).length(),l=ts.set(s[8],s[9],s[10]).length();r<0&&(a=-a),In.copy(this);let c=1/a,h=1/o,f=1/l;return In.elements[0]*=c,In.elements[1]*=c,In.elements[2]*=c,In.elements[4]*=h,In.elements[5]*=h,In.elements[6]*=h,In.elements[8]*=f,In.elements[9]*=f,In.elements[10]*=f,t.setFromRotationMatrix(In),n.x=a,n.y=o,n.z=l,this}makePerspective(e,t,n,s,r,a,o=Un,l=!1){let c=this.elements,h=2*r/(t-e),f=2*r/(n-s),u=(t+e)/(t-e),d=(n+s)/(n-s),g,M;if(l)g=r/(a-r),M=a*r/(a-r);else if(o===Un)g=-(a+r)/(a-r),M=-2*a*r/(a-r);else if(o===_s)g=-a/(a-r),M=-a*r/(a-r);else throw new Error("THREE.Matrix4.makePerspective(): Invalid coordinate system: "+o);return c[0]=h,c[4]=0,c[8]=u,c[12]=0,c[1]=0,c[5]=f,c[9]=d,c[13]=0,c[2]=0,c[6]=0,c[10]=g,c[14]=M,c[3]=0,c[7]=0,c[11]=-1,c[15]=0,this}makeOrthographic(e,t,n,s,r,a,o=Un,l=!1){let c=this.elements,h=2/(t-e),f=2/(n-s),u=-(t+e)/(t-e),d=-(n+s)/(n-s),g,M;if(l)g=1/(a-r),M=a/(a-r);else if(o===Un)g=-2/(a-r),M=-(a+r)/(a-r);else if(o===_s)g=-1/(a-r),M=-r/(a-r);else throw new Error("THREE.Matrix4.makeOrthographic(): Invalid coordinate system: "+o);return c[0]=h,c[4]=0,c[8]=0,c[12]=u,c[1]=0,c[5]=f,c[9]=0,c[13]=d,c[2]=0,c[6]=0,c[10]=g,c[14]=M,c[3]=0,c[7]=0,c[11]=0,c[15]=1,this}equals(e){let t=this.elements,n=e.elements;for(let s=0;s<16;s++)if(t[s]!==n[s])return!1;return!0}fromArray(e,t=0){for(let n=0;n<16;n++)this.elements[n]=e[n+t];return this}toArray(e=[],t=0){let n=this.elements;return e[t]=n[0],e[t+1]=n[1],e[t+2]=n[2],e[t+3]=n[3],e[t+4]=n[4],e[t+5]=n[5],e[t+6]=n[6],e[t+7]=n[7],e[t+8]=n[8],e[t+9]=n[9],e[t+10]=n[10],e[t+11]=n[11],e[t+12]=n[12],e[t+13]=n[13],e[t+14]=n[14],e[t+15]=n[15],e}},ts=new D,In=new pt,md=new D(0,0,0),gd=new D(1,1,1),fi=new D,ea=new D,yn=new D,Hc=new pt,Gc=new Gt,En=class i{constructor(e=0,t=0,n=0,s=i.DEFAULT_ORDER){this.isEuler=!0,this._x=e,this._y=t,this._z=n,this._order=s}get x(){return this._x}set x(e){this._x=e,this._onChangeCallback()}get y(){return this._y}set y(e){this._y=e,this._onChangeCallback()}get z(){return this._z}set z(e){this._z=e,this._onChangeCallback()}get order(){return this._order}set order(e){this._order=e,this._onChangeCallback()}set(e,t,n,s=this._order){return this._x=e,this._y=t,this._z=n,this._order=s,this._onChangeCallback(),this}clone(){return new this.constructor(this._x,this._y,this._z,this._order)}copy(e){return this._x=e._x,this._y=e._y,this._z=e._z,this._order=e._order,this._onChangeCallback(),this}setFromRotationMatrix(e,t=this._order,n=!0){let s=e.elements,r=s[0],a=s[4],o=s[8],l=s[1],c=s[5],h=s[9],f=s[2],u=s[6],d=s[10];switch(t){case"XYZ":this._y=Math.asin(ft(o,-1,1)),Math.abs(o)<.9999999?(this._x=Math.atan2(-h,d),this._z=Math.atan2(-a,r)):(this._x=Math.atan2(u,c),this._z=0);break;case"YXZ":this._x=Math.asin(-ft(h,-1,1)),Math.abs(h)<.9999999?(this._y=Math.atan2(o,d),this._z=Math.atan2(l,c)):(this._y=Math.atan2(-f,r),this._z=0);break;case"ZXY":this._x=Math.asin(ft(u,-1,1)),Math.abs(u)<.9999999?(this._y=Math.atan2(-f,d),this._z=Math.atan2(-a,c)):(this._y=0,this._z=Math.atan2(l,r));break;case"ZYX":this._y=Math.asin(-ft(f,-1,1)),Math.abs(f)<.9999999?(this._x=Math.atan2(u,d),this._z=Math.atan2(l,r)):(this._x=0,this._z=Math.atan2(-a,c));break;case"YZX":this._z=Math.asin(ft(l,-1,1)),Math.abs(l)<.9999999?(this._x=Math.atan2(-h,c),this._y=Math.atan2(-f,r)):(this._x=0,this._y=Math.atan2(o,d));break;case"XZY":this._z=Math.asin(-ft(a,-1,1)),Math.abs(a)<.9999999?(this._x=Math.atan2(u,c),this._y=Math.atan2(o,r)):(this._x=Math.atan2(-h,d),this._y=0);break;default:Je("Euler: .setFromRotationMatrix() encountered an unknown order: "+t)}return this._order=t,n===!0&&this._onChangeCallback(),this}setFromQuaternion(e,t,n){return Hc.makeRotationFromQuaternion(e),this.setFromRotationMatrix(Hc,t,n)}setFromVector3(e,t=this._order){return this.set(e.x,e.y,e.z,t)}reorder(e){return Gc.setFromEuler(this),this.setFromQuaternion(Gc,e)}equals(e){return e._x===this._x&&e._y===this._y&&e._z===this._z&&e._order===this._order}fromArray(e){return this._x=e[0],this._y=e[1],this._z=e[2],e[3]!==void 0&&(this._order=e[3]),this._onChangeCallback(),this}toArray(e=[],t=0){return e[t]=this._x,e[t+1]=this._y,e[t+2]=this._z,e[t+3]=this._order,e}_onChange(e){return this._onChangeCallback=e,this}_onChangeCallback(){}*[Symbol.iterator](){yield this._x,yield this._y,yield this._z,yield this._order}};En.DEFAULT_ORDER="XYZ";var Ms=class{constructor(){this.mask=1}set(e){this.mask=(1<<e|0)>>>0}enable(e){this.mask|=1<<e|0}enableAll(){this.mask=-1}toggle(e){this.mask^=1<<e|0}disable(e){this.mask&=~(1<<e|0)}disableAll(){this.mask=0}test(e){return(this.mask&e.mask)!==0}isEnabled(e){return(this.mask&(1<<e|0))!==0}},_d=0,Wc=new D,ns=new Gt,Qn=new pt,ta=new D,qs=new D,xd=new D,vd=new Gt,qc=new D(1,0,0),Xc=new D(0,1,0),$c=new D(0,0,1),Yc={type:"added"},yd={type:"removed"},is={type:"childadded",child:null},vl={type:"childremoved",child:null},Ht=class i extends Wn{constructor(){super(),this.isObject3D=!0,Object.defineProperty(this,"id",{value:_d++}),this.uuid=Ds(),this.name="",this.type="Object3D",this.parent=null,this.children=[],this.up=i.DEFAULT_UP.clone();let e=new D,t=new En,n=new Gt,s=new D(1,1,1);function r(){n.setFromEuler(t,!1)}function a(){t.setFromQuaternion(n,void 0,!1)}t._onChange(r),n._onChange(a),Object.defineProperties(this,{position:{configurable:!0,enumerable:!0,value:e},rotation:{configurable:!0,enumerable:!0,value:t},quaternion:{configurable:!0,enumerable:!0,value:n},scale:{configurable:!0,enumerable:!0,value:s},modelViewMatrix:{value:new pt},normalMatrix:{value:new nt}}),this.matrix=new pt,this.matrixWorld=new pt,this.matrixAutoUpdate=i.DEFAULT_MATRIX_AUTO_UPDATE,this.matrixWorldAutoUpdate=i.DEFAULT_MATRIX_WORLD_AUTO_UPDATE,this.matrixWorldNeedsUpdate=!1,this.layers=new Ms,this.visible=!0,this.castShadow=!1,this.receiveShadow=!1,this.frustumCulled=!0,this.renderOrder=0,this.animations=[],this.customDepthMaterial=void 0,this.customDistanceMaterial=void 0,this.static=!1,this.userData={},this.pivot=null}onBeforeShadow(){}onAfterShadow(){}onBeforeRender(){}onAfterRender(){}applyMatrix4(e){this.matrixAutoUpdate&&this.updateMatrix(),this.matrix.premultiply(e),this.matrix.decompose(this.position,this.quaternion,this.scale)}applyQuaternion(e){return this.quaternion.premultiply(e),this}setRotationFromAxisAngle(e,t){this.quaternion.setFromAxisAngle(e,t)}setRotationFromEuler(e){this.quaternion.setFromEuler(e,!0)}setRotationFromMatrix(e){this.quaternion.setFromRotationMatrix(e)}setRotationFromQuaternion(e){this.quaternion.copy(e)}rotateOnAxis(e,t){return ns.setFromAxisAngle(e,t),this.quaternion.multiply(ns),this}rotateOnWorldAxis(e,t){return ns.setFromAxisAngle(e,t),this.quaternion.premultiply(ns),this}rotateX(e){return this.rotateOnAxis(qc,e)}rotateY(e){return this.rotateOnAxis(Xc,e)}rotateZ(e){return this.rotateOnAxis($c,e)}translateOnAxis(e,t){return Wc.copy(e).applyQuaternion(this.quaternion),this.position.add(Wc.multiplyScalar(t)),this}translateX(e){return this.translateOnAxis(qc,e)}translateY(e){return this.translateOnAxis(Xc,e)}translateZ(e){return this.translateOnAxis($c,e)}localToWorld(e){return this.updateWorldMatrix(!0,!1),e.applyMatrix4(this.matrixWorld)}worldToLocal(e){return this.updateWorldMatrix(!0,!1),e.applyMatrix4(Qn.copy(this.matrixWorld).invert())}lookAt(e,t,n){e.isVector3?ta.copy(e):ta.set(e,t,n);let s=this.parent;this.updateWorldMatrix(!0,!1),qs.setFromMatrixPosition(this.matrixWorld),this.isCamera||this.isLight?Qn.lookAt(qs,ta,this.up):Qn.lookAt(ta,qs,this.up),this.quaternion.setFromRotationMatrix(Qn),s&&(Qn.extractRotation(s.matrixWorld),ns.setFromRotationMatrix(Qn),this.quaternion.premultiply(ns.invert()))}add(e){if(arguments.length>1){for(let t=0;t<arguments.length;t++)this.add(arguments[t]);return this}return e===this?(et("Object3D.add: object can't be added as a child of itself.",e),this):(e&&e.isObject3D?(e.removeFromParent(),e.parent=this,this.children.push(e),e.dispatchEvent(Yc),is.child=e,this.dispatchEvent(is),is.child=null):et("Object3D.add: object not an instance of THREE.Object3D.",e),this)}remove(e){if(arguments.length>1){for(let n=0;n<arguments.length;n++)this.remove(arguments[n]);return this}let t=this.children.indexOf(e);return t!==-1&&(e.parent=null,this.children.splice(t,1),e.dispatchEvent(yd),vl.child=e,this.dispatchEvent(vl),vl.child=null),this}removeFromParent(){let e=this.parent;return e!==null&&e.remove(this),this}clear(){return this.remove(...this.children)}attach(e){return this.updateWorldMatrix(!0,!1),Qn.copy(this.matrixWorld).invert(),e.parent!==null&&(e.parent.updateWorldMatrix(!0,!1),Qn.multiply(e.parent.matrixWorld)),e.applyMatrix4(Qn),e.removeFromParent(),e.parent=this,this.children.push(e),e.updateWorldMatrix(!1,!0),e.dispatchEvent(Yc),is.child=e,this.dispatchEvent(is),is.child=null,this}getObjectById(e){return this.getObjectByProperty("id",e)}getObjectByName(e){return this.getObjectByProperty("name",e)}getObjectByProperty(e,t){if(this[e]===t)return this;for(let n=0,s=this.children.length;n<s;n++){let a=this.children[n].getObjectByProperty(e,t);if(a!==void 0)return a}}getObjectsByProperty(e,t,n=[]){this[e]===t&&n.push(this);let s=this.children;for(let r=0,a=s.length;r<a;r++)s[r].getObjectsByProperty(e,t,n);return n}getWorldPosition(e){return this.updateWorldMatrix(!0,!1),e.setFromMatrixPosition(this.matrixWorld)}getWorldQuaternion(e){return this.updateWorldMatrix(!0,!1),this.matrixWorld.decompose(qs,e,xd),e}getWorldScale(e){return this.updateWorldMatrix(!0,!1),this.matrixWorld.decompose(qs,vd,e),e}getWorldDirection(e){this.updateWorldMatrix(!0,!1);let t=this.matrixWorld.elements;return e.set(t[8],t[9],t[10]).normalize()}raycast(){}intersectsFrustum(){}traverse(e){e(this);let t=this.children;for(let n=0,s=t.length;n<s;n++)t[n].traverse(e)}traverseVisible(e){if(this.visible===!1)return;e(this);let t=this.children;for(let n=0,s=t.length;n<s;n++)t[n].traverseVisible(e)}traverseAncestors(e){let t=this.parent;t!==null&&(e(t),t.traverseAncestors(e))}updateMatrix(){this.matrix.compose(this.position,this.quaternion,this.scale);let e=this.pivot;if(e!==null){let t=e.x,n=e.y,s=e.z,r=this.matrix.elements;r[12]+=t-r[0]*t-r[4]*n-r[8]*s,r[13]+=n-r[1]*t-r[5]*n-r[9]*s,r[14]+=s-r[2]*t-r[6]*n-r[10]*s}this.matrixWorldNeedsUpdate=!0}updateMatrixWorld(e){this.matrixAutoUpdate&&this.updateMatrix(),(this.matrixWorldNeedsUpdate||e)&&(this.matrixWorldAutoUpdate===!0&&(this.parent===null?this.matrixWorld.copy(this.matrix):this.matrixWorld.multiplyMatrices(this.parent.matrixWorld,this.matrix)),this.matrixWorldNeedsUpdate=!1,e=!0);let t=this.children;for(let n=0,s=t.length;n<s;n++)t[n].updateMatrixWorld(e)}updateWorldMatrix(e,t,n=!1){let s=this.parent;if(e===!0&&s!==null&&s.updateWorldMatrix(!0,!1),this.matrixAutoUpdate&&this.updateMatrix(),(this.matrixWorldNeedsUpdate||n)&&(this.matrixWorldAutoUpdate===!0&&(this.parent===null?this.matrixWorld.copy(this.matrix):this.matrixWorld.multiplyMatrices(this.parent.matrixWorld,this.matrix)),this.matrixWorldNeedsUpdate=!1,n=!0),t===!0){let r=this.children;for(let a=0,o=r.length;a<o;a++)r[a].updateWorldMatrix(!1,!0,n)}}toJSON(e){let t=e===void 0||typeof e=="string",n={};t&&(e={geometries:{},materials:{},textures:{},images:{},shapes:{},skeletons:{},animations:{},nodes:{}},n.metadata={version:4.7,type:"Object",generator:"Object3D.toJSON"});let s={};s.uuid=this.uuid,s.type=this.type,s.name=this.name,s.castShadow=this.castShadow,s.receiveShadow=this.receiveShadow,s.visible=this.visible,s.frustumCulled=this.frustumCulled,s.renderOrder=this.renderOrder,s.static=this.static,s.matrixAutoUpdate=this.matrixAutoUpdate,Object.keys(this.userData).length>0&&(s.userData=this.userData),s.layers=this.layers.mask,s.matrix=this.matrix.toArray(),s.up=this.up.toArray(),this.pivot!==null&&(s.pivot=this.pivot.toArray()),this.morphTargetDictionary!==void 0&&(s.morphTargetDictionary=Object.assign({},this.morphTargetDictionary)),this.morphTargetInfluences!==void 0&&(s.morphTargetInfluences=this.morphTargetInfluences.slice()),this.isInstancedMesh&&(s.type="InstancedMesh",s.count=this.count,s.instanceMatrix=this.instanceMatrix.toJSON(),this.instanceColor!==null&&(s.instanceColor=this.instanceColor.toJSON())),this.isBatchedMesh&&(s.type="BatchedMesh",s.perObjectFrustumCulled=this.perObjectFrustumCulled,s.sortObjects=this.sortObjects,s.drawRanges=this._drawRanges,s.reservedRanges=this._reservedRanges,s.geometryInfo=this._geometryInfo.map(o=>({...o,boundingBox:o.boundingBox?o.boundingBox.toJSON():void 0,boundingSphere:o.boundingSphere?o.boundingSphere.toJSON():void 0})),s.instanceInfo=this._instanceInfo.map(o=>({...o})),s.availableInstanceIds=this._availableInstanceIds.slice(),s.availableGeometryIds=this._availableGeometryIds.slice(),s.nextIndexStart=this._nextIndexStart,s.nextVertexStart=this._nextVertexStart,s.geometryCount=this._geometryCount,s.maxInstanceCount=this._maxInstanceCount,s.maxVertexCount=this._maxVertexCount,s.maxIndexCount=this._maxIndexCount,s.geometryInitialized=this._geometryInitialized,s.matricesTexture=this._matricesTexture.toJSON(e),s.indirectTexture=this._indirectTexture.toJSON(e),this._colorsTexture!==null&&(s.colorsTexture=this._colorsTexture.toJSON(e)),this.boundingSphere!==null&&(s.boundingSphere=this.boundingSphere.toJSON()),this.boundingBox!==null&&(s.boundingBox=this.boundingBox.toJSON()));function r(o,l){return o[l.uuid]===void 0&&(o[l.uuid]=l.toJSON(e)),l.uuid}if(this.isScene)this.background&&(this.background.isColor?s.background=this.background.toJSON():this.background.isTexture&&(s.background=this.background.toJSON(e).uuid)),this.environment&&this.environment.isTexture&&this.environment.isRenderTargetTexture!==!0&&(s.environment=this.environment.toJSON(e).uuid);else if(this.isMesh||this.isLine||this.isPoints){s.geometry=r(e.geometries,this.geometry);let o=this.geometry.parameters;if(o!==void 0&&o.shapes!==void 0){let l=o.shapes;if(Array.isArray(l))for(let c=0,h=l.length;c<h;c++){let f=l[c];r(e.shapes,f)}else r(e.shapes,l)}}if(this.isSkinnedMesh&&(s.bindMode=this.bindMode,s.bindMatrix=this.bindMatrix.toArray(),this.skeleton!==void 0&&(r(e.skeletons,this.skeleton),s.skeleton=this.skeleton.uuid)),this.material!==void 0)if(Array.isArray(this.material)){let o=[];for(let l=0,c=this.material.length;l<c;l++)o.push(r(e.materials,this.material[l]));s.material=o}else s.material=r(e.materials,this.material);if(this.children.length>0){s.children=[];for(let o=0;o<this.children.length;o++)s.children.push(this.children[o].toJSON(e).object)}if(this.animations.length>0){s.animations=[];for(let o=0;o<this.animations.length;o++){let l=this.animations[o];s.animations.push(r(e.animations,l))}}if(t){let o=a(e.geometries),l=a(e.materials),c=a(e.textures),h=a(e.images),f=a(e.shapes),u=a(e.skeletons),d=a(e.animations),g=a(e.nodes);o.length>0&&(n.geometries=o),l.length>0&&(n.materials=l),c.length>0&&(n.textures=c),h.length>0&&(n.images=h),f.length>0&&(n.shapes=f),u.length>0&&(n.skeletons=u),d.length>0&&(n.animations=d),g.length>0&&(n.nodes=g)}return n.object=s,n;function a(o){let l=[];for(let c in o){let h=o[c];delete h.metadata,l.push(h)}return l}}clone(e){return new this.constructor().copy(this,e)}copy(e,t=!0){if(this.name=e.name,this.up.copy(e.up),this.position.copy(e.position),this.rotation.order=e.rotation.order,this.quaternion.copy(e.quaternion),this.scale.copy(e.scale),this.pivot=e.pivot!==null?e.pivot.clone():null,this.matrix.copy(e.matrix),this.matrixWorld.copy(e.matrixWorld),this.matrixAutoUpdate=e.matrixAutoUpdate,this.matrixWorldAutoUpdate=e.matrixWorldAutoUpdate,this.matrixWorldNeedsUpdate=e.matrixWorldNeedsUpdate,this.layers.mask=e.layers.mask,this.visible=e.visible,this.castShadow=e.castShadow,this.receiveShadow=e.receiveShadow,this.frustumCulled=e.frustumCulled,this.renderOrder=e.renderOrder,this.static=e.static,this.animations=e.animations.slice(),this.userData=JSON.parse(JSON.stringify(e.userData)),t===!0)for(let n=0;n<e.children.length;n++){let s=e.children[n];this.add(s.clone())}return this}dispose(){this.dispatchEvent({type:"dispose"})}};Ht.DEFAULT_UP=new D(0,1,0);Ht.DEFAULT_MATRIX_AUTO_UPDATE=!0;Ht.DEFAULT_MATRIX_WORLD_AUTO_UPDATE=!0;var zt=class extends Ht{constructor(){super(),this.isGroup=!0,this.type="Group"}},Md={type:"move"},bs=class{constructor(){this._targetRay=null,this._grip=null,this._hand=null}getHandSpace(){return this._hand===null&&(this._hand=new zt,this._hand.matrixAutoUpdate=!1,this._hand.visible=!1,this._hand.joints={},this._hand.inputState={pinching:!1}),this._hand}getTargetRaySpace(){return this._targetRay===null&&(this._targetRay=new zt,this._targetRay.matrixAutoUpdate=!1,this._targetRay.visible=!1,this._targetRay.hasLinearVelocity=!1,this._targetRay.linearVelocity=new D,this._targetRay.hasAngularVelocity=!1,this._targetRay.angularVelocity=new D),this._targetRay}getGripSpace(){return this._grip===null&&(this._grip=new zt,this._grip.matrixAutoUpdate=!1,this._grip.visible=!1,this._grip.hasLinearVelocity=!1,this._grip.linearVelocity=new D,this._grip.hasAngularVelocity=!1,this._grip.angularVelocity=new D,this._grip.eventsEnabled=!1),this._grip}dispatchEvent(e){return this._targetRay!==null&&this._targetRay.dispatchEvent(e),this._grip!==null&&this._grip.dispatchEvent(e),this._hand!==null&&this._hand.dispatchEvent(e),this}connect(e){if(e&&e.hand){let t=this._hand;if(t)for(let n of e.hand.values())this._getHandJoint(t,n)}return this.dispatchEvent({type:"connected",data:e}),this}disconnect(e){return this.dispatchEvent({type:"disconnected",data:e}),this._targetRay!==null&&(this._targetRay.visible=!1),this._grip!==null&&(this._grip.visible=!1),this._hand!==null&&(this._hand.visible=!1),this}update(e,t,n){let s=null,r=null,a=null,o=this._targetRay,l=this._grip,c=this._hand;if(e&&t.session.visibilityState!=="visible-blurred"){if(c&&e.hand){a=!0;for(let M of e.hand.values()){let m=t.getJointPose(M,n),p=this._getHandJoint(c,M);m!==null&&(p.matrix.fromArray(m.transform.matrix),p.matrix.decompose(p.position,p.rotation,p.scale),p.matrixWorldNeedsUpdate=!0,p.jointRadius=m.radius),p.visible=m!==null}let h=c.joints["index-finger-tip"],f=c.joints["thumb-tip"],u=h.position.distanceTo(f.position),d=.02,g=.005;c.inputState.pinching&&u>d+g?(c.inputState.pinching=!1,this.dispatchEvent({type:"pinchend",handedness:e.handedness,target:this})):!c.inputState.pinching&&u<=d-g&&(c.inputState.pinching=!0,this.dispatchEvent({type:"pinchstart",handedness:e.handedness,target:this}))}else l!==null&&e.gripSpace&&(r=t.getPose(e.gripSpace,n),r!==null&&(l.matrix.fromArray(r.transform.matrix),l.matrix.decompose(l.position,l.rotation,l.scale),l.matrixWorldNeedsUpdate=!0,r.linearVelocity?(l.hasLinearVelocity=!0,l.linearVelocity.copy(r.linearVelocity)):l.hasLinearVelocity=!1,r.angularVelocity?(l.hasAngularVelocity=!0,l.angularVelocity.copy(r.angularVelocity)):l.hasAngularVelocity=!1,l.eventsEnabled&&l.dispatchEvent({type:"gripUpdated",data:e,target:this})));o!==null&&(s=t.getPose(e.targetRaySpace,n),s===null&&r!==null&&(s=r),s!==null&&(o.matrix.fromArray(s.transform.matrix),o.matrix.decompose(o.position,o.rotation,o.scale),o.matrixWorldNeedsUpdate=!0,s.linearVelocity?(o.hasLinearVelocity=!0,o.linearVelocity.copy(s.linearVelocity)):o.hasLinearVelocity=!1,s.angularVelocity?(o.hasAngularVelocity=!0,o.angularVelocity.copy(s.angularVelocity)):o.hasAngularVelocity=!1,this.dispatchEvent(Md)))}return o!==null&&(o.visible=s!==null),l!==null&&(l.visible=r!==null),c!==null&&(c.visible=a!==null),this}_getHandJoint(e,t){if(e.joints[t.jointName]===void 0){let n=new zt;n.matrixAutoUpdate=!1,n.visible=!1,e.joints[t.jointName]=n,e.add(n)}return e.joints[t.jointName]}},eh={aliceblue:15792383,antiquewhite:16444375,aqua:65535,aquamarine:8388564,azure:15794175,beige:16119260,bisque:16770244,black:0,blanchedalmond:16772045,blue:255,blueviolet:9055202,brown:10824234,burlywood:14596231,cadetblue:6266528,chartreuse:8388352,chocolate:13789470,coral:16744272,cornflowerblue:6591981,cornsilk:16775388,crimson:14423100,cyan:65535,darkblue:139,darkcyan:35723,darkgoldenrod:12092939,darkgray:11119017,darkgreen:25600,darkgrey:11119017,darkkhaki:12433259,darkmagenta:9109643,darkolivegreen:5597999,darkorange:16747520,darkorchid:10040012,darkred:9109504,darksalmon:15308410,darkseagreen:9419919,darkslateblue:4734347,darkslategray:3100495,darkslategrey:3100495,darkturquoise:52945,darkviolet:9699539,deeppink:16716947,deepskyblue:49151,dimgray:6908265,dimgrey:6908265,dodgerblue:2003199,firebrick:11674146,floralwhite:16775920,forestgreen:2263842,fuchsia:16711935,gainsboro:14474460,ghostwhite:16316671,gold:16766720,goldenrod:14329120,gray:8421504,green:32768,greenyellow:11403055,grey:8421504,honeydew:15794160,hotpink:16738740,indianred:13458524,indigo:4915330,ivory:16777200,khaki:15787660,lavender:15132410,lavenderblush:16773365,lawngreen:8190976,lemonchiffon:16775885,lightblue:11393254,lightcoral:15761536,lightcyan:14745599,lightgoldenrodyellow:16448210,lightgray:13882323,lightgreen:9498256,lightgrey:13882323,lightpink:16758465,lightsalmon:16752762,lightseagreen:2142890,lightskyblue:8900346,lightslategray:7833753,lightslategrey:7833753,lightsteelblue:11584734,lightyellow:16777184,lime:65280,limegreen:3329330,linen:16445670,magenta:16711935,maroon:8388608,mediumaquamarine:6737322,mediumblue:205,mediumorchid:12211667,mediumpurple:9662683,mediumseagreen:3978097,mediumslateblue:8087790,mediumspringgreen:64154,mediumturquoise:4772300,mediumvioletred:13047173,midnightblue:1644912,mintcream:16121850,mistyrose:16770273,moccasin:16770229,navajowhite:16768685,navy:128,oldlace:16643558,olive:8421376,olivedrab:7048739,orange:16753920,orangered:16729344,orchid:14315734,palegoldenrod:15657130,palegreen:10025880,paleturquoise:11529966,palevioletred:14381203,papayawhip:16773077,peachpuff:16767673,peru:13468991,pink:16761035,plum:14524637,powderblue:11591910,purple:8388736,rebeccapurple:6697881,red:16711680,rosybrown:12357519,royalblue:4286945,saddlebrown:9127187,salmon:16416882,sandybrown:16032864,seagreen:3050327,seashell:16774638,sienna:10506797,silver:12632256,skyblue:8900331,slateblue:6970061,slategray:7372944,slategrey:7372944,snow:16775930,springgreen:65407,steelblue:4620980,tan:13808780,teal:32896,thistle:14204888,tomato:16737095,turquoise:4251856,violet:15631086,wheat:16113331,white:16777215,whitesmoke:16119285,yellow:16776960,yellowgreen:10145074},pi={h:0,s:0,l:0},na={h:0,s:0,l:0};function yl(i,e,t){return t<0&&(t+=1),t>1&&(t-=1),t<1/6?i+(e-i)*6*t:t<1/2?e:t<2/3?i+(e-i)*6*(2/3-t):i}var Ke=class{constructor(e,t,n){return this.isColor=!0,this.r=1,this.g=1,this.b=1,this.set(e,t,n)}set(e,t,n){if(t===void 0&&n===void 0){let s=e;s&&s.isColor?this.copy(s):typeof s=="number"?this.setHex(s):typeof s=="string"&&this.setStyle(s)}else this.setRGB(e,t,n);return this}setScalar(e){return this.r=e,this.g=e,this.b=e,this}setHex(e,t=dn){return e=Math.floor(e),this.r=(e>>16&255)/255,this.g=(e>>8&255)/255,this.b=(e&255)/255,dt.colorSpaceToWorking(this,t),this}setRGB(e,t,n,s=dt.workingColorSpace){return this.r=e,this.g=t,this.b=n,dt.colorSpaceToWorking(this,s),this}setHSL(e,t,n,s=dt.workingColorSpace){if(e=hc(e,1),t=ft(t,0,1),n=ft(n,0,1),t===0)this.r=this.g=this.b=n;else{let r=n<=.5?n*(1+t):n+t-n*t,a=2*n-r;this.r=yl(a,r,e+1/3),this.g=yl(a,r,e),this.b=yl(a,r,e-1/3)}return dt.colorSpaceToWorking(this,s),this}setStyle(e,t=dn){function n(r){r!==void 0&&parseFloat(r)<1&&Je("Color: Alpha component of "+e+" will be ignored.")}let s;if(s=/^(\w+)\(([^\)]*)\)/.exec(e)){let r,a=s[1],o=s[2];switch(a){case"rgb":case"rgba":if(r=/^\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(o))return n(r[4]),this.setRGB(Math.min(255,parseInt(r[1],10))/255,Math.min(255,parseInt(r[2],10))/255,Math.min(255,parseInt(r[3],10))/255,t);if(r=/^\s*(\d+)\%\s*,\s*(\d+)\%\s*,\s*(\d+)\%\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(o))return n(r[4]),this.setRGB(Math.min(100,parseInt(r[1],10))/100,Math.min(100,parseInt(r[2],10))/100,Math.min(100,parseInt(r[3],10))/100,t);break;case"hsl":case"hsla":if(r=/^\s*(\d*\.?\d+)\s*,\s*(\d*\.?\d+)\%\s*,\s*(\d*\.?\d+)\%\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(o))return n(r[4]),this.setHSL(parseFloat(r[1])/360,parseFloat(r[2])/100,parseFloat(r[3])/100,t);break;default:Je("Color: Unknown color model "+e)}}else if(s=/^\#([A-Fa-f\d]+)$/.exec(e)){let r=s[1],a=r.length;if(a===3)return this.setRGB(parseInt(r.charAt(0),16)/15,parseInt(r.charAt(1),16)/15,parseInt(r.charAt(2),16)/15,t);if(a===6)return this.setHex(parseInt(r,16),t);Je("Color: Invalid hex color "+e)}else if(e&&e.length>0)return this.setColorName(e,t);return this}setColorName(e,t=dn){let n=eh[e.toLowerCase()];return n!==void 0?this.setHex(n,t):Je("Color: Unknown color "+e),this}clone(){return new this.constructor(this.r,this.g,this.b)}copy(e){return this.r=e.r,this.g=e.g,this.b=e.b,this}copySRGBToLinear(e){return this.r=si(e.r),this.g=si(e.g),this.b=si(e.b),this}copyLinearToSRGB(e){return this.r=ms(e.r),this.g=ms(e.g),this.b=ms(e.b),this}convertSRGBToLinear(){return this.copySRGBToLinear(this),this}convertLinearToSRGB(){return this.copyLinearToSRGB(this),this}getHex(e=dn){return dt.workingToColorSpace(rn.copy(this),e),Math.round(ft(rn.r*255,0,255))*65536+Math.round(ft(rn.g*255,0,255))*256+Math.round(ft(rn.b*255,0,255))}getHexString(e=dn){return("000000"+this.getHex(e).toString(16)).slice(-6)}getHSL(e,t=dt.workingColorSpace){dt.workingToColorSpace(rn.copy(this),t);let n=rn.r,s=rn.g,r=rn.b,a=Math.max(n,s,r),o=Math.min(n,s,r),l,c,h=(o+a)/2;if(o===a)l=0,c=0;else{let f=a-o;switch(c=h<=.5?f/(a+o):f/(2-a-o),a){case n:l=(s-r)/f+(s<r?6:0);break;case s:l=(r-n)/f+2;break;case r:l=(n-s)/f+4;break}l/=6}return e.h=l,e.s=c,e.l=h,e}getRGB(e,t=dt.workingColorSpace){return dt.workingToColorSpace(rn.copy(this),t),e.r=rn.r,e.g=rn.g,e.b=rn.b,e}getStyle(e=dn){dt.workingToColorSpace(rn.copy(this),e);let t=rn.r,n=rn.g,s=rn.b;return e!==dn?`color(${e} ${t.toFixed(3)} ${n.toFixed(3)} ${s.toFixed(3)})`:`rgb(${Math.round(t*255)},${Math.round(n*255)},${Math.round(s*255)})`}offsetHSL(e,t,n){return this.getHSL(pi),this.setHSL(pi.h+e,pi.s+t,pi.l+n)}add(e){return this.r+=e.r,this.g+=e.g,this.b+=e.b,this}addColors(e,t){return this.r=e.r+t.r,this.g=e.g+t.g,this.b=e.b+t.b,this}addScalar(e){return this.r+=e,this.g+=e,this.b+=e,this}sub(e){return this.r=Math.max(0,this.r-e.r),this.g=Math.max(0,this.g-e.g),this.b=Math.max(0,this.b-e.b),this}multiply(e){return this.r*=e.r,this.g*=e.g,this.b*=e.b,this}multiplyScalar(e){return this.r*=e,this.g*=e,this.b*=e,this}lerp(e,t){return this.r+=(e.r-this.r)*t,this.g+=(e.g-this.g)*t,this.b+=(e.b-this.b)*t,this}lerpColors(e,t,n){return this.r=e.r+(t.r-e.r)*n,this.g=e.g+(t.g-e.g)*n,this.b=e.b+(t.b-e.b)*n,this}lerpHSL(e,t){this.getHSL(pi),e.getHSL(na);let n=Qs(pi.h,na.h,t),s=Qs(pi.s,na.s,t),r=Qs(pi.l,na.l,t);return this.setHSL(n,s,r),this}setFromVector3(e){return this.r=e.x,this.g=e.y,this.b=e.z,this}applyMatrix3(e){let t=this.r,n=this.g,s=this.b,r=e.elements;return this.r=r[0]*t+r[3]*n+r[6]*s,this.g=r[1]*t+r[4]*n+r[7]*s,this.b=r[2]*t+r[5]*n+r[8]*s,this}equals(e){return e.r===this.r&&e.g===this.g&&e.b===this.b}fromArray(e,t=0){return this.r=e[t],this.g=e[t+1],this.b=e[t+2],this}toArray(e=[],t=0){return e[t]=this.r,e[t+1]=this.g,e[t+2]=this.b,e}fromBufferAttribute(e,t){return this.r=e.getX(t),this.g=e.getY(t),this.b=e.getZ(t),this}toJSON(){return this.getHex()}*[Symbol.iterator](){yield this.r,yield this.g,yield this.b}},rn=new Ke;Ke.NAMES=eh;var or=class i{constructor(e,t=25e-5){this.isFogExp2=!0,this.name="",this.color=new Ke(e),this.density=t}clone(){return new i(this.color,this.density)}toJSON(){return{type:"FogExp2",name:this.name,color:this.color.getHex(),density:this.density}}};var Bi=class extends Ht{constructor(){super(),this.isScene=!0,this.type="Scene",this.background=null,this.environment=null,this.fog=null,this.backgroundBlurriness=0,this.backgroundIntensity=1,this.backgroundRotation=new En,this.environmentIntensity=1,this.environmentRotation=new En,this.overrideMaterial=null,typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("observe",{detail:this}))}copy(e,t){return super.copy(e,t),e.background!==null&&(this.background=e.background.clone()),e.environment!==null&&(this.environment=e.environment.clone()),e.fog!==null&&(this.fog=e.fog.clone()),this.backgroundBlurriness=e.backgroundBlurriness,this.backgroundIntensity=e.backgroundIntensity,this.backgroundRotation.copy(e.backgroundRotation),this.environmentIntensity=e.environmentIntensity,this.environmentRotation.copy(e.environmentRotation),e.overrideMaterial!==null&&(this.overrideMaterial=e.overrideMaterial.clone()),this.matrixAutoUpdate=e.matrixAutoUpdate,this}toJSON(e){let t=super.toJSON(e);return this.fog!==null&&(t.object.fog=this.fog.toJSON()),t.object.backgroundBlurriness=this.backgroundBlurriness,t.object.backgroundIntensity=this.backgroundIntensity,t.object.backgroundRotation=this.backgroundRotation.toArray(),t.object.environmentIntensity=this.environmentIntensity,t.object.environmentRotation=this.environmentRotation.toArray(),t}},Ln=new D,ei=new D,Ml=new D,ti=new D,ss=new D,rs=new D,Zc=new D,bl=new D,Sl=new D,Tl=new D,El=new Dt,wl=new Dt,Al=new Dt,xi=class i{constructor(e=new D,t=new D,n=new D){this.a=e,this.b=t,this.c=n}static getNormal(e,t,n,s){s.subVectors(n,t),Ln.subVectors(e,t),s.cross(Ln);let r=s.lengthSq();return r>0?s.multiplyScalar(1/Math.sqrt(r)):s.set(0,0,0)}static getBarycoord(e,t,n,s,r){Ln.subVectors(s,t),ei.subVectors(n,t),Ml.subVectors(e,t);let a=Ln.dot(Ln),o=Ln.dot(ei),l=Ln.dot(Ml),c=ei.dot(ei),h=ei.dot(Ml),f=a*c-o*o;if(f===0)return r.set(0,0,0),null;let u=1/f,d=(c*l-o*h)*u,g=(a*h-o*l)*u;return r.set(1-d-g,g,d)}static containsPoint(e,t,n,s){return this.getBarycoord(e,t,n,s,ti)===null?!1:ti.x>=0&&ti.y>=0&&ti.x+ti.y<=1}static getInterpolation(e,t,n,s,r,a,o,l){return this.getBarycoord(e,t,n,s,ti)===null?(l.x=0,l.y=0,"z"in l&&(l.z=0),"w"in l&&(l.w=0),null):(l.setScalar(0),l.addScaledVector(r,ti.x),l.addScaledVector(a,ti.y),l.addScaledVector(o,ti.z),l)}static getInterpolatedAttribute(e,t,n,s,r,a){return El.setScalar(0),wl.setScalar(0),Al.setScalar(0),El.fromBufferAttribute(e,t),wl.fromBufferAttribute(e,n),Al.fromBufferAttribute(e,s),a.setScalar(0),a.addScaledVector(El,r.x),a.addScaledVector(wl,r.y),a.addScaledVector(Al,r.z),a}static isFrontFacing(e,t,n,s){return Ln.subVectors(n,t),ei.subVectors(e,t),Ln.cross(ei).dot(s)<0}set(e,t,n){return this.a.copy(e),this.b.copy(t),this.c.copy(n),this}setFromPointsAndIndices(e,t,n,s){return this.a.copy(e[t]),this.b.copy(e[n]),this.c.copy(e[s]),this}setFromAttributeAndIndices(e,t,n,s){return this.a.fromBufferAttribute(e,t),this.b.fromBufferAttribute(e,n),this.c.fromBufferAttribute(e,s),this}clone(){return new this.constructor().copy(this)}copy(e){return this.a.copy(e.a),this.b.copy(e.b),this.c.copy(e.c),this}getArea(){return Ln.subVectors(this.c,this.b),ei.subVectors(this.a,this.b),Ln.cross(ei).length()*.5}getMidpoint(e){return e.addVectors(this.a,this.b).add(this.c).multiplyScalar(1/3)}getNormal(e){return i.getNormal(this.a,this.b,this.c,e)}getPlane(e){return e.setFromCoplanarPoints(this.a,this.b,this.c)}getBarycoord(e,t){return i.getBarycoord(e,this.a,this.b,this.c,t)}getInterpolation(e,t,n,s,r){return i.getInterpolation(e,this.a,this.b,this.c,t,n,s,r)}containsPoint(e){return i.containsPoint(e,this.a,this.b,this.c)}isFrontFacing(e){return i.isFrontFacing(this.a,this.b,this.c,e)}intersectsBox(e){return e.intersectsTriangle(this)}closestPointToPoint(e,t){let n=this.a,s=this.b,r=this.c,a,o;ss.subVectors(s,n),rs.subVectors(r,n),bl.subVectors(e,n);let l=ss.dot(bl),c=rs.dot(bl);if(l<=0&&c<=0)return t.copy(n);Sl.subVectors(e,s);let h=ss.dot(Sl),f=rs.dot(Sl);if(h>=0&&f<=h)return t.copy(s);let u=l*f-h*c;if(u<=0&&l>=0&&h<=0)return a=l/(l-h),t.copy(n).addScaledVector(ss,a);Tl.subVectors(e,r);let d=ss.dot(Tl),g=rs.dot(Tl);if(g>=0&&d<=g)return t.copy(r);let M=d*c-l*g;if(M<=0&&c>=0&&g<=0)return o=c/(c-g),t.copy(n).addScaledVector(rs,o);let m=h*g-d*f;if(m<=0&&f-h>=0&&d-g>=0)return Zc.subVectors(r,s),o=(f-h)/(f-h+(d-g)),t.copy(s).addScaledVector(Zc,o);let p=1/(m+M+u);return a=M*p,o=u*p,t.copy(n).addScaledVector(ss,a).addScaledVector(rs,o)}equals(e){return e.a.equals(this.a)&&e.b.equals(this.b)&&e.c.equals(this.c)}},qn=class{constructor(e=new D(1/0,1/0,1/0),t=new D(-1/0,-1/0,-1/0)){this.isBox3=!0,this.min=e,this.max=t}set(e,t){return this.min.copy(e),this.max.copy(t),this}setFromArray(e){this.makeEmpty();for(let t=0,n=e.length;t<n;t+=3)this.expandByPoint(Nn.fromArray(e,t));return this}setFromBufferAttribute(e){this.makeEmpty();for(let t=0,n=e.count;t<n;t++)this.expandByPoint(Nn.fromBufferAttribute(e,t));return this}setFromPoints(e){this.makeEmpty();for(let t=0,n=e.length;t<n;t++)this.expandByPoint(e[t]);return this}setFromCenterAndSize(e,t){let n=Nn.copy(t).multiplyScalar(.5);return this.min.copy(e).sub(n),this.max.copy(e).add(n),this}setFromObject(e,t=!1){return this.makeEmpty(),this.expandByObject(e,t)}clone(){return new this.constructor().copy(this)}copy(e){return this.min.copy(e.min),this.max.copy(e.max),this}makeEmpty(){return this.min.x=this.min.y=this.min.z=1/0,this.max.x=this.max.y=this.max.z=-1/0,this}isEmpty(){return this.max.x<this.min.x||this.max.y<this.min.y||this.max.z<this.min.z}getCenter(e){return this.isEmpty()?e.set(0,0,0):e.addVectors(this.min,this.max).multiplyScalar(.5)}getSize(e){return this.isEmpty()?e.set(0,0,0):e.subVectors(this.max,this.min)}expandByPoint(e){return this.min.min(e),this.max.max(e),this}expandByVector(e){return this.min.sub(e),this.max.add(e),this}expandByScalar(e){return this.min.addScalar(-e),this.max.addScalar(e),this}expandByObject(e,t=!1){e.updateWorldMatrix(!1,!1);let n=e.geometry;if(n!==void 0){let r=n.getAttribute("position");if(t===!0&&r!==void 0&&e.isInstancedMesh!==!0)for(let a=0,o=r.count;a<o;a++)e.isMesh===!0?e.getVertexPosition(a,Nn):Nn.fromBufferAttribute(r,a),Nn.applyMatrix4(e.matrixWorld),this.expandByPoint(Nn);else e.boundingBox!==void 0?(e.boundingBox===null&&e.computeBoundingBox(),ia.copy(e.boundingBox)):(n.boundingBox===null&&n.computeBoundingBox(),ia.copy(n.boundingBox)),ia.applyMatrix4(e.matrixWorld),this.union(ia)}let s=e.children;for(let r=0,a=s.length;r<a;r++)this.expandByObject(s[r],t);return this}containsPoint(e){return e.x>=this.min.x&&e.x<=this.max.x&&e.y>=this.min.y&&e.y<=this.max.y&&e.z>=this.min.z&&e.z<=this.max.z}containsBox(e){return this.min.x<=e.min.x&&e.max.x<=this.max.x&&this.min.y<=e.min.y&&e.max.y<=this.max.y&&this.min.z<=e.min.z&&e.max.z<=this.max.z}getParameter(e,t){return t.set((e.x-this.min.x)/(this.max.x-this.min.x),(e.y-this.min.y)/(this.max.y-this.min.y),(e.z-this.min.z)/(this.max.z-this.min.z))}intersectsBox(e){return e.max.x>=this.min.x&&e.min.x<=this.max.x&&e.max.y>=this.min.y&&e.min.y<=this.max.y&&e.max.z>=this.min.z&&e.min.z<=this.max.z}intersectsSphere(e){return this.clampPoint(e.center,Nn),Nn.distanceToSquared(e.center)<=e.radius*e.radius}intersectsPlane(e){let t,n;return e.normal.x>0?(t=e.normal.x*this.min.x,n=e.normal.x*this.max.x):(t=e.normal.x*this.max.x,n=e.normal.x*this.min.x),e.normal.y>0?(t+=e.normal.y*this.min.y,n+=e.normal.y*this.max.y):(t+=e.normal.y*this.max.y,n+=e.normal.y*this.min.y),e.normal.z>0?(t+=e.normal.z*this.min.z,n+=e.normal.z*this.max.z):(t+=e.normal.z*this.max.z,n+=e.normal.z*this.min.z),t<=-e.constant&&n>=-e.constant}intersectsTriangle(e){if(this.isEmpty())return!1;this.getCenter(Xs),sa.subVectors(this.max,Xs),as.subVectors(e.a,Xs),os.subVectors(e.b,Xs),ls.subVectors(e.c,Xs),mi.subVectors(os,as),gi.subVectors(ls,os),Di.subVectors(as,ls);let t=[0,-mi.z,mi.y,0,-gi.z,gi.y,0,-Di.z,Di.y,mi.z,0,-mi.x,gi.z,0,-gi.x,Di.z,0,-Di.x,-mi.y,mi.x,0,-gi.y,gi.x,0,-Di.y,Di.x,0];return!Cl(t,as,os,ls,sa)||(t=[1,0,0,0,1,0,0,0,1],!Cl(t,as,os,ls,sa))?!1:(ra.crossVectors(mi,gi),t=[ra.x,ra.y,ra.z],Cl(t,as,os,ls,sa))}clampPoint(e,t){return t.copy(e).clamp(this.min,this.max)}distanceToPoint(e){return this.clampPoint(e,Nn).distanceTo(e)}getBoundingSphere(e){return this.isEmpty()?e.makeEmpty():(this.getCenter(e.center),e.radius=this.getSize(Nn).length()*.5),e}intersect(e){return this.min.max(e.min),this.max.min(e.max),this.isEmpty()&&this.makeEmpty(),this}union(e){return this.min.min(e.min),this.max.max(e.max),this}applyMatrix4(e){return this.isEmpty()?this:(ni[0].set(this.min.x,this.min.y,this.min.z).applyMatrix4(e),ni[1].set(this.min.x,this.min.y,this.max.z).applyMatrix4(e),ni[2].set(this.min.x,this.max.y,this.min.z).applyMatrix4(e),ni[3].set(this.min.x,this.max.y,this.max.z).applyMatrix4(e),ni[4].set(this.max.x,this.min.y,this.min.z).applyMatrix4(e),ni[5].set(this.max.x,this.min.y,this.max.z).applyMatrix4(e),ni[6].set(this.max.x,this.max.y,this.min.z).applyMatrix4(e),ni[7].set(this.max.x,this.max.y,this.max.z).applyMatrix4(e),this.setFromPoints(ni),this)}translate(e){return this.min.add(e),this.max.add(e),this}equals(e){return e.min.equals(this.min)&&e.max.equals(this.max)}toJSON(){return{min:this.min.toArray(),max:this.max.toArray()}}fromJSON(e){return this.min.fromArray(e.min),this.max.fromArray(e.max),this}},ni=[new D,new D,new D,new D,new D,new D,new D,new D],Nn=new D,ia=new qn,as=new D,os=new D,ls=new D,mi=new D,gi=new D,Di=new D,Xs=new D,sa=new D,ra=new D,Ui=new D;function Cl(i,e,t,n,s){for(let r=0,a=i.length-3;r<=a;r+=3){Ui.fromArray(i,r);let o=s.x*Math.abs(Ui.x)+s.y*Math.abs(Ui.y)+s.z*Math.abs(Ui.z),l=e.dot(Ui),c=t.dot(Ui),h=n.dot(Ui);if(Math.max(-Math.max(l,c,h),Math.min(l,c,h))>o)return!1}return!0}var Bt=new D,aa=new Ue,bd=0,Kt=class extends Wn{constructor(e,t,n=!1){if(super(),Array.isArray(e))throw new TypeError("THREE.BufferAttribute: array should be a Typed Array.");this.isBufferAttribute=!0,Object.defineProperty(this,"id",{value:bd++}),this.name="",this.array=e,this.itemSize=t,this.count=e!==void 0?e.length/t:0,this.normalized=n,this.usage=Zu,this.updateRanges=[],this.gpuType=Rn,this.version=0}onUploadCallback(){}set needsUpdate(e){e===!0&&this.version++}setUsage(e){return this.usage=e,this}addUpdateRange(e,t){this.updateRanges.push({start:e,count:t})}clearUpdateRanges(){this.updateRanges.length=0}copy(e){return this.name=e.name,this.array=new e.array.constructor(e.array),this.itemSize=e.itemSize,this.count=e.count,this.normalized=e.normalized,this.usage=e.usage,this.gpuType=e.gpuType,this}copyAt(e,t,n){e*=this.itemSize,n*=t.itemSize;for(let s=0,r=this.itemSize;s<r;s++)this.array[e+s]=t.array[n+s];return this}copyArray(e){return this.array.set(e),this}applyMatrix3(e){if(this.itemSize===2)for(let t=0,n=this.count;t<n;t++)aa.fromBufferAttribute(this,t),aa.applyMatrix3(e),this.setXY(t,aa.x,aa.y);else if(this.itemSize===3)for(let t=0,n=this.count;t<n;t++)Bt.fromBufferAttribute(this,t),Bt.applyMatrix3(e),this.setXYZ(t,Bt.x,Bt.y,Bt.z);return this}applyMatrix4(e){for(let t=0,n=this.count;t<n;t++)Bt.fromBufferAttribute(this,t),Bt.applyMatrix4(e),this.setXYZ(t,Bt.x,Bt.y,Bt.z);return this}applyNormalMatrix(e){for(let t=0,n=this.count;t<n;t++)Bt.fromBufferAttribute(this,t),Bt.applyNormalMatrix(e),this.setXYZ(t,Bt.x,Bt.y,Bt.z);return this}transformDirection(e){for(let t=0,n=this.count;t<n;t++)Bt.fromBufferAttribute(this,t),Bt.transformDirection(e),this.setXYZ(t,Bt.x,Bt.y,Bt.z);return this}set(e,t=0){return this.array.set(e,t),this}getComponent(e,t){let n=this.array[e*this.itemSize+t];return this.normalized&&(n=ps(n,this.array)),n}setComponent(e,t,n){return this.normalized&&(n=hn(n,this.array)),this.array[e*this.itemSize+t]=n,this}getX(e){let t=this.array[e*this.itemSize];return this.normalized&&(t=ps(t,this.array)),t}setX(e,t){return this.normalized&&(t=hn(t,this.array)),this.array[e*this.itemSize]=t,this}getY(e){let t=this.array[e*this.itemSize+1];return this.normalized&&(t=ps(t,this.array)),t}setY(e,t){return this.normalized&&(t=hn(t,this.array)),this.array[e*this.itemSize+1]=t,this}getZ(e){let t=this.array[e*this.itemSize+2];return this.normalized&&(t=ps(t,this.array)),t}setZ(e,t){return this.normalized&&(t=hn(t,this.array)),this.array[e*this.itemSize+2]=t,this}getW(e){let t=this.array[e*this.itemSize+3];return this.normalized&&(t=ps(t,this.array)),t}setW(e,t){return this.normalized&&(t=hn(t,this.array)),this.array[e*this.itemSize+3]=t,this}setXY(e,t,n){return e*=this.itemSize,this.normalized&&(t=hn(t,this.array),n=hn(n,this.array)),this.array[e+0]=t,this.array[e+1]=n,this}setXYZ(e,t,n,s){return e*=this.itemSize,this.normalized&&(t=hn(t,this.array),n=hn(n,this.array),s=hn(s,this.array)),this.array[e+0]=t,this.array[e+1]=n,this.array[e+2]=s,this}setXYZW(e,t,n,s,r){return e*=this.itemSize,this.normalized&&(t=hn(t,this.array),n=hn(n,this.array),s=hn(s,this.array),r=hn(r,this.array)),this.array[e+0]=t,this.array[e+1]=n,this.array[e+2]=s,this.array[e+3]=r,this}onUpload(e){return this.onUploadCallback=e,this}clone(){return new this.constructor(this.array,this.itemSize).copy(this)}toJSON(){let e={itemSize:this.itemSize,type:this.array.constructor.name,array:Array.from(this.array),normalized:this.normalized};return e.name=this.name,e.usage=this.usage,e.gpuType=this.gpuType,e}dispose(){this.dispatchEvent({type:"dispose"})}};var lr=class extends Kt{constructor(e,t,n){super(new Uint16Array(e),t,n)}};var cr=class extends Kt{constructor(e,t,n){super(new Uint32Array(e),t,n)}};var vt=class extends Kt{constructor(e,t,n){super(new Float32Array(e),t,n)}},Sd=new qn,$s=new D,Rl=new D,Xn=class{constructor(e=new D,t=-1){this.isSphere=!0,this.center=e,this.radius=t}set(e,t){return this.center.copy(e),this.radius=t,this}setFromPoints(e,t){let n=this.center;t!==void 0?n.copy(t):Sd.setFromPoints(e).getCenter(n);let s=0;for(let r=0,a=e.length;r<a;r++)s=Math.max(s,n.distanceToSquared(e[r]));return this.radius=Math.sqrt(s),this}copy(e){return this.center.copy(e.center),this.radius=e.radius,this}isEmpty(){return this.radius<0}makeEmpty(){return this.center.set(0,0,0),this.radius=-1,this}containsPoint(e){return e.distanceToSquared(this.center)<=this.radius*this.radius}distanceToPoint(e){return e.distanceTo(this.center)-this.radius}intersectsSphere(e){let t=this.radius+e.radius;return e.center.distanceToSquared(this.center)<=t*t}intersectsBox(e){return e.intersectsSphere(this)}intersectsPlane(e){return Math.abs(e.distanceToPoint(this.center))<=this.radius}clampPoint(e,t){let n=this.center.distanceToSquared(e);return t.copy(e),n>this.radius*this.radius&&(t.sub(this.center).normalize(),t.multiplyScalar(this.radius).add(this.center)),t}getBoundingBox(e){return this.isEmpty()?(e.makeEmpty(),e):(e.set(this.center,this.center),e.expandByScalar(this.radius),e)}applyMatrix4(e){return this.center.applyMatrix4(e),this.radius=this.radius*e.getMaxScaleOnAxis(),this}translate(e){return this.center.add(e),this}expandByPoint(e){if(this.isEmpty())return this.center.copy(e),this.radius=0,this;$s.subVectors(e,this.center);let t=$s.lengthSq();if(t>this.radius*this.radius){let n=Math.sqrt(t),s=(n-this.radius)*.5;this.center.addScaledVector($s,s/n),this.radius+=s}return this}union(e){return e.isEmpty()?this:this.isEmpty()?(this.copy(e),this):(this.center.equals(e.center)===!0?this.radius=Math.max(this.radius,e.radius):(Rl.subVectors(e.center,this.center).setLength(e.radius),this.expandByPoint($s.copy(e.center).add(Rl)),this.expandByPoint($s.copy(e.center).sub(Rl))),this)}equals(e){return e.center.equals(this.center)&&e.radius===this.radius}clone(){return new this.constructor().copy(this)}toJSON(){return{radius:this.radius,center:this.center.toArray()}}fromJSON(e){return this.radius=e.radius,this.center.fromArray(e.center),this}},Td=0,Tn=new pt,Pl=new Ht,cs=new D,Mn=new qn,Ys=new qn,Yt=new D,Rt=class i extends Wn{constructor(){super(),this.isBufferGeometry=!0,Object.defineProperty(this,"id",{value:Td++}),this.uuid=Ds(),this.name="",this.type="BufferGeometry",this.index=null,this.indirect=null,this.indirectOffset=0,this.attributes={},this.morphAttributes={},this.morphTargetsRelative=!1,this.groups=[],this.boundingBox=null,this.boundingSphere=null,this.drawRange={start:0,count:1/0},this.userData={},this._transformed=!1}getIndex(){return this.index}setIndex(e){return Array.isArray(e)?this.index=new(Yh(e)?cr:lr)(e,1):this.index=e,this}setIndirect(e,t=0){return this.indirect=e,this.indirectOffset=t,this}getIndirect(){return this.indirect}getAttribute(e){return this.attributes[e]}setAttribute(e,t){return this.attributes[e]=t,this}deleteAttribute(e){return delete this.attributes[e],this}hasAttribute(e){return this.attributes[e]!==void 0}addGroup(e,t,n=0){this.groups.push({start:e,count:t,materialIndex:n})}clearGroups(){this.groups=[]}setDrawRange(e,t){this.drawRange.start=e,this.drawRange.count=t}applyMatrix4(e){let t=this.attributes.position;t!==void 0&&(t.applyMatrix4(e),t.needsUpdate=!0);let n=this.attributes.normal;if(n!==void 0){let r=new nt().getNormalMatrix(e);n.applyNormalMatrix(r),n.needsUpdate=!0}let s=this.attributes.tangent;return s!==void 0&&(s.transformDirection(e),s.needsUpdate=!0),this.boundingBox!==null&&this.computeBoundingBox(),this.boundingSphere!==null&&this.computeBoundingSphere(),this._transformed=!0,this}applyQuaternion(e){return Tn.makeRotationFromQuaternion(e),this.applyMatrix4(Tn),this}rotateX(e){return Tn.makeRotationX(e),this.applyMatrix4(Tn),this}rotateY(e){return Tn.makeRotationY(e),this.applyMatrix4(Tn),this}rotateZ(e){return Tn.makeRotationZ(e),this.applyMatrix4(Tn),this}translate(e,t,n){return Tn.makeTranslation(e,t,n),this.applyMatrix4(Tn),this}scale(e,t,n){return Tn.makeScale(e,t,n),this.applyMatrix4(Tn),this}lookAt(e){return Pl.lookAt(e),Pl.updateMatrix(),this.applyMatrix4(Pl.matrix),this}center(){return this.computeBoundingBox(),this.boundingBox.getCenter(cs).negate(),this.translate(cs.x,cs.y,cs.z),this}setFromPoints(e){let t=this.getAttribute("position");if(t===void 0){let n=[];for(let s=0,r=e.length;s<r;s++){let a=e[s];n.push(a.x,a.y,a.z||0)}this.setAttribute("position",new vt(n,3))}else{let n=Math.min(e.length,t.count);for(let s=0;s<n;s++){let r=e[s];t.setXYZ(s,r.x,r.y,r.z||0)}e.length>t.count&&Je("BufferGeometry: Buffer size too small for points data. Use .dispose() and create a new geometry."),t.needsUpdate=!0}return this}computeBoundingBox(){this.boundingBox===null&&(this.boundingBox=new qn);let e=this.attributes.position,t=this.morphAttributes.position;if(e&&e.isGLBufferAttribute){et("BufferGeometry.computeBoundingBox(): GLBufferAttribute requires a manual bounding box.",this),this.boundingBox.set(new D(-1/0,-1/0,-1/0),new D(1/0,1/0,1/0));return}if(e!==void 0){if(this.boundingBox.setFromBufferAttribute(e),t)for(let n=0,s=t.length;n<s;n++){let r=t[n];Mn.setFromBufferAttribute(r),this.morphTargetsRelative?(Yt.addVectors(this.boundingBox.min,Mn.min),this.boundingBox.expandByPoint(Yt),Yt.addVectors(this.boundingBox.max,Mn.max),this.boundingBox.expandByPoint(Yt)):(this.boundingBox.expandByPoint(Mn.min),this.boundingBox.expandByPoint(Mn.max))}}else this.boundingBox.makeEmpty();(isNaN(this.boundingBox.min.x)||isNaN(this.boundingBox.min.y)||isNaN(this.boundingBox.min.z))&&et('BufferGeometry.computeBoundingBox(): Computed min/max have NaN values. The "position" attribute is likely to have NaN values.',this)}computeBoundingSphere(){this.boundingSphere===null&&(this.boundingSphere=new Xn);let e=this.attributes.position,t=this.morphAttributes.position;if(e&&e.isGLBufferAttribute){et("BufferGeometry.computeBoundingSphere(): GLBufferAttribute requires a manual bounding sphere.",this),this.boundingSphere.set(new D,1/0);return}if(e){let n=this.boundingSphere.center;if(Mn.setFromBufferAttribute(e),t)for(let r=0,a=t.length;r<a;r++){let o=t[r];Ys.setFromBufferAttribute(o),this.morphTargetsRelative?(Yt.addVectors(Mn.min,Ys.min),Mn.expandByPoint(Yt),Yt.addVectors(Mn.max,Ys.max),Mn.expandByPoint(Yt)):(Mn.expandByPoint(Ys.min),Mn.expandByPoint(Ys.max))}Mn.getCenter(n);let s=0;for(let r=0,a=e.count;r<a;r++)Yt.fromBufferAttribute(e,r),s=Math.max(s,n.distanceToSquared(Yt));if(t)for(let r=0,a=t.length;r<a;r++){let o=t[r],l=this.morphTargetsRelative;for(let c=0,h=o.count;c<h;c++)Yt.fromBufferAttribute(o,c),l&&(cs.fromBufferAttribute(e,c),Yt.add(cs)),s=Math.max(s,n.distanceToSquared(Yt))}this.boundingSphere.radius=Math.sqrt(s),isNaN(this.boundingSphere.radius)&&et('BufferGeometry.computeBoundingSphere(): Computed radius is NaN. The "position" attribute is likely to have NaN values.',this)}}computeTangents(){let e=this.index,t=this.attributes;if(e===null||t.position===void 0||t.normal===void 0||t.uv===void 0){et("BufferGeometry: .computeTangents() failed. Missing required attributes (index, position, normal or uv)");return}let n=t.position,s=t.normal,r=t.uv,a=this.getAttribute("tangent");(a===void 0||a.count!==n.count)&&(a=new Kt(new Float32Array(4*n.count),4),this.setAttribute("tangent",a));let o=[],l=[];for(let x=0;x<n.count;x++)o[x]=new D,l[x]=new D;let c=new D,h=new D,f=new D,u=new Ue,d=new Ue,g=new Ue,M=new D,m=new D;function p(x,A,N){c.fromBufferAttribute(n,x),h.fromBufferAttribute(n,A),f.fromBufferAttribute(n,N),u.fromBufferAttribute(r,x),d.fromBufferAttribute(r,A),g.fromBufferAttribute(r,N),h.sub(c),f.sub(c),d.sub(u),g.sub(u);let k=1/(d.x*g.y-g.x*d.y);isFinite(k)&&(M.copy(h).multiplyScalar(g.y).addScaledVector(f,-d.y).multiplyScalar(k),m.copy(f).multiplyScalar(d.x).addScaledVector(h,-g.x).multiplyScalar(k),o[x].add(M),o[A].add(M),o[N].add(M),l[x].add(m),l[A].add(m),l[N].add(m))}let T=this.groups;T.length===0&&(T=[{start:0,count:e.count}]);for(let x=0,A=T.length;x<A;++x){let N=T[x],k=N.start,V=N.count;for(let $=k,U=k+V;$<U;$+=3)p(e.getX($+0),e.getX($+1),e.getX($+2))}let C=new D,v=new D,w=new D,S=new D;function I(x){w.fromBufferAttribute(s,x),S.copy(w);let A=o[x];C.copy(A),C.sub(w.multiplyScalar(w.dot(A))).normalize(),v.crossVectors(S,A);let k=v.dot(l[x])<0?-1:1;a.setXYZW(x,C.x,C.y,C.z,k)}for(let x=0,A=T.length;x<A;++x){let N=T[x],k=N.start,V=N.count;for(let $=k,U=k+V;$<U;$+=3)I(e.getX($+0)),I(e.getX($+1)),I(e.getX($+2))}this._transformed=!0}computeVertexNormals(){let e=this.index,t=this.getAttribute("position");if(t!==void 0){let n=this.getAttribute("normal");if(n===void 0||n.count!==t.count)n=new Kt(new Float32Array(t.count*3),3),this.setAttribute("normal",n);else for(let u=0,d=n.count;u<d;u++)n.setXYZ(u,0,0,0);let s=new D,r=new D,a=new D,o=new D,l=new D,c=new D,h=new D,f=new D;if(e)for(let u=0,d=e.count;u<d;u+=3){let g=e.getX(u+0),M=e.getX(u+1),m=e.getX(u+2);s.fromBufferAttribute(t,g),r.fromBufferAttribute(t,M),a.fromBufferAttribute(t,m),h.subVectors(a,r),f.subVectors(s,r),h.cross(f),o.fromBufferAttribute(n,g),l.fromBufferAttribute(n,M),c.fromBufferAttribute(n,m),o.add(h),l.add(h),c.add(h),n.setXYZ(g,o.x,o.y,o.z),n.setXYZ(M,l.x,l.y,l.z),n.setXYZ(m,c.x,c.y,c.z)}else for(let u=0,d=t.count;u<d;u+=3)s.fromBufferAttribute(t,u+0),r.fromBufferAttribute(t,u+1),a.fromBufferAttribute(t,u+2),h.subVectors(a,r),f.subVectors(s,r),h.cross(f),n.setXYZ(u+0,h.x,h.y,h.z),n.setXYZ(u+1,h.x,h.y,h.z),n.setXYZ(u+2,h.x,h.y,h.z);this.normalizeNormals(),n.needsUpdate=!0}}normalizeNormals(){let e=this.attributes.normal;for(let t=0,n=e.count;t<n;t++)Yt.fromBufferAttribute(e,t),Yt.normalize(),e.setXYZ(t,Yt.x,Yt.y,Yt.z)}toNonIndexed(){function e(o,l){let c=o.array,h=o.itemSize,f=o.normalized,u=new c.constructor(l.length*h),d=0,g=0;for(let M=0,m=l.length;M<m;M++){o.isInterleavedBufferAttribute?d=l[M]*o.data.stride+o.offset:d=l[M]*h;for(let p=0;p<h;p++)u[g++]=c[d++]}return new Kt(u,h,f)}if(this.index===null)return Je("BufferGeometry.toNonIndexed(): BufferGeometry is already non-indexed."),this;let t=new i,n=this.index.array,s=this.attributes;for(let o in s){let l=s[o],c=e(l,n);t.setAttribute(o,c)}let r=this.morphAttributes;for(let o in r){let l=[],c=r[o];for(let h=0,f=c.length;h<f;h++){let u=c[h],d=e(u,n);l.push(d)}t.morphAttributes[o]=l}t.morphTargetsRelative=this.morphTargetsRelative;let a=this.groups;for(let o=0,l=a.length;o<l;o++){let c=a[o];t.addGroup(c.start,c.count,c.materialIndex)}return t}toJSON(){let e={metadata:{version:4.7,type:"BufferGeometry",generator:"BufferGeometry.toJSON"}};if(e.uuid=this.uuid,e.type=this.parameters!==void 0&&this._transformed===!0?"BufferGeometry":this.type,e.name=this.name,Object.keys(this.userData).length>0&&(e.userData=this.userData),this.parameters!==void 0&&this._transformed!==!0){let l=this.parameters;for(let c in l)l[c]!==void 0&&(e[c]=l[c]);return e}e.data={attributes:{}};let t=this.index;t!==null&&(e.data.index={type:t.array.constructor.name,array:Array.prototype.slice.call(t.array)});let n=this.attributes;for(let l in n){let c=n[l];e.data.attributes[l]=c.toJSON(e.data)}let s={},r=!1;for(let l in this.morphAttributes){let c=this.morphAttributes[l],h=[];for(let f=0,u=c.length;f<u;f++){let d=c[f];h.push(d.toJSON(e.data))}h.length>0&&(s[l]=h,r=!0)}r&&(e.data.morphAttributes=s,e.data.morphTargetsRelative=this.morphTargetsRelative);let a=this.groups;a.length>0&&(e.data.groups=JSON.parse(JSON.stringify(a)));let o=this.boundingSphere;return o!==null&&(e.data.boundingSphere=o.toJSON()),e}clone(){return new this.constructor().copy(this)}copy(e){this.index=null,this.attributes={},this.morphAttributes={},this.groups=[],this.boundingBox=null,this.boundingSphere=null;let t={};this.name=e.name;let n=e.index;n!==null&&this.setIndex(n.clone());let s=e.attributes;for(let c in s){let h=s[c];this.setAttribute(c,h.clone(t))}let r=e.morphAttributes;for(let c in r){let h=[],f=r[c];for(let u=0,d=f.length;u<d;u++)h.push(f[u].clone(t));this.morphAttributes[c]=h}this.morphTargetsRelative=e.morphTargetsRelative;let a=e.groups;for(let c=0,h=a.length;c<h;c++){let f=a[c];this.addGroup(f.start,f.count,f.materialIndex)}let o=e.boundingBox;o!==null&&(this.boundingBox=o.clone());let l=e.boundingSphere;return l!==null&&(this.boundingSphere=l.clone()),this.drawRange.start=e.drawRange.start,this.drawRange.count=e.drawRange.count,this.userData=e.userData,this._transformed=e._transformed,this}dispose(){this.dispatchEvent({type:"dispose"})}};var Il=new D,Ed=new D,wd=new nt,Dn=class{constructor(e=new D(1,0,0),t=0){this.isPlane=!0,this.normal=e,this.constant=t}set(e,t){return this.normal.copy(e),this.constant=t,this}setComponents(e,t,n,s){return this.normal.set(e,t,n),this.constant=s,this}setFromNormalAndCoplanarPoint(e,t){return this.normal.copy(e),this.constant=-t.dot(this.normal),this}setFromCoplanarPoints(e,t,n){let s=Il.subVectors(n,t).cross(Ed.subVectors(e,t)).normalize();return this.setFromNormalAndCoplanarPoint(s,e),this}copy(e){return this.normal.copy(e.normal),this.constant=e.constant,this}normalize(){let e=1/this.normal.length();return this.normal.multiplyScalar(e),this.constant*=e,this}negate(){return this.constant*=-1,this.normal.negate(),this}distanceToPoint(e){return this.normal.dot(e)+this.constant}distanceToSphere(e){return this.distanceToPoint(e.center)-e.radius}projectPoint(e,t){return t.copy(e).addScaledVector(this.normal,-this.distanceToPoint(e))}intersectLine(e,t,n=!0){let s=e.delta(Il),r=this.normal.dot(s);if(r===0)return this.distanceToPoint(e.start)===0?t.copy(e.start):null;let a=-(e.start.dot(this.normal)+this.constant)/r;return n===!0&&(a<0||a>1)?null:t.copy(e.start).addScaledVector(s,a)}intersectsLine(e){let t=this.distanceToPoint(e.start),n=this.distanceToPoint(e.end);return t<0&&n>0||n<0&&t>0}intersectsBox(e){return e.intersectsPlane(this)}intersectsSphere(e){return e.intersectsPlane(this)}coplanarPoint(e){return e.copy(this.normal).multiplyScalar(-this.constant)}applyMatrix4(e,t){let n=t||wd.getNormalMatrix(e),s=this.coplanarPoint(Il).applyMatrix4(e),r=this.normal.applyMatrix3(n).normalize();return this.constant=-s.dot(r),this}translate(e){return this.constant-=e.dot(this.normal),this}equals(e){return e.normal.equals(this.normal)&&e.constant===this.constant}clone(){return new this.constructor().copy(this)}toJSON(){return{normal:this.normal.toArray(),constant:this.constant}}fromJSON(e){return this.normal.fromArray(e.normal),this.constant=e.constant,this}},Ad=0,Fn=class extends Wn{constructor(){super(),this.isMaterial=!0,Object.defineProperty(this,"id",{value:Ad++}),this.uuid=Ds(),this.name="",this.type="Material",this.blending=Is,this.side=Ti,this.vertexColors=!1,this.opacity=1,this.transparent=!1,this.alphaHash=!1,this.blendSrc=Ql,this.blendDst=ec,this.blendEquation=qi,this.blendSrcAlpha=null,this.blendDstAlpha=null,this.blendEquationAlpha=null,this.blendColor=new Ke(0,0,0),this.blendAlpha=0,this.depthFunc=gs,this.depthTest=!0,this.depthWrite=!0,this.stencilWriteMask=255,this.stencilFunc=Hu,this.stencilRef=0,this.stencilFuncMask=255,this.stencilFail=Ea,this.stencilZFail=Ea,this.stencilZPass=Ea,this.stencilWrite=!1,this.clippingPlanes=null,this.clipIntersection=!1,this.clipShadows=!1,this.shadowSide=null,this.colorWrite=!0,this.precision=null,this.polygonOffset=!1,this.polygonOffsetFactor=0,this.polygonOffsetUnits=0,this.dithering=!1,this.alphaToCoverage=!1,this.premultipliedAlpha=!1,this.forceSinglePass=!1,this.allowOverride=!0,this.visible=!0,this.toneMapped=!0,this.userData={},this.version=0,this._alphaTest=0}get alphaTest(){return this._alphaTest}set alphaTest(e){this._alphaTest>0!=e>0&&this.version++,this._alphaTest=e}onBeforeRender(){}onBeforeCompile(){}customProgramCacheKey(){return this.onBeforeCompile.toString()}setValues(e){if(e!==void 0)for(let t in e){let n=e[t];if(n===void 0){Je(`Material: parameter '${t}' has value of undefined.`);continue}let s=this[t];if(s===void 0){Je(`Material: '${t}' is not a property of THREE.${this.type}.`);continue}s&&s.isColor?s.set(n):s&&s.isVector2&&n&&n.isVector2||s&&s.isEuler&&n&&n.isEuler||s&&s.isVector3&&n&&n.isVector3?s.copy(n):this[t]=n}}toJSON(e){let t=e===void 0||typeof e=="string";t&&(e={textures:{},images:{}});let n={metadata:{version:4.7,type:"Material",generator:"Material.toJSON"}};n.uuid=this.uuid,n.type=this.type,n.blending=this.blending,n.side=this.side,n.shadowSide=this.shadowSide,n.vertexColors=this.vertexColors,n.opacity=this.opacity,n.transparent=this.transparent,n.blendSrc=this.blendSrc,n.blendDst=this.blendDst,n.blendEquation=this.blendEquation,n.blendSrcAlpha=this.blendSrcAlpha,n.blendDstAlpha=this.blendDstAlpha,n.blendEquationAlpha=this.blendEquationAlpha,n.blendColor=this.blendColor.getHex(),n.blendAlpha=this.blendAlpha,n.depthFunc=this.depthFunc,n.depthTest=this.depthTest,n.depthWrite=this.depthWrite,n.colorWrite=this.colorWrite,n.clipIntersection=this.clipIntersection,n.clipShadows=this.clipShadows,n.stencilWriteMask=this.stencilWriteMask,n.stencilFunc=this.stencilFunc,n.stencilRef=this.stencilRef,n.stencilFuncMask=this.stencilFuncMask,n.stencilFail=this.stencilFail,n.stencilZFail=this.stencilZFail,n.stencilZPass=this.stencilZPass,n.stencilWrite=this.stencilWrite,n.polygonOffset=this.polygonOffset,n.polygonOffsetFactor=this.polygonOffsetFactor,n.polygonOffsetUnits=this.polygonOffsetUnits,n.dithering=this.dithering,n.alphaTest=this.alphaTest,n.alphaHash=this.alphaHash,n.alphaToCoverage=this.alphaToCoverage,n.premultipliedAlpha=this.premultipliedAlpha,n.forceSinglePass=this.forceSinglePass,n.allowOverride=this.allowOverride,n.visible=this.visible,n.toneMapped=this.toneMapped,n.name=this.name,this.color&&this.color.isColor&&(n.color=this.color.getHex()),this.roughness!==void 0&&(n.roughness=this.roughness),this.metalness!==void 0&&(n.metalness=this.metalness),this.sheen!==void 0&&(n.sheen=this.sheen),this.sheenColor&&this.sheenColor.isColor&&(n.sheenColor=this.sheenColor.getHex()),this.sheenRoughness!==void 0&&(n.sheenRoughness=this.sheenRoughness),this.emissive&&this.emissive.isColor&&(n.emissive=this.emissive.getHex()),this.emissiveIntensity!==void 0&&(n.emissiveIntensity=this.emissiveIntensity),this.specular&&this.specular.isColor&&(n.specular=this.specular.getHex()),this.specularIntensity!==void 0&&(n.specularIntensity=this.specularIntensity),this.specularColor&&this.specularColor.isColor&&(n.specularColor=this.specularColor.getHex()),this.shininess!==void 0&&(n.shininess=this.shininess),this.clearcoat!==void 0&&(n.clearcoat=this.clearcoat),this.clearcoatRoughness!==void 0&&(n.clearcoatRoughness=this.clearcoatRoughness),this.clearcoatMap&&this.clearcoatMap.isTexture&&(n.clearcoatMap=this.clearcoatMap.toJSON(e).uuid),this.clearcoatRoughnessMap&&this.clearcoatRoughnessMap.isTexture&&(n.clearcoatRoughnessMap=this.clearcoatRoughnessMap.toJSON(e).uuid),this.clearcoatNormalMap&&this.clearcoatNormalMap.isTexture&&(n.clearcoatNormalMap=this.clearcoatNormalMap.toJSON(e).uuid,n.clearcoatNormalScale=this.clearcoatNormalScale.toArray()),this.sheenColorMap&&this.sheenColorMap.isTexture&&(n.sheenColorMap=this.sheenColorMap.toJSON(e).uuid),this.sheenRoughnessMap&&this.sheenRoughnessMap.isTexture&&(n.sheenRoughnessMap=this.sheenRoughnessMap.toJSON(e).uuid),this.dispersion!==void 0&&(n.dispersion=this.dispersion),this.retroreflectivity!==void 0&&(n.retroreflectivity=this.retroreflectivity),this.iridescence!==void 0&&(n.iridescence=this.iridescence),this.iridescenceIOR!==void 0&&(n.iridescenceIOR=this.iridescenceIOR),this.iridescenceThicknessRange!==void 0&&(n.iridescenceThicknessRange=this.iridescenceThicknessRange),this.iridescenceMap&&this.iridescenceMap.isTexture&&(n.iridescenceMap=this.iridescenceMap.toJSON(e).uuid),this.iridescenceThicknessMap&&this.iridescenceThicknessMap.isTexture&&(n.iridescenceThicknessMap=this.iridescenceThicknessMap.toJSON(e).uuid),this.anisotropy!==void 0&&(n.anisotropy=this.anisotropy),this.anisotropyRotation!==void 0&&(n.anisotropyRotation=this.anisotropyRotation),this.anisotropyMap&&this.anisotropyMap.isTexture&&(n.anisotropyMap=this.anisotropyMap.toJSON(e).uuid),this.map&&this.map.isTexture&&(n.map=this.map.toJSON(e).uuid),this.matcap&&this.matcap.isTexture&&(n.matcap=this.matcap.toJSON(e).uuid),this.alphaMap&&this.alphaMap.isTexture&&(n.alphaMap=this.alphaMap.toJSON(e).uuid),this.lightMap&&this.lightMap.isTexture&&(n.lightMap=this.lightMap.toJSON(e).uuid,n.lightMapIntensity=this.lightMapIntensity),this.aoMap&&this.aoMap.isTexture&&(n.aoMap=this.aoMap.toJSON(e).uuid,n.aoMapIntensity=this.aoMapIntensity),this.bumpMap&&this.bumpMap.isTexture&&(n.bumpMap=this.bumpMap.toJSON(e).uuid,n.bumpScale=this.bumpScale),this.normalMap&&this.normalMap.isTexture&&(n.normalMap=this.normalMap.toJSON(e).uuid,n.normalMapType=this.normalMapType,n.normalScale=this.normalScale.toArray()),this.displacementMap&&this.displacementMap.isTexture&&(n.displacementMap=this.displacementMap.toJSON(e).uuid,n.displacementScale=this.displacementScale,n.displacementBias=this.displacementBias),this.roughnessMap&&this.roughnessMap.isTexture&&(n.roughnessMap=this.roughnessMap.toJSON(e).uuid),this.metalnessMap&&this.metalnessMap.isTexture&&(n.metalnessMap=this.metalnessMap.toJSON(e).uuid),this.emissiveMap&&this.emissiveMap.isTexture&&(n.emissiveMap=this.emissiveMap.toJSON(e).uuid),this.specularMap&&this.specularMap.isTexture&&(n.specularMap=this.specularMap.toJSON(e).uuid),this.specularIntensityMap&&this.specularIntensityMap.isTexture&&(n.specularIntensityMap=this.specularIntensityMap.toJSON(e).uuid),this.specularColorMap&&this.specularColorMap.isTexture&&(n.specularColorMap=this.specularColorMap.toJSON(e).uuid),this.envMap&&this.envMap.isTexture&&(n.envMap=this.envMap.toJSON(e).uuid,this.combine!==void 0&&(n.combine=this.combine)),this.envMapRotation!==void 0&&(n.envMapRotation=this.envMapRotation.toArray()),this.envMapIntensity!==void 0&&(n.envMapIntensity=this.envMapIntensity),this.reflectivity!==void 0&&(n.reflectivity=this.reflectivity),this.refractionRatio!==void 0&&(n.refractionRatio=this.refractionRatio),this.gradientMap&&this.gradientMap.isTexture&&(n.gradientMap=this.gradientMap.toJSON(e).uuid),this.transmission!==void 0&&(n.transmission=this.transmission),this.transmissionMap&&this.transmissionMap.isTexture&&(n.transmissionMap=this.transmissionMap.toJSON(e).uuid),this.thickness!==void 0&&(n.thickness=this.thickness),this.thicknessMap&&this.thicknessMap.isTexture&&(n.thicknessMap=this.thicknessMap.toJSON(e).uuid),this.attenuationDistance!==void 0&&(n.attenuationDistance=this.attenuationDistance),this.attenuationColor!==void 0&&(n.attenuationColor=this.attenuationColor.getHex()),this.size!==void 0&&(n.size=this.size),this.sizeAttenuation!==void 0&&(n.sizeAttenuation=this.sizeAttenuation),Array.isArray(this.clippingPlanes)&&this.clippingPlanes.length>0&&(n.clippingPlanes=this.clippingPlanes.map(r=>r.toJSON())),this.rotation!==void 0&&(n.rotation=this.rotation),this.depthPacking!==void 0&&(n.depthPacking=this.depthPacking),this.linewidth!==void 0&&(n.linewidth=this.linewidth),this.linecap!==void 0&&(n.linecap=this.linecap),this.linejoin!==void 0&&(n.linejoin=this.linejoin),this.dashSize!==void 0&&(n.dashSize=this.dashSize),this.gapSize!==void 0&&(n.gapSize=this.gapSize),this.scale!==void 0&&(n.scale=this.scale),this.wireframe!==void 0&&(n.wireframe=this.wireframe),this.wireframeLinewidth!==void 0&&(n.wireframeLinewidth=this.wireframeLinewidth),this.wireframeLinecap!==void 0&&(n.wireframeLinecap=this.wireframeLinecap),this.wireframeLinejoin!==void 0&&(n.wireframeLinejoin=this.wireframeLinejoin),this.flatShading!==void 0&&(n.flatShading=this.flatShading),this.fog!==void 0&&(n.fog=this.fog),Object.keys(this.userData).length>0&&(n.userData=this.userData);function s(r){let a=[];for(let o in r){let l=r[o];delete l.metadata,a.push(l)}return a}if(t){let r=s(e.textures),a=s(e.images);r.length>0&&(n.textures=r),a.length>0&&(n.images=a)}return n}fromJSON(e,t){if(e.uuid!==void 0&&(this.uuid=e.uuid),e.name!==void 0&&(this.name=e.name),e.color!==void 0&&this.color!==void 0&&this.color.setHex(e.color),e.roughness!==void 0&&(this.roughness=e.roughness),e.metalness!==void 0&&(this.metalness=e.metalness),e.sheen!==void 0&&(this.sheen=e.sheen),e.sheenColor!==void 0&&(this.sheenColor=new Ke().setHex(e.sheenColor)),e.sheenRoughness!==void 0&&(this.sheenRoughness=e.sheenRoughness),e.emissive!==void 0&&this.emissive!==void 0&&this.emissive.setHex(e.emissive),e.specular!==void 0&&this.specular!==void 0&&this.specular.setHex(e.specular),e.specularIntensity!==void 0&&(this.specularIntensity=e.specularIntensity),e.specularColor!==void 0&&this.specularColor!==void 0&&this.specularColor.setHex(e.specularColor),e.shininess!==void 0&&(this.shininess=e.shininess),e.clearcoat!==void 0&&(this.clearcoat=e.clearcoat),e.clearcoatRoughness!==void 0&&(this.clearcoatRoughness=e.clearcoatRoughness),e.dispersion!==void 0&&(this.dispersion=e.dispersion),e.retroreflectivity!==void 0&&(this.retroreflectivity=e.retroreflectivity),e.iridescence!==void 0&&(this.iridescence=e.iridescence),e.iridescenceIOR!==void 0&&(this.iridescenceIOR=e.iridescenceIOR),e.iridescenceThicknessRange!==void 0&&(this.iridescenceThicknessRange=e.iridescenceThicknessRange),e.transmission!==void 0&&(this.transmission=e.transmission),e.thickness!==void 0&&(this.thickness=e.thickness),e.attenuationDistance!==void 0&&(this.attenuationDistance=e.attenuationDistance),e.attenuationColor!==void 0&&this.attenuationColor!==void 0&&this.attenuationColor.setHex(e.attenuationColor),e.anisotropy!==void 0&&(this.anisotropy=e.anisotropy),e.anisotropyRotation!==void 0&&(this.anisotropyRotation=e.anisotropyRotation),e.fog!==void 0&&(this.fog=e.fog),e.flatShading!==void 0&&(this.flatShading=e.flatShading),e.blending!==void 0&&(this.blending=e.blending),e.combine!==void 0&&(this.combine=e.combine),e.side!==void 0&&(this.side=e.side),e.shadowSide!==void 0&&(this.shadowSide=e.shadowSide),e.opacity!==void 0&&(this.opacity=e.opacity),e.transparent!==void 0&&(this.transparent=e.transparent),e.alphaTest!==void 0&&(this.alphaTest=e.alphaTest),e.alphaHash!==void 0&&(this.alphaHash=e.alphaHash),e.depthFunc!==void 0&&(this.depthFunc=e.depthFunc),e.depthTest!==void 0&&(this.depthTest=e.depthTest),e.depthWrite!==void 0&&(this.depthWrite=e.depthWrite),e.colorWrite!==void 0&&(this.colorWrite=e.colorWrite),e.clippingPlanes!==void 0&&(this.clippingPlanes=e.clippingPlanes.map(n=>new Dn().fromJSON(n))),e.clipIntersection!==void 0&&(this.clipIntersection=e.clipIntersection),e.clipShadows!==void 0&&(this.clipShadows=e.clipShadows),e.depthPacking!==void 0&&(this.depthPacking=e.depthPacking),e.blendSrc!==void 0&&(this.blendSrc=e.blendSrc),e.blendDst!==void 0&&(this.blendDst=e.blendDst),e.blendEquation!==void 0&&(this.blendEquation=e.blendEquation),e.blendSrcAlpha!==void 0&&(this.blendSrcAlpha=e.blendSrcAlpha),e.blendDstAlpha!==void 0&&(this.blendDstAlpha=e.blendDstAlpha),e.blendEquationAlpha!==void 0&&(this.blendEquationAlpha=e.blendEquationAlpha),e.blendColor!==void 0&&this.blendColor!==void 0&&this.blendColor.setHex(e.blendColor),e.blendAlpha!==void 0&&(this.blendAlpha=e.blendAlpha),e.stencilWriteMask!==void 0&&(this.stencilWriteMask=e.stencilWriteMask),e.stencilFunc!==void 0&&(this.stencilFunc=e.stencilFunc),e.stencilRef!==void 0&&(this.stencilRef=e.stencilRef),e.stencilFuncMask!==void 0&&(this.stencilFuncMask=e.stencilFuncMask),e.stencilFail!==void 0&&(this.stencilFail=e.stencilFail),e.stencilZFail!==void 0&&(this.stencilZFail=e.stencilZFail),e.stencilZPass!==void 0&&(this.stencilZPass=e.stencilZPass),e.stencilWrite!==void 0&&(this.stencilWrite=e.stencilWrite),e.wireframe!==void 0&&(this.wireframe=e.wireframe),e.wireframeLinewidth!==void 0&&(this.wireframeLinewidth=e.wireframeLinewidth),e.wireframeLinecap!==void 0&&(this.wireframeLinecap=e.wireframeLinecap),e.wireframeLinejoin!==void 0&&(this.wireframeLinejoin=e.wireframeLinejoin),e.rotation!==void 0&&(this.rotation=e.rotation),e.linewidth!==void 0&&(this.linewidth=e.linewidth),e.linecap!==void 0&&(this.linecap=e.linecap),e.linejoin!==void 0&&(this.linejoin=e.linejoin),e.dashSize!==void 0&&(this.dashSize=e.dashSize),e.gapSize!==void 0&&(this.gapSize=e.gapSize),e.scale!==void 0&&(this.scale=e.scale),e.polygonOffset!==void 0&&(this.polygonOffset=e.polygonOffset),e.polygonOffsetFactor!==void 0&&(this.polygonOffsetFactor=e.polygonOffsetFactor),e.polygonOffsetUnits!==void 0&&(this.polygonOffsetUnits=e.polygonOffsetUnits),e.dithering!==void 0&&(this.dithering=e.dithering),e.alphaToCoverage!==void 0&&(this.alphaToCoverage=e.alphaToCoverage),e.premultipliedAlpha!==void 0&&(this.premultipliedAlpha=e.premultipliedAlpha),e.forceSinglePass!==void 0&&(this.forceSinglePass=e.forceSinglePass),e.allowOverride!==void 0&&(this.allowOverride=e.allowOverride),e.visible!==void 0&&(this.visible=e.visible),e.toneMapped!==void 0&&(this.toneMapped=e.toneMapped),e.userData!==void 0&&(this.userData=e.userData),e.vertexColors!==void 0&&(typeof e.vertexColors=="number"?this.vertexColors=e.vertexColors>0:this.vertexColors=e.vertexColors),e.size!==void 0&&(this.size=e.size),e.sizeAttenuation!==void 0&&(this.sizeAttenuation=e.sizeAttenuation),e.map!==void 0&&(this.map=t[e.map]||null),e.matcap!==void 0&&(this.matcap=t[e.matcap]||null),e.alphaMap!==void 0&&(this.alphaMap=t[e.alphaMap]||null),e.bumpMap!==void 0&&(this.bumpMap=t[e.bumpMap]||null),e.bumpScale!==void 0&&(this.bumpScale=e.bumpScale),e.normalMap!==void 0&&(this.normalMap=t[e.normalMap]||null),e.normalMapType!==void 0&&(this.normalMapType=e.normalMapType),e.normalScale!==void 0){let n=e.normalScale;Array.isArray(n)===!1&&(n=[n,n]),this.normalScale=new Ue().fromArray(n)}return e.displacementMap!==void 0&&(this.displacementMap=t[e.displacementMap]||null),e.displacementScale!==void 0&&(this.displacementScale=e.displacementScale),e.displacementBias!==void 0&&(this.displacementBias=e.displacementBias),e.roughnessMap!==void 0&&(this.roughnessMap=t[e.roughnessMap]||null),e.metalnessMap!==void 0&&(this.metalnessMap=t[e.metalnessMap]||null),e.emissiveMap!==void 0&&(this.emissiveMap=t[e.emissiveMap]||null),e.emissiveIntensity!==void 0&&(this.emissiveIntensity=e.emissiveIntensity),e.specularMap!==void 0&&(this.specularMap=t[e.specularMap]||null),e.specularIntensityMap!==void 0&&(this.specularIntensityMap=t[e.specularIntensityMap]||null),e.specularColorMap!==void 0&&(this.specularColorMap=t[e.specularColorMap]||null),e.envMap!==void 0&&(this.envMap=t[e.envMap]||null),e.envMapRotation!==void 0&&this.envMapRotation.fromArray(e.envMapRotation),e.envMapIntensity!==void 0&&(this.envMapIntensity=e.envMapIntensity),e.reflectivity!==void 0&&(this.reflectivity=e.reflectivity),e.refractionRatio!==void 0&&(this.refractionRatio=e.refractionRatio),e.lightMap!==void 0&&(this.lightMap=t[e.lightMap]||null),e.lightMapIntensity!==void 0&&(this.lightMapIntensity=e.lightMapIntensity),e.aoMap!==void 0&&(this.aoMap=t[e.aoMap]||null),e.aoMapIntensity!==void 0&&(this.aoMapIntensity=e.aoMapIntensity),e.gradientMap!==void 0&&(this.gradientMap=t[e.gradientMap]||null),e.clearcoatMap!==void 0&&(this.clearcoatMap=t[e.clearcoatMap]||null),e.clearcoatRoughnessMap!==void 0&&(this.clearcoatRoughnessMap=t[e.clearcoatRoughnessMap]||null),e.clearcoatNormalMap!==void 0&&(this.clearcoatNormalMap=t[e.clearcoatNormalMap]||null),e.clearcoatNormalScale!==void 0&&(this.clearcoatNormalScale=new Ue().fromArray(e.clearcoatNormalScale)),e.iridescenceMap!==void 0&&(this.iridescenceMap=t[e.iridescenceMap]||null),e.iridescenceThicknessMap!==void 0&&(this.iridescenceThicknessMap=t[e.iridescenceThicknessMap]||null),e.transmissionMap!==void 0&&(this.transmissionMap=t[e.transmissionMap]||null),e.thicknessMap!==void 0&&(this.thicknessMap=t[e.thicknessMap]||null),e.anisotropyMap!==void 0&&(this.anisotropyMap=t[e.anisotropyMap]||null),e.sheenColorMap!==void 0&&(this.sheenColorMap=t[e.sheenColorMap]||null),e.sheenRoughnessMap!==void 0&&(this.sheenRoughnessMap=t[e.sheenRoughnessMap]||null),this}clone(){return new this.constructor().copy(this)}copy(e){this.name=e.name,this.blending=e.blending,this.side=e.side,this.vertexColors=e.vertexColors,this.opacity=e.opacity,this.transparent=e.transparent,this.blendSrc=e.blendSrc,this.blendDst=e.blendDst,this.blendEquation=e.blendEquation,this.blendSrcAlpha=e.blendSrcAlpha,this.blendDstAlpha=e.blendDstAlpha,this.blendEquationAlpha=e.blendEquationAlpha,this.blendColor.copy(e.blendColor),this.blendAlpha=e.blendAlpha,this.depthFunc=e.depthFunc,this.depthTest=e.depthTest,this.depthWrite=e.depthWrite,this.stencilWriteMask=e.stencilWriteMask,this.stencilFunc=e.stencilFunc,this.stencilRef=e.stencilRef,this.stencilFuncMask=e.stencilFuncMask,this.stencilFail=e.stencilFail,this.stencilZFail=e.stencilZFail,this.stencilZPass=e.stencilZPass,this.stencilWrite=e.stencilWrite;let t=e.clippingPlanes,n=null;if(t!==null){let s=t.length;n=new Array(s);for(let r=0;r!==s;++r)n[r]=t[r].clone()}return this.clippingPlanes=n,this.clipIntersection=e.clipIntersection,this.clipShadows=e.clipShadows,this.shadowSide=e.shadowSide,this.colorWrite=e.colorWrite,this.precision=e.precision,this.polygonOffset=e.polygonOffset,this.polygonOffsetFactor=e.polygonOffsetFactor,this.polygonOffsetUnits=e.polygonOffsetUnits,this.dithering=e.dithering,this.alphaTest=e.alphaTest,this.alphaHash=e.alphaHash,this.alphaToCoverage=e.alphaToCoverage,this.premultipliedAlpha=e.premultipliedAlpha,this.forceSinglePass=e.forceSinglePass,this.allowOverride=e.allowOverride,this.visible=e.visible,this.toneMapped=e.toneMapped,this.userData=JSON.parse(JSON.stringify(e.userData)),this}dispose(){this.dispatchEvent({type:"dispose"})}set needsUpdate(e){e===!0&&this.version++}};var ii=new D,Ll=new D,oa=new D,la=new D,zi=class{constructor(e=new D,t=new D(0,0,-1)){this.origin=e,this.direction=t}set(e,t){return this.origin.copy(e),this.direction.copy(t),this}copy(e){return this.origin.copy(e.origin),this.direction.copy(e.direction),this}at(e,t){return t.copy(this.origin).addScaledVector(this.direction,e)}lookAt(e){return this.direction.copy(e).sub(this.origin).normalize(),this}recast(e){return this.origin.copy(this.at(e,ii)),this}closestPointToPoint(e,t){t.subVectors(e,this.origin);let n=t.dot(this.direction);return n<0?t.copy(this.origin):t.copy(this.origin).addScaledVector(this.direction,n)}distanceToPoint(e){return Math.sqrt(this.distanceSqToPoint(e))}distanceSqToPoint(e){let t=ii.subVectors(e,this.origin).dot(this.direction);return t<0?this.origin.distanceToSquared(e):(ii.copy(this.origin).addScaledVector(this.direction,t),ii.distanceToSquared(e))}distanceSqToSegment(e,t,n,s){Ll.copy(e).add(t).multiplyScalar(.5),oa.copy(t).sub(e).normalize(),la.copy(this.origin).sub(Ll);let r=e.distanceTo(t)*.5,a=-this.direction.dot(oa),o=la.dot(this.direction),l=-la.dot(oa),c=la.lengthSq(),h=Math.abs(1-a*a),f,u,d,g;if(h>0)if(f=a*l-o,u=a*o-l,g=r*h,f>=0)if(u>=-g)if(u<=g){let M=1/h;f*=M,u*=M,d=f*(f+a*u+2*o)+u*(a*f+u+2*l)+c}else u=r,f=Math.max(0,-(a*u+o)),d=-f*f+u*(u+2*l)+c;else u=-r,f=Math.max(0,-(a*u+o)),d=-f*f+u*(u+2*l)+c;else u<=-g?(f=Math.max(0,-(-a*r+o)),u=f>0?-r:Math.min(Math.max(-r,-l),r),d=-f*f+u*(u+2*l)+c):u<=g?(f=0,u=Math.min(Math.max(-r,-l),r),d=u*(u+2*l)+c):(f=Math.max(0,-(a*r+o)),u=f>0?r:Math.min(Math.max(-r,-l),r),d=-f*f+u*(u+2*l)+c);else u=a>0?-r:r,f=Math.max(0,-(a*u+o)),d=-f*f+u*(u+2*l)+c;return n&&n.copy(this.origin).addScaledVector(this.direction,f),s&&s.copy(Ll).addScaledVector(oa,u),d}intersectSphere(e,t){if(e.radius<0)return null;ii.subVectors(e.center,this.origin);let n=ii.dot(this.direction),s=ii.dot(ii)-n*n,r=e.radius*e.radius;if(s>r)return null;let a=Math.sqrt(r-s),o=n-a,l=n+a;return l<0?null:o<0?this.at(l,t):this.at(o,t)}intersectsSphere(e){return e.radius<0?!1:this.distanceSqToPoint(e.center)<=e.radius*e.radius}distanceToPlane(e){let t=e.normal.dot(this.direction);if(t===0)return e.distanceToPoint(this.origin)===0?0:null;let n=-(this.origin.dot(e.normal)+e.constant)/t;return n>=0?n:null}intersectPlane(e,t){let n=this.distanceToPlane(e);return n===null?null:this.at(n,t)}intersectsPlane(e){let t=e.distanceToPoint(this.origin);return t===0||e.normal.dot(this.direction)*t<0}intersectBox(e,t){let n,s,r,a,o,l,c=1/this.direction.x,h=1/this.direction.y,f=1/this.direction.z,u=this.origin;return c>=0?(n=(e.min.x-u.x)*c,s=(e.max.x-u.x)*c):(n=(e.max.x-u.x)*c,s=(e.min.x-u.x)*c),h>=0?(r=(e.min.y-u.y)*h,a=(e.max.y-u.y)*h):(r=(e.max.y-u.y)*h,a=(e.min.y-u.y)*h),n>a||r>s||((r>n||isNaN(n))&&(n=r),(a<s||isNaN(s))&&(s=a),f>=0?(o=(e.min.z-u.z)*f,l=(e.max.z-u.z)*f):(o=(e.max.z-u.z)*f,l=(e.min.z-u.z)*f),n>l||o>s)||((o>n||n!==n)&&(n=o),(l<s||s!==s)&&(s=l),s<0)?null:this.at(n>=0?n:s,t)}intersectsBox(e){return this.intersectBox(e,ii)!==null}intersectTriangle(e,t,n,s,r){let a=this.origin,o=this.direction,l=o.x,c=o.y,h=o.z,f=e.x-a.x,u=e.y-a.y,d=e.z-a.z,g=t.x-a.x,M=t.y-a.y,m=t.z-a.z,p=n.x-a.x,T=n.y-a.y,C=n.z-a.z,v=Math.abs(l),w=Math.abs(c),S=Math.abs(h),I,x,A,N,k,V,$,U,W,ee,ie,Z;if(v>=w&&v>=S?(A=l,V=f,W=g,Z=p,l>=0?(I=c,x=h,N=u,k=d,$=M,U=m,ee=T,ie=C):(I=h,x=c,N=d,k=u,$=m,U=M,ee=C,ie=T)):w>=S?(A=c,V=u,W=M,Z=T,c>=0?(I=h,x=l,N=d,k=f,$=m,U=g,ee=C,ie=p):(I=l,x=h,N=f,k=d,$=g,U=m,ee=p,ie=C)):(A=h,V=d,W=m,Z=C,h>=0?(I=l,x=c,N=f,k=u,$=g,U=M,ee=p,ie=T):(I=c,x=l,N=u,k=f,$=M,U=g,ee=T,ie=p)),A===0)return null;let Q=I/A,ue=x/A,se=1/A,Ge=N-Q*V,Pe=k-ue*V,ot=$-Q*W,$e=U-ue*W,Xe=ee-Q*Z,K=ie-ue*Z,re=Xe*$e-K*ot,Se=Ge*K-Pe*Xe,Le=ot*Pe-$e*Ge;if(s){if(re<0||Se<0||Le<0)return null}else if((re<0||Se<0||Le<0)&&(re>0||Se>0||Le>0))return null;let Ie=re+Se+Le;if(Ie===0)return null;let Ze=se*(re*V+Se*W+Le*Z);return(Ie>0?Ze<0:Ze>0)?null:this.at(Ze/Ie,r)}applyMatrix4(e){return this.origin.applyMatrix4(e),this.direction.transformDirection(e),this}equals(e){return e.origin.equals(this.origin)&&e.direction.equals(this.direction)}clone(){return new this.constructor().copy(this)}},fn=class extends Fn{constructor(e){super(),this.isMeshBasicMaterial=!0,this.type="MeshBasicMaterial",this.color=new Ke(16777215),this.map=null,this.lightMap=null,this.lightMapIntensity=1,this.aoMap=null,this.aoMapIntensity=1,this.specularMap=null,this.alphaMap=null,this.envMap=null,this.envMapRotation=new En,this.combine=co,this.reflectivity=1,this.refractionRatio=.98,this.wireframe=!1,this.wireframeLinewidth=1,this.wireframeLinecap="round",this.wireframeLinejoin="round",this.fog=!0,this.setValues(e)}copy(e){return super.copy(e),this.color.copy(e.color),this.map=e.map,this.lightMap=e.lightMap,this.lightMapIntensity=e.lightMapIntensity,this.aoMap=e.aoMap,this.aoMapIntensity=e.aoMapIntensity,this.specularMap=e.specularMap,this.alphaMap=e.alphaMap,this.envMap=e.envMap,this.envMapRotation.copy(e.envMapRotation),this.combine=e.combine,this.reflectivity=e.reflectivity,this.refractionRatio=e.refractionRatio,this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this.wireframeLinecap=e.wireframeLinecap,this.wireframeLinejoin=e.wireframeLinejoin,this.fog=e.fog,this}},jc=new pt,Fi=new zi,ca=new Xn,Jc=new D,ua=new D,ha=new D,da=new D,Nl=new D,fa=new D,Kc=new D,pa=new D,yt=class extends Ht{constructor(e=new Rt,t=new fn){super(),this.isMesh=!0,this.type="Mesh",this.geometry=e,this.material=t,this.morphTargetDictionary=void 0,this.morphTargetInfluences=void 0,this.count=1,this.updateMorphTargets()}copy(e,t){return super.copy(e,t),e.morphTargetInfluences!==void 0&&(this.morphTargetInfluences=e.morphTargetInfluences.slice()),e.morphTargetDictionary!==void 0&&(this.morphTargetDictionary=Object.assign({},e.morphTargetDictionary)),this.material=Array.isArray(e.material)?e.material.slice():e.material,this.geometry=e.geometry,this}updateMorphTargets(){let t=this.geometry.morphAttributes,n=Object.keys(t);if(n.length>0){let s=t[n[0]];if(s!==void 0){this.morphTargetInfluences=[],this.morphTargetDictionary={};for(let r=0,a=s.length;r<a;r++){let o=s[r].name||String(r);this.morphTargetInfluences.push(0),this.morphTargetDictionary[o]=r}}}}getVertexPosition(e,t){let n=this.geometry,s=n.attributes.position,r=n.morphAttributes.position,a=n.morphTargetsRelative;t.fromBufferAttribute(s,e);let o=this.morphTargetInfluences;if(r&&o){fa.set(0,0,0);for(let l=0,c=r.length;l<c;l++){let h=o[l],f=r[l];h!==0&&(Nl.fromBufferAttribute(f,e),a?fa.addScaledVector(Nl,h):fa.addScaledVector(Nl.sub(t),h))}t.add(fa)}return t}intersectsFrustum(e){return e.intersectsObject(this)}raycast(e,t){let n=this.geometry,s=this.material,r=this.matrixWorld;s!==void 0&&(n.boundingSphere===null&&n.computeBoundingSphere(),ca.copy(n.boundingSphere),ca.applyMatrix4(r),Fi.copy(e.ray).recast(e.near),!(ca.containsPoint(Fi.origin)===!1&&(Fi.intersectSphere(ca,Jc)===null||Fi.origin.distanceToSquared(Jc)>(e.far-e.near)**2))&&(jc.copy(r).invert(),Fi.copy(e.ray).applyMatrix4(jc),!(n.boundingBox!==null&&Fi.intersectsBox(n.boundingBox)===!1)&&this._computeIntersections(e,t,Fi)))}_computeIntersections(e,t,n){let s,r=this.geometry,a=this.material,o=r.index,l=r.attributes.position,c=r.attributes.uv,h=r.attributes.uv1,f=r.attributes.normal,u=r.groups,d=r.drawRange;if(o!==null)if(Array.isArray(a))for(let g=0,M=u.length;g<M;g++){let m=u[g],p=a[m.materialIndex],T=Math.max(m.start,d.start),C=Math.min(o.count,Math.min(m.start+m.count,d.start+d.count));for(let v=T,w=C;v<w;v+=3){let S=o.getX(v),I=o.getX(v+1),x=o.getX(v+2);s=ma(this,p,e,n,c,h,f,S,I,x),s&&(s.faceIndex=Math.floor(v/3),s.face.materialIndex=m.materialIndex,t.push(s))}}else{let g=Math.max(0,d.start),M=Math.min(o.count,d.start+d.count);for(let m=g,p=M;m<p;m+=3){let T=o.getX(m),C=o.getX(m+1),v=o.getX(m+2);s=ma(this,a,e,n,c,h,f,T,C,v),s&&(s.faceIndex=Math.floor(m/3),t.push(s))}}else if(l!==void 0)if(Array.isArray(a))for(let g=0,M=u.length;g<M;g++){let m=u[g],p=a[m.materialIndex],T=Math.max(m.start,d.start),C=Math.min(l.count,Math.min(m.start+m.count,d.start+d.count));for(let v=T,w=C;v<w;v+=3){let S=v,I=v+1,x=v+2;s=ma(this,p,e,n,c,h,f,S,I,x),s&&(s.faceIndex=Math.floor(v/3),s.face.materialIndex=m.materialIndex,t.push(s))}}else{let g=Math.max(0,d.start),M=Math.min(l.count,d.start+d.count);for(let m=g,p=M;m<p;m+=3){let T=m,C=m+1,v=m+2;s=ma(this,a,e,n,c,h,f,T,C,v),s&&(s.faceIndex=Math.floor(m/3),t.push(s))}}}};function Cd(i,e,t,n,s,r,a,o){let l;if(e.side===en?l=n.intersectTriangle(a,r,s,!0,o):l=n.intersectTriangle(s,r,a,e.side===Ti,o),l===null)return null;pa.copy(o),pa.applyMatrix4(i.matrixWorld);let c=t.ray.origin.distanceTo(pa);return c<t.near||c>t.far?null:{distance:c,point:pa.clone(),object:i}}function ma(i,e,t,n,s,r,a,o,l,c){i.getVertexPosition(o,ua),i.getVertexPosition(l,ha),i.getVertexPosition(c,da);let h=Cd(i,e,t,n,ua,ha,da,Kc);if(h){let f=new D;xi.getBarycoord(Kc,ua,ha,da,f),s&&(h.uv=xi.getInterpolatedAttribute(s,o,l,c,f,new Ue)),r&&(h.uv1=xi.getInterpolatedAttribute(r,o,l,c,f,new Ue)),a&&(h.normal=xi.getInterpolatedAttribute(a,o,l,c,f,new D),h.normal.dot(n.direction)>0&&h.normal.multiplyScalar(-1));let u={a:o,b:l,c,normal:new D,materialIndex:0};xi.getNormal(ua,ha,da,u.normal),h.face=u,h.barycoord=f}return h}var ur=class extends mn{constructor(e=null,t=1,n=1,s,r,a,o,l,c=Zt,h=Zt,f,u){super(null,a,o,l,c,h,s,r,f,u),this.isDataTexture=!0,this.image={data:e,width:t,height:n},this.generateMipmaps=!1,this.flipY=!1,this.unpackAlignment=1}};var hr=class extends Kt{constructor(e,t,n,s=1){super(e,t,n),this.isInstancedBufferAttribute=!0,this.meshPerAttribute=s}copy(e){return super.copy(e),this.meshPerAttribute=e.meshPerAttribute,this}toJSON(){let e=super.toJSON();return e.meshPerAttribute=this.meshPerAttribute,e.isInstancedBufferAttribute=!0,e}},us=new pt,Qc=new pt,ga=[],eu=new qn,Rd=new pt,Zs=new yt,js=new Xn,gn=class extends yt{constructor(e,t,n){super(e,t),this.isInstancedMesh=!0,this.instanceMatrix=new hr(new Float32Array(n*16),16),this.instanceColor=null,this.morphTexture=null,this.count=n,this.boundingBox=null,this.boundingSphere=null;for(let s=0;s<n;s++)this.setMatrixAt(s,Rd)}computeBoundingBox(){let e=this.geometry,t=this.count;this.boundingBox===null&&(this.boundingBox=new qn),e.boundingBox===null&&e.computeBoundingBox(),this.boundingBox.makeEmpty();for(let n=0;n<t;n++)this.getMatrixAt(n,us),eu.copy(e.boundingBox).applyMatrix4(us),this.boundingBox.union(eu)}computeBoundingSphere(){let e=this.geometry,t=this.count;this.boundingSphere===null&&(this.boundingSphere=new Xn),e.boundingSphere===null&&e.computeBoundingSphere(),this.boundingSphere.makeEmpty();for(let n=0;n<t;n++)this.getMatrixAt(n,us),js.copy(e.boundingSphere).applyMatrix4(us),this.boundingSphere.union(js)}copy(e,t){return super.copy(e,t),this.instanceMatrix.copy(e.instanceMatrix),e.morphTexture!==null&&(this.morphTexture=e.morphTexture.clone()),e.instanceColor!==null&&(this.instanceColor=e.instanceColor.clone()),this.count=e.count,e.boundingBox!==null&&(this.boundingBox=e.boundingBox.clone()),e.boundingSphere!==null&&(this.boundingSphere=e.boundingSphere.clone()),this}getColorAt(e,t){return this.instanceColor===null?t.setRGB(1,1,1):t.fromArray(this.instanceColor.array,e*3)}getMatrixAt(e,t){return t.fromArray(this.instanceMatrix.array,e*16)}getMorphAt(e,t){let n=t.morphTargetInfluences,s=this.morphTexture.source.data.data,r=n.length+1,a=e*r+1;for(let o=0;o<n.length;o++)n[o]=s[a+o]}raycast(e,t){let n=this.matrixWorld,s=this.count;if(Zs.geometry=this.geometry,Zs.material=this.material,Zs.material!==void 0&&(this.boundingSphere===null&&this.computeBoundingSphere(),js.copy(this.boundingSphere),js.applyMatrix4(n),e.ray.intersectsSphere(js)!==!1))for(let r=0;r<s;r++){this.getMatrixAt(r,us),Qc.multiplyMatrices(n,us),Zs.matrixWorld=Qc,Zs.raycast(e,ga);for(let a=0,o=ga.length;a<o;a++){let l=ga[a];l.instanceId=r,l.object=this,t.push(l)}ga.length=0}}setColorAt(e,t){return this.instanceColor===null&&(this.instanceColor=new hr(new Float32Array(this.instanceMatrix.count*3).fill(1),3)),t.toArray(this.instanceColor.array,e*3),this}setMatrixAt(e,t){return t.toArray(this.instanceMatrix.array,e*16),this}setMorphAt(e,t){let n=t.morphTargetInfluences,s=n.length+1;this.morphTexture===null&&(this.morphTexture=new ur(new Float32Array(s*this.count),s,this.count,_o,Rn));let r=this.morphTexture.source.data.data,a=0;for(let c=0;c<n.length;c++)a+=n[c];let o=this.geometry.morphTargetsRelative?1:1-a,l=s*e;return r[l]=o,r.set(n,l+1),this}updateMorphTargets(){}dispose(){super.dispose(),this.morphTexture!==null&&(this.morphTexture.dispose(),this.morphTexture=null)}},ki=new Xn,Pd=new Ue(.5,.5),_a=new D,Ss=class{constructor(e=new Dn,t=new Dn,n=new Dn,s=new Dn,r=new Dn,a=new Dn){this.planes=[e,t,n,s,r,a]}set(e,t,n,s,r,a){let o=this.planes;return o[0].copy(e),o[1].copy(t),o[2].copy(n),o[3].copy(s),o[4].copy(r),o[5].copy(a),this}copy(e){let t=this.planes;for(let n=0;n<6;n++)t[n].copy(e.planes[n]);return this}setFromProjectionMatrix(e,t=Un,n=!1){let s=this.planes,r=e.elements,a=r[0],o=r[1],l=r[2],c=r[3],h=r[4],f=r[5],u=r[6],d=r[7],g=r[8],M=r[9],m=r[10],p=r[11],T=r[12],C=r[13],v=r[14],w=r[15];if(s[0].setComponents(c-a,d-h,p-g,w-T).normalize(),s[1].setComponents(c+a,d+h,p+g,w+T).normalize(),s[2].setComponents(c+o,d+f,p+M,w+C).normalize(),s[3].setComponents(c-o,d-f,p-M,w-C).normalize(),n)s[4].setComponents(l,u,m,v).normalize(),s[5].setComponents(c-l,d-u,p-m,w-v).normalize();else if(s[4].setComponents(c-l,d-u,p-m,w-v).normalize(),t===Un)s[5].setComponents(c+l,d+u,p+m,w+v).normalize();else if(t===_s)s[5].setComponents(l,u,m,v).normalize();else throw new Error("THREE.Frustum.setFromProjectionMatrix(): Invalid coordinate system: "+t);return this}intersectsObject(e){if(e.boundingSphere!==void 0)e.boundingSphere===null&&e.computeBoundingSphere(),ki.copy(e.boundingSphere).applyMatrix4(e.matrixWorld);else{let t=e.geometry;t.boundingSphere===null&&t.computeBoundingSphere(),ki.copy(t.boundingSphere).applyMatrix4(e.matrixWorld)}return this.intersectsSphere(ki)}intersectsSprite(e){ki.center.set(0,0,0);let t=Pd.distanceTo(e.center);return ki.radius=.7071067811865476+t,ki.applyMatrix4(e.matrixWorld),this.intersectsSphere(ki)}intersectsSphere(e){let t=this.planes,n=e.center,s=-e.radius;for(let r=0;r<6;r++)if(t[r].distanceToPoint(n)<s)return!1;return!0}intersectsBox(e){let t=this.planes;for(let n=0;n<6;n++){let s=t[n];if(_a.x=s.normal.x>0?e.max.x:e.min.x,_a.y=s.normal.y>0?e.max.y:e.min.y,_a.z=s.normal.z>0?e.max.z:e.min.z,s.distanceToPoint(_a)<0)return!1}return!0}containsPoint(e){let t=this.planes;for(let n=0;n<6;n++)if(t[n].distanceToPoint(e)<0)return!1;return!0}clone(){return new this.constructor().copy(this)}};var ri=class extends Fn{constructor(e){super(),this.isLineBasicMaterial=!0,this.type="LineBasicMaterial",this.color=new Ke(16777215),this.map=null,this.linewidth=1,this.linecap="round",this.linejoin="round",this.fog=!0,this.setValues(e)}copy(e){return super.copy(e),this.color.copy(e.color),this.map=e.map,this.linewidth=e.linewidth,this.linecap=e.linecap,this.linejoin=e.linejoin,this.fog=e.fog,this}},Ba=new D,za=new D,tu=new pt,Js=new zi,xa=new Xn,Dl=new D,nu=new D,Vi=class extends Ht{constructor(e=new Rt,t=new ri){super(),this.isLine=!0,this.type="Line",this.geometry=e,this.material=t,this.morphTargetDictionary=void 0,this.morphTargetInfluences=void 0,this.updateMorphTargets()}copy(e,t){return super.copy(e,t),this.material=Array.isArray(e.material)?e.material.slice():e.material,this.geometry=e.geometry,this}computeLineDistances(){let e=this.geometry;if(e.index===null){let t=e.attributes.position,n=[0];for(let s=1,r=t.count;s<r;s++)Ba.fromBufferAttribute(t,s-1),za.fromBufferAttribute(t,s),n[s]=n[s-1],n[s]+=Ba.distanceTo(za);e.setAttribute("lineDistance",new vt(n,1))}else Je("Line.computeLineDistances(): Computation only possible with non-indexed BufferGeometry.");return this}intersectsFrustum(e){return e.intersectsObject(this)}raycast(e,t){let n=this.geometry,s=this.matrixWorld,r=e.params.Line.threshold,a=n.drawRange;if(n.boundingSphere===null&&n.computeBoundingSphere(),xa.copy(n.boundingSphere),xa.applyMatrix4(s),xa.radius+=r,e.ray.intersectsSphere(xa)===!1)return;tu.copy(s).invert(),Js.copy(e.ray).applyMatrix4(tu);let o=r/((this.scale.x+this.scale.y+this.scale.z)/3),l=o*o,c=this.isLineSegments?2:1,h=n.index,u=n.attributes.position;if(h!==null){let d=Math.max(0,a.start),g=Math.min(h.count,a.start+a.count);for(let M=d,m=g-1;M<m;M+=c){let p=h.getX(M),T=h.getX(M+1),C=va(this,e,Js,l,p,T,M);C&&t.push(C)}if(this.isLineLoop){let M=h.getX(g-1),m=h.getX(d),p=va(this,e,Js,l,M,m,g-1);p&&t.push(p)}}else{let d=Math.max(0,a.start),g=Math.min(u.count,a.start+a.count);for(let M=d,m=g-1;M<m;M+=c){let p=va(this,e,Js,l,M,M+1,M);p&&t.push(p)}if(this.isLineLoop){let M=va(this,e,Js,l,g-1,d,g-1);M&&t.push(M)}}}updateMorphTargets(){let t=this.geometry.morphAttributes,n=Object.keys(t);if(n.length>0){let s=t[n[0]];if(s!==void 0){this.morphTargetInfluences=[],this.morphTargetDictionary={};for(let r=0,a=s.length;r<a;r++){let o=s[r].name||String(r);this.morphTargetInfluences.push(0),this.morphTargetDictionary[o]=r}}}}};function va(i,e,t,n,s,r,a){let o=i.geometry.attributes.position;if(Ba.fromBufferAttribute(o,s),za.fromBufferAttribute(o,r),t.distanceSqToSegment(Ba,za,Dl,nu)>n)return;Dl.applyMatrix4(i.matrixWorld);let c=e.ray.origin.distanceTo(Dl);if(!(c<e.near||c>e.far))return{distance:c,point:nu.clone().applyMatrix4(i.matrixWorld),index:a,face:null,faceIndex:null,barycoord:null,object:i}}var dr=class extends Vi{constructor(e,t){super(e,t),this.isLineLoop=!0,this.type="LineLoop"}},Ts=class extends Fn{constructor(e){super(),this.isPointsMaterial=!0,this.type="PointsMaterial",this.color=new Ke(16777215),this.map=null,this.alphaMap=null,this.size=1,this.sizeAttenuation=!0,this.fog=!0,this.setValues(e)}copy(e){return super.copy(e),this.color.copy(e.color),this.map=e.map,this.alphaMap=e.alphaMap,this.size=e.size,this.sizeAttenuation=e.sizeAttenuation,this.fog=e.fog,this}},iu=new pt,Wl=new zi,ya=new Xn,Ma=new D,fr=class extends Ht{constructor(e=new Rt,t=new Ts){super(),this.isPoints=!0,this.type="Points",this.geometry=e,this.material=t,this.morphTargetDictionary=void 0,this.morphTargetInfluences=void 0,this.updateMorphTargets()}copy(e,t){return super.copy(e,t),this.material=Array.isArray(e.material)?e.material.slice():e.material,this.geometry=e.geometry,this}intersectsFrustum(e){return e.intersectsObject(this)}raycast(e,t){let n=this.geometry,s=this.matrixWorld,r=e.params.Points.threshold,a=n.drawRange;if(n.boundingSphere===null&&n.computeBoundingSphere(),ya.copy(n.boundingSphere),ya.applyMatrix4(s),ya.radius+=r,e.ray.intersectsSphere(ya)===!1)return;iu.copy(s).invert(),Wl.copy(e.ray).applyMatrix4(iu);let o=r/((this.scale.x+this.scale.y+this.scale.z)/3),l=o*o,c=n.index,f=n.attributes.position;if(c!==null){let u=Math.max(0,a.start),d=Math.min(c.count,a.start+a.count);for(let g=u,M=d;g<M;g++){let m=c.getX(g);Ma.fromBufferAttribute(f,m),su(Ma,m,l,s,e,t,this)}}else{let u=Math.max(0,a.start),d=Math.min(f.count,a.start+a.count);for(let g=u,M=d;g<M;g++)Ma.fromBufferAttribute(f,g),su(Ma,g,l,s,e,t,this)}}updateMorphTargets(){let t=this.geometry.morphAttributes,n=Object.keys(t);if(n.length>0){let s=t[n[0]];if(s!==void 0){this.morphTargetInfluences=[],this.morphTargetDictionary={};for(let r=0,a=s.length;r<a;r++){let o=s[r].name||String(r);this.morphTargetInfluences.push(0),this.morphTargetDictionary[o]=r}}}}};function su(i,e,t,n,s,r,a){let o=Wl.distanceSqToPoint(i);if(o<t){let l=new D;Wl.closestPointToPoint(i,l),l.applyMatrix4(n);let c=s.ray.origin.distanceTo(l);if(c<s.near||c>s.far)return;r.push({distance:c,distanceToRay:Math.sqrt(o),point:l,index:e,face:null,faceIndex:null,barycoord:null,object:a})}}var pr=class extends mn{constructor(e=[],t=Ei,n,s,r,a,o,l,c,h){super(e,t,n,s,r,a,o,l,c,h),this.isCubeTexture=!0,this.flipY=!1}get images(){return this.image}set images(e){this.image=e}};var vi=class extends mn{constructor(e,t,n=Bn,s,r,a,o=Zt,l=Zt,c,h=Gn,f=1){if(h!==Gn&&h!==Ai)throw new Error("THREE.DepthTexture: format must be either THREE.DepthFormat or THREE.DepthStencilFormat");let u={width:e,height:t,depth:f};super(u,s,r,a,o,l,h,n,c),this.isDepthTexture=!0,this.flipY=!1,this.generateMipmaps=!1,this.compareFunction=null}copy(e){return super.copy(e),this.source=new ys(Object.assign({},e.image)),this.compareFunction=e.compareFunction,this}toJSON(e){let t=super.toJSON(e);return t.compareFunction=this.compareFunction,t}},Va=class extends vi{constructor(e,t=Bn,n=Ei,s,r,a=Zt,o=Zt,l,c=Gn){let h={width:e,height:e,depth:1},f=[h,h,h,h,h,h];super(e,e,t,n,s,r,a,o,l,c),this.image=f,this.isCubeDepthTexture=!0,this.isCubeTexture=!0}get images(){return this.image}set images(e){this.image=e}},mr=class extends mn{constructor(e=null){super(),this.sourceTexture=e,this.isExternalTexture=!0}copy(e){return super.copy(e),this.sourceTexture=e.sourceTexture,this}},kn=class i extends Rt{constructor(e=1,t=1,n=1,s=1,r=1,a=1){super(),this.type="BoxGeometry",this.parameters={width:e,height:t,depth:n,widthSegments:s,heightSegments:r,depthSegments:a};let o=this;s=Math.floor(s),r=Math.floor(r),a=Math.floor(a);let l=[],c=[],h=[],f=[],u=0,d=0;g("z","y","x",-1,-1,n,t,e,a,r,0),g("z","y","x",1,-1,n,t,-e,a,r,1),g("x","z","y",1,1,e,n,t,s,a,2),g("x","z","y",1,-1,e,n,-t,s,a,3),g("x","y","z",1,-1,e,t,n,s,r,4),g("x","y","z",-1,-1,e,t,-n,s,r,5),this.setIndex(l),this.setAttribute("position",new vt(c,3)),this.setAttribute("normal",new vt(h,3)),this.setAttribute("uv",new vt(f,2));function g(M,m,p,T,C,v,w,S,I,x,A){let N=v/I,k=w/x,V=v/2,$=w/2,U=S/2,W=I+1,ee=x+1,ie=0,Z=0,Q=new D;for(let ue=0;ue<ee;ue++){let se=ue*k-$;for(let Ge=0;Ge<W;Ge++){let Pe=Ge*N-V;Q[M]=Pe*T,Q[m]=se*C,Q[p]=U,c.push(Q.x,Q.y,Q.z),Q[M]=0,Q[m]=0,Q[p]=S>0?1:-1,h.push(Q.x,Q.y,Q.z),f.push(Ge/I),f.push(1-ue/x),ie+=1}}for(let ue=0;ue<x;ue++)for(let se=0;se<I;se++){let Ge=u+se+W*ue,Pe=u+se+W*(ue+1),ot=u+(se+1)+W*(ue+1),$e=u+(se+1)+W*ue;l.push(Ge,Pe,$e),l.push(Pe,ot,$e),Z+=6}o.addGroup(d,Z,A),d+=Z,u+=ie}}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}static fromJSON(e){return new i(e.width,e.height,e.depth,e.widthSegments,e.heightSegments,e.depthSegments)}};var $n=class i extends Rt{constructor(e=1,t=1,n=1,s=32,r=1,a=!1,o=0,l=Math.PI*2){super(),this.type="CylinderGeometry",this.parameters={radiusTop:e,radiusBottom:t,height:n,radialSegments:s,heightSegments:r,openEnded:a,thetaStart:o,thetaLength:l};let c=this;s=Math.floor(s),r=Math.floor(r);let h=[],f=[],u=[],d=[],g=0,M=[],m=n/2,p=0;T(),a===!1&&(e>0&&C(!0),t>0&&C(!1)),this.setIndex(h),this.setAttribute("position",new vt(f,3)),this.setAttribute("normal",new vt(u,3)),this.setAttribute("uv",new vt(d,2));function T(){let v=new D,w=new D,S=0,I=(t-e)/n;for(let x=0;x<=r;x++){let A=[],N=x/r,k=N*(t-e)+e;for(let V=0;V<=s;V++){let $=V/s,U=$*l+o,W=Math.sin(U),ee=Math.cos(U);w.x=k*W,w.y=-N*n+m,w.z=k*ee,f.push(w.x,w.y,w.z),v.set(W,I,ee).normalize(),u.push(v.x,v.y,v.z),d.push($,1-N),A.push(g++)}M.push(A)}for(let x=0;x<s;x++)for(let A=0;A<r;A++){let N=M[A][x],k=M[A+1][x],V=M[A+1][x+1],$=M[A][x+1];(e>0||A!==0)&&(h.push(N,k,$),S+=3),(t>0||A!==r-1)&&(h.push(k,V,$),S+=3)}c.addGroup(p,S,0),p+=S}function C(v){let w=g,S=new Ue,I=new D,x=0,A=v===!0?e:t,N=v===!0?1:-1;for(let V=1;V<=s;V++)f.push(0,m*N,0),u.push(0,N,0),d.push(.5,.5),g++;let k=g;for(let V=0;V<=s;V++){let U=V/s*l+o,W=Math.cos(U),ee=Math.sin(U);I.x=A*ee,I.y=m*N,I.z=A*W,f.push(I.x,I.y,I.z),u.push(0,N,0),S.x=W*.5+.5,S.y=ee*.5*N+.5,d.push(S.x,S.y),g++}for(let V=0;V<s;V++){let $=w+V,U=k+V;v===!0?h.push(U,U+1,$):h.push(U+1,U,$),x+=3}c.addGroup(p,x,v===!0?1:2),p+=x}}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}static fromJSON(e){return new i(e.radiusTop,e.radiusBottom,e.height,e.radialSegments,e.heightSegments,e.openEnded,e.thetaStart,e.thetaLength)}},gr=class i extends $n{constructor(e=1,t=1,n=32,s=1,r=!1,a=0,o=Math.PI*2){super(0,e,t,n,s,r,a,o),this.type="ConeGeometry",this.parameters={radius:e,height:t,radialSegments:n,heightSegments:s,openEnded:r,thetaStart:a,thetaLength:o}}static fromJSON(e){return new i(e.radius,e.height,e.radialSegments,e.heightSegments,e.openEnded,e.thetaStart,e.thetaLength)}},Es=class i extends Rt{constructor(e=[],t=[],n=1,s=0){super(),this.type="PolyhedronGeometry",this.parameters={vertices:e,indices:t,radius:n,detail:s};let r=[],a=[];o(s),c(n),h(),this.setAttribute("position",new vt(r,3)),this.setAttribute("normal",new vt(r.slice(),3)),this.setAttribute("uv",new vt(a,2)),s===0?this.computeVertexNormals():this.normalizeNormals();function o(T){let C=new D,v=new D,w=new D;for(let S=0;S<t.length;S+=3)d(t[S+0],C),d(t[S+1],v),d(t[S+2],w),l(C,v,w,T)}function l(T,C,v,w){let S=w+1,I=[];for(let x=0;x<=S;x++){I[x]=[];let A=T.clone().lerp(v,x/S),N=C.clone().lerp(v,x/S),k=S-x;for(let V=0;V<=k;V++)V===0&&x===S?I[x][V]=A:I[x][V]=A.clone().lerp(N,V/k)}for(let x=0;x<S;x++)for(let A=0;A<2*(S-x)-1;A++){let N=Math.floor(A/2);A%2===0?(u(I[x][N+1]),u(I[x+1][N]),u(I[x][N])):(u(I[x][N+1]),u(I[x+1][N+1]),u(I[x+1][N]))}}function c(T){let C=new D;for(let v=0;v<r.length;v+=3)C.x=r[v+0],C.y=r[v+1],C.z=r[v+2],C.normalize().multiplyScalar(T),r[v+0]=C.x,r[v+1]=C.y,r[v+2]=C.z}function h(){let T=new D;for(let C=0;C<r.length;C+=3){T.x=r[C+0],T.y=r[C+1],T.z=r[C+2];let v=m(T)/2/Math.PI+.5,w=p(T)/Math.PI+.5;a.push(v,1-w)}g(),f()}function f(){for(let T=0;T<a.length;T+=6){let C=a[T+0],v=a[T+2],w=a[T+4],S=Math.max(C,v,w),I=Math.min(C,v,w);S>.9&&I<.1&&(C<.2&&(a[T+0]+=1),v<.2&&(a[T+2]+=1),w<.2&&(a[T+4]+=1))}}function u(T){r.push(T.x,T.y,T.z)}function d(T,C){let v=T*3;C.x=e[v+0],C.y=e[v+1],C.z=e[v+2]}function g(){let T=new D,C=new D,v=new D,w=new D,S=new Ue,I=new Ue,x=new Ue;for(let A=0,N=0;A<r.length;A+=9,N+=6){T.set(r[A+0],r[A+1],r[A+2]),C.set(r[A+3],r[A+4],r[A+5]),v.set(r[A+6],r[A+7],r[A+8]),S.set(a[N+0],a[N+1]),I.set(a[N+2],a[N+3]),x.set(a[N+4],a[N+5]),w.copy(T).add(C).add(v).divideScalar(3);let k=m(w);M(S,N+0,T,k),M(I,N+2,C,k),M(x,N+4,v,k)}}function M(T,C,v,w){w<0&&T.x===1&&(a[C]=T.x-1),v.x===0&&v.z===0&&(a[C]=w/2/Math.PI+.5)}function m(T){return Math.atan2(T.z,-T.x)}function p(T){return Math.atan2(-T.y,Math.sqrt(T.x*T.x+T.z*T.z))}}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}static fromJSON(e){return new i(e.vertices,e.indices,e.radius,e.detail)}},_r=class i extends Es{constructor(e=1,t=0){let n=(1+Math.sqrt(5))/2,s=1/n,r=[-1,-1,-1,-1,-1,1,-1,1,-1,-1,1,1,1,-1,-1,1,-1,1,1,1,-1,1,1,1,0,-s,-n,0,-s,n,0,s,-n,0,s,n,-s,-n,0,-s,n,0,s,-n,0,s,n,0,-n,0,-s,n,0,-s,-n,0,s,n,0,s],a=[3,11,7,3,7,15,3,15,13,7,19,17,7,17,6,7,6,15,17,4,8,17,8,10,17,10,6,8,0,16,8,16,2,8,2,10,0,12,1,0,1,18,0,18,16,6,10,2,6,2,13,6,13,15,2,16,18,2,18,3,2,3,13,18,1,9,18,9,11,18,11,3,4,14,12,4,12,0,4,0,8,11,9,5,11,5,19,11,19,7,19,5,14,19,14,4,19,4,17,1,12,14,1,14,5,1,5,9];super(r,a,e,t),this.type="DodecahedronGeometry",this.parameters={radius:e,detail:t}}static fromJSON(e){return new i(e.radius,e.detail)}};var wn=class{constructor(){this.type="Curve",this.arcLengthDivisions=200,this.needsUpdate=!1,this.cacheArcLengths=null}getPoint(){Je("Curve: .getPoint() not implemented.")}getPointAt(e,t){let n=this.getUtoTmapping(e);return this.getPoint(n,t)}getPoints(e=5){let t=[];for(let n=0;n<=e;n++)t.push(this.getPoint(n/e));return t}getSpacedPoints(e=5){let t=[];for(let n=0;n<=e;n++)t.push(this.getPointAt(n/e));return t}getLength(){let e=this.getLengths();return e[e.length-1]}getLengths(e=this.arcLengthDivisions){if(this.cacheArcLengths&&this.cacheArcLengths.length===e+1&&!this.needsUpdate)return this.cacheArcLengths;this.needsUpdate=!1;let t=[],n,s=this.getPoint(0),r=0;t.push(0);for(let a=1;a<=e;a++)n=this.getPoint(a/e),r+=n.distanceTo(s),t.push(r),s=n;return this.cacheArcLengths=t,t}updateArcLengths(){this.needsUpdate=!0,this.getLengths()}getUtoTmapping(e,t=null){let n=this.getLengths(),s=0,r=n.length,a;t?a=t:a=e*n[r-1];let o=0,l=r-1,c;for(;o<=l;)if(s=Math.floor(o+(l-o)/2),c=n[s]-a,c<0)o=s+1;else if(c>0)l=s-1;else{l=s;break}if(s=l,n[s]===a)return s/(r-1);let h=n[s],u=n[s+1]-h,d=(a-h)/u;return(s+d)/(r-1)}getTangent(e,t){let s=e-1e-4,r=e+1e-4;s<0&&(s=0),r>1&&(r=1);let a=this.getPoint(s),o=this.getPoint(r),l=t||(a.isVector2?new Ue:new D);return l.copy(o).sub(a).normalize(),l}getTangentAt(e,t){let n=this.getUtoTmapping(e);return this.getTangent(n,t)}computeFrenetFrames(e,t=!1){let n=new D,s=[],r=[],a=[],o=new D,l=new pt;for(let d=0;d<=e;d++){let g=d/e;s[d]=this.getTangentAt(g,new D)}r[0]=new D,a[0]=new D;let c=Number.MAX_VALUE,h=Math.abs(s[0].x),f=Math.abs(s[0].y),u=Math.abs(s[0].z);h<=c&&(c=h,n.set(1,0,0)),f<=c&&(c=f,n.set(0,1,0)),u<=c&&n.set(0,0,1),o.crossVectors(s[0],n).normalize(),r[0].crossVectors(s[0],o),a[0].crossVectors(s[0],r[0]);for(let d=1;d<=e;d++){if(r[d]=r[d-1].clone(),a[d]=a[d-1].clone(),o.crossVectors(s[d-1],s[d]),o.length()>Number.EPSILON){o.normalize();let g=Math.acos(ft(s[d-1].dot(s[d]),-1,1));r[d].applyMatrix4(l.makeRotationAxis(o,g))}a[d].crossVectors(s[d],r[d])}if(t===!0){let d=Math.acos(ft(r[0].dot(r[e]),-1,1));d/=e,s[0].dot(o.crossVectors(r[0],r[e]))>0&&(d=-d);for(let g=1;g<=e;g++)r[g].applyMatrix4(l.makeRotationAxis(s[g],d*g)),a[g].crossVectors(s[g],r[g])}return{tangents:s,normals:r,binormals:a}}clone(){return new this.constructor().copy(this)}copy(e){return this.arcLengthDivisions=e.arcLengthDivisions,this}toJSON(){let e={metadata:{version:4.7,type:"Curve",generator:"Curve.toJSON"}};return e.arcLengthDivisions=this.arcLengthDivisions,e.type=this.type,e}fromJSON(e){return this.arcLengthDivisions=e.arcLengthDivisions,this}},xr=class extends wn{constructor(e=0,t=0,n=1,s=1,r=0,a=Math.PI*2,o=!1,l=0){super(),this.isEllipseCurve=!0,this.type="EllipseCurve",this.aX=e,this.aY=t,this.xRadius=n,this.yRadius=s,this.aStartAngle=r,this.aEndAngle=a,this.aClockwise=o,this.aRotation=l}getPoint(e,t=new Ue){let n=t,s=Math.PI*2,r=this.aEndAngle-this.aStartAngle,a=Math.abs(r)<Number.EPSILON;for(;r<0;)r+=s;for(;r>s;)r-=s;r<Number.EPSILON&&(a?r=0:r=s),this.aClockwise===!0&&!a&&(r===s?r=-s:r=r-s);let o=this.aStartAngle+e*r,l=this.aX+this.xRadius*Math.cos(o),c=this.aY+this.yRadius*Math.sin(o);if(this.aRotation!==0){let h=Math.cos(this.aRotation),f=Math.sin(this.aRotation),u=l-this.aX,d=c-this.aY;l=u*h-d*f+this.aX,c=u*f+d*h+this.aY}return n.set(l,c)}copy(e){return super.copy(e),this.aX=e.aX,this.aY=e.aY,this.xRadius=e.xRadius,this.yRadius=e.yRadius,this.aStartAngle=e.aStartAngle,this.aEndAngle=e.aEndAngle,this.aClockwise=e.aClockwise,this.aRotation=e.aRotation,this}toJSON(){let e=super.toJSON();return e.aX=this.aX,e.aY=this.aY,e.xRadius=this.xRadius,e.yRadius=this.yRadius,e.aStartAngle=this.aStartAngle,e.aEndAngle=this.aEndAngle,e.aClockwise=this.aClockwise,e.aRotation=this.aRotation,e}fromJSON(e){return super.fromJSON(e),this.aX=e.aX,this.aY=e.aY,this.xRadius=e.xRadius,this.yRadius=e.yRadius,this.aStartAngle=e.aStartAngle,this.aEndAngle=e.aEndAngle,this.aClockwise=e.aClockwise,this.aRotation=e.aRotation,this}},Ha=class extends xr{constructor(e,t,n,s,r,a){super(e,t,n,n,s,r,a),this.isArcCurve=!0,this.type="ArcCurve"}};function dc(){let i=0,e=0,t=0,n=0;function s(r,a,o,l){i=r,e=o,t=-3*r+3*a-2*o-l,n=2*r-2*a+o+l}return{initCatmullRom:function(r,a,o,l,c){s(a,o,c*(o-r),c*(l-a))},initNonuniformCatmullRom:function(r,a,o,l,c,h,f){let u=(a-r)/c-(o-r)/(c+h)+(o-a)/h,d=(o-a)/h-(l-a)/(h+f)+(l-o)/f;u*=h,d*=h,s(a,o,u,d)},calc:function(r){let a=r*r,o=a*r;return i+e*r+t*a+n*o}}}var ru=new D,au=new D,Ul=new dc,Fl=new dc,kl=new dc,ws=class extends wn{constructor(e=[],t=!1,n="centripetal",s=.5){super(),this.isCatmullRomCurve3=!0,this.type="CatmullRomCurve3",this.points=e,this.closed=t,this.curveType=n,this.tension=s}getPoint(e,t=new D){let n=t,s=this.points,r=s.length,a=(r-(this.closed?0:1))*e,o=Math.floor(a),l=a-o;this.closed?o+=o>0?0:(Math.floor(Math.abs(o)/r)+1)*r:l===0&&o===r-1&&(o=r-2,l=1);let c,h;this.closed||o>0?c=s[(o-1)%r]:(au.subVectors(s[0],s[1]).add(s[0]),c=au);let f=s[o%r],u=s[(o+1)%r];if(this.closed||o+2<r?h=s[(o+2)%r]:(ru.subVectors(s[r-1],s[r-2]).add(s[r-1]),h=ru),this.curveType==="centripetal"||this.curveType==="chordal"){let d=this.curveType==="chordal"?.5:.25,g=Math.pow(c.distanceToSquared(f),d),M=Math.pow(f.distanceToSquared(u),d),m=Math.pow(u.distanceToSquared(h),d);M<1e-4&&(M=1),g<1e-4&&(g=M),m<1e-4&&(m=M),Ul.initNonuniformCatmullRom(c.x,f.x,u.x,h.x,g,M,m),Fl.initNonuniformCatmullRom(c.y,f.y,u.y,h.y,g,M,m),kl.initNonuniformCatmullRom(c.z,f.z,u.z,h.z,g,M,m)}else this.curveType==="catmullrom"&&(Ul.initCatmullRom(c.x,f.x,u.x,h.x,this.tension),Fl.initCatmullRom(c.y,f.y,u.y,h.y,this.tension),kl.initCatmullRom(c.z,f.z,u.z,h.z,this.tension));return n.set(Ul.calc(l),Fl.calc(l),kl.calc(l)),n}copy(e){super.copy(e),this.points=[];for(let t=0,n=e.points.length;t<n;t++){let s=e.points[t];this.points.push(s.clone())}return this.closed=e.closed,this.curveType=e.curveType,this.tension=e.tension,this}toJSON(){let e=super.toJSON();e.points=[];for(let t=0,n=this.points.length;t<n;t++){let s=this.points[t];e.points.push(s.toArray())}return e.closed=this.closed,e.curveType=this.curveType,e.tension=this.tension,e}fromJSON(e){super.fromJSON(e),this.points=[];for(let t=0,n=e.points.length;t<n;t++){let s=e.points[t];this.points.push(new D().fromArray(s))}return this.closed=e.closed,this.curveType=e.curveType,this.tension=e.tension,this}};function ou(i,e,t,n,s){let r=(n-e)*.5,a=(s-t)*.5,o=i*i,l=i*o;return(2*t-2*n+r+a)*l+(-3*t+3*n-2*r-a)*o+r*i+t}function Id(i,e){let t=1-i;return t*t*e}function Ld(i,e){return 2*(1-i)*i*e}function Nd(i,e){return i*i*e}function er(i,e,t,n){return Id(i,e)+Ld(i,t)+Nd(i,n)}function Dd(i,e){let t=1-i;return t*t*t*e}function Ud(i,e){let t=1-i;return 3*t*t*i*e}function Fd(i,e){return 3*(1-i)*i*i*e}function kd(i,e){return i*i*i*e}function tr(i,e,t,n,s){return Dd(i,e)+Ud(i,t)+Fd(i,n)+kd(i,s)}var Ga=class extends wn{constructor(e=new Ue,t=new Ue,n=new Ue,s=new Ue){super(),this.isCubicBezierCurve=!0,this.type="CubicBezierCurve",this.v0=e,this.v1=t,this.v2=n,this.v3=s}getPoint(e,t=new Ue){let n=t,s=this.v0,r=this.v1,a=this.v2,o=this.v3;return n.set(tr(e,s.x,r.x,a.x,o.x),tr(e,s.y,r.y,a.y,o.y)),n}copy(e){return super.copy(e),this.v0.copy(e.v0),this.v1.copy(e.v1),this.v2.copy(e.v2),this.v3.copy(e.v3),this}toJSON(){let e=super.toJSON();return e.v0=this.v0.toArray(),e.v1=this.v1.toArray(),e.v2=this.v2.toArray(),e.v3=this.v3.toArray(),e}fromJSON(e){return super.fromJSON(e),this.v0.fromArray(e.v0),this.v1.fromArray(e.v1),this.v2.fromArray(e.v2),this.v3.fromArray(e.v3),this}},Wa=class extends wn{constructor(e=new D,t=new D,n=new D,s=new D){super(),this.isCubicBezierCurve3=!0,this.type="CubicBezierCurve3",this.v0=e,this.v1=t,this.v2=n,this.v3=s}getPoint(e,t=new D){let n=t,s=this.v0,r=this.v1,a=this.v2,o=this.v3;return n.set(tr(e,s.x,r.x,a.x,o.x),tr(e,s.y,r.y,a.y,o.y),tr(e,s.z,r.z,a.z,o.z)),n}copy(e){return super.copy(e),this.v0.copy(e.v0),this.v1.copy(e.v1),this.v2.copy(e.v2),this.v3.copy(e.v3),this}toJSON(){let e=super.toJSON();return e.v0=this.v0.toArray(),e.v1=this.v1.toArray(),e.v2=this.v2.toArray(),e.v3=this.v3.toArray(),e}fromJSON(e){return super.fromJSON(e),this.v0.fromArray(e.v0),this.v1.fromArray(e.v1),this.v2.fromArray(e.v2),this.v3.fromArray(e.v3),this}},qa=class extends wn{constructor(e=new Ue,t=new Ue){super(),this.isLineCurve=!0,this.type="LineCurve",this.v1=e,this.v2=t}getPoint(e,t=new Ue){let n=t;return e===1?n.copy(this.v2):(n.copy(this.v2).sub(this.v1),n.multiplyScalar(e).add(this.v1)),n}getPointAt(e,t){return this.getPoint(e,t)}getTangent(e,t=new Ue){return t.subVectors(this.v2,this.v1).normalize()}getTangentAt(e,t){return this.getTangent(e,t)}copy(e){return super.copy(e),this.v1.copy(e.v1),this.v2.copy(e.v2),this}toJSON(){let e=super.toJSON();return e.v1=this.v1.toArray(),e.v2=this.v2.toArray(),e}fromJSON(e){return super.fromJSON(e),this.v1.fromArray(e.v1),this.v2.fromArray(e.v2),this}},Xa=class extends wn{constructor(e=new D,t=new D){super(),this.isLineCurve3=!0,this.type="LineCurve3",this.v1=e,this.v2=t}getPoint(e,t=new D){let n=t;return e===1?n.copy(this.v2):(n.copy(this.v2).sub(this.v1),n.multiplyScalar(e).add(this.v1)),n}getPointAt(e,t){return this.getPoint(e,t)}getTangent(e,t=new D){return t.subVectors(this.v2,this.v1).normalize()}getTangentAt(e,t){return this.getTangent(e,t)}copy(e){return super.copy(e),this.v1.copy(e.v1),this.v2.copy(e.v2),this}toJSON(){let e=super.toJSON();return e.v1=this.v1.toArray(),e.v2=this.v2.toArray(),e}fromJSON(e){return super.fromJSON(e),this.v1.fromArray(e.v1),this.v2.fromArray(e.v2),this}},$a=class extends wn{constructor(e=new Ue,t=new Ue,n=new Ue){super(),this.isQuadraticBezierCurve=!0,this.type="QuadraticBezierCurve",this.v0=e,this.v1=t,this.v2=n}getPoint(e,t=new Ue){let n=t,s=this.v0,r=this.v1,a=this.v2;return n.set(er(e,s.x,r.x,a.x),er(e,s.y,r.y,a.y)),n}copy(e){return super.copy(e),this.v0.copy(e.v0),this.v1.copy(e.v1),this.v2.copy(e.v2),this}toJSON(){let e=super.toJSON();return e.v0=this.v0.toArray(),e.v1=this.v1.toArray(),e.v2=this.v2.toArray(),e}fromJSON(e){return super.fromJSON(e),this.v0.fromArray(e.v0),this.v1.fromArray(e.v1),this.v2.fromArray(e.v2),this}},Hi=class extends wn{constructor(e=new D,t=new D,n=new D){super(),this.isQuadraticBezierCurve3=!0,this.type="QuadraticBezierCurve3",this.v0=e,this.v1=t,this.v2=n}getPoint(e,t=new D){let n=t,s=this.v0,r=this.v1,a=this.v2;return n.set(er(e,s.x,r.x,a.x),er(e,s.y,r.y,a.y),er(e,s.z,r.z,a.z)),n}copy(e){return super.copy(e),this.v0.copy(e.v0),this.v1.copy(e.v1),this.v2.copy(e.v2),this}toJSON(){let e=super.toJSON();return e.v0=this.v0.toArray(),e.v1=this.v1.toArray(),e.v2=this.v2.toArray(),e}fromJSON(e){return super.fromJSON(e),this.v0.fromArray(e.v0),this.v1.fromArray(e.v1),this.v2.fromArray(e.v2),this}},Ya=class extends wn{constructor(e=[]){super(),this.isSplineCurve=!0,this.type="SplineCurve",this.points=e}getPoint(e,t=new Ue){let n=t,s=this.points,r=(s.length-1)*e,a=Math.floor(r),o=r-a,l=s[a===0?a:a-1],c=s[a],h=s[a>s.length-2?s.length-1:a+1],f=s[a>s.length-3?s.length-1:a+2];return n.set(ou(o,l.x,c.x,h.x,f.x),ou(o,l.y,c.y,h.y,f.y)),n}copy(e){super.copy(e),this.points=[];for(let t=0,n=e.points.length;t<n;t++){let s=e.points[t];this.points.push(s.clone())}return this}toJSON(){let e=super.toJSON();e.points=[];for(let t=0,n=this.points.length;t<n;t++){let s=this.points[t];e.points.push(s.toArray())}return e}fromJSON(e){super.fromJSON(e),this.points=[];for(let t=0,n=e.points.length;t<n;t++){let s=e.points[t];this.points.push(new Ue().fromArray(s))}return this}},Od=Object.freeze({__proto__:null,ArcCurve:Ha,CatmullRomCurve3:ws,CubicBezierCurve:Ga,CubicBezierCurve3:Wa,EllipseCurve:xr,LineCurve:qa,LineCurve3:Xa,QuadraticBezierCurve:$a,QuadraticBezierCurve3:Hi,SplineCurve:Ya});var As=class i extends Es{constructor(e=1,t=0){let n=(1+Math.sqrt(5))/2,s=[-1,n,0,1,n,0,-1,-n,0,1,-n,0,0,-1,n,0,1,n,0,-1,-n,0,1,-n,n,0,-1,n,0,1,-n,0,-1,-n,0,1],r=[0,11,5,0,5,1,0,1,7,0,7,10,0,10,11,1,5,9,5,11,4,11,10,2,10,7,6,7,1,8,3,9,4,3,4,2,3,2,6,3,6,8,3,8,9,4,9,5,2,4,11,6,2,10,8,6,7,9,8,1];super(s,r,e,t),this.type="IcosahedronGeometry",this.parameters={radius:e,detail:t}}static fromJSON(e){return new i(e.radius,e.detail)}};var vr=class i extends Es{constructor(e=1,t=0){let n=[1,0,0,-1,0,0,0,1,0,0,-1,0,0,0,1,0,0,-1],s=[0,2,4,0,4,3,0,3,5,0,5,2,1,2,5,1,5,3,1,3,4,1,4,2];super(n,s,e,t),this.type="OctahedronGeometry",this.parameters={radius:e,detail:t}}static fromJSON(e){return new i(e.radius,e.detail)}},yr=class i extends Rt{constructor(e=1,t=1,n=1,s=1){super(),this.type="PlaneGeometry",this.parameters={width:e,height:t,widthSegments:n,heightSegments:s};let r=e/2,a=t/2,o=Math.floor(n),l=Math.floor(s),c=o+1,h=l+1,f=e/o,u=t/l,d=[],g=[],M=[],m=[];for(let p=0;p<h;p++){let T=p*u-a;for(let C=0;C<c;C++){let v=C*f-r;g.push(v,-T,0),M.push(0,0,1),m.push(C/o),m.push(1-p/l)}}for(let p=0;p<l;p++)for(let T=0;T<o;T++){let C=T+c*p,v=T+c*(p+1),w=T+1+c*(p+1),S=T+1+c*p;d.push(C,v,S),d.push(v,w,S)}this.setIndex(d),this.setAttribute("position",new vt(g,3)),this.setAttribute("normal",new vt(M,3)),this.setAttribute("uv",new vt(m,2))}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}static fromJSON(e){return new i(e.width,e.height,e.widthSegments,e.heightSegments)}};var _n=class i extends Rt{constructor(e=1,t=32,n=16,s=0,r=Math.PI*2,a=0,o=Math.PI){super(),this.type="SphereGeometry",this.parameters={radius:e,widthSegments:t,heightSegments:n,phiStart:s,phiLength:r,thetaStart:a,thetaLength:o},t=Math.max(3,Math.floor(t)),n=Math.max(2,Math.floor(n));let l=Math.min(a+o,Math.PI),c=0,h=[],f=new D,u=new D,d=[],g=[],M=[],m=[];for(let p=0;p<=n;p++){let T=[],C=p/n,v=a+C*o,w=e*Math.cos(v),S=Math.sqrt(e*e-w*w),I=0;p===0&&a===0?I=.5/t:p===n&&l===Math.PI&&(I=-.5/t);for(let x=0;x<=t;x++){let A=x/t,N=s+A*r;f.x=-S*Math.cos(N),f.y=w,f.z=S*Math.sin(N),g.push(f.x,f.y,f.z),u.copy(f).normalize(),M.push(u.x,u.y,u.z),m.push(A+I,1-C),T.push(c++)}h.push(T)}for(let p=0;p<n;p++)for(let T=0;T<t;T++){let C=h[p][T+1],v=h[p][T],w=h[p+1][T],S=h[p+1][T+1];(p!==0||a>0)&&d.push(C,v,S),(p!==n-1||l<Math.PI)&&d.push(v,w,S)}this.setIndex(d),this.setAttribute("position",new vt(g,3)),this.setAttribute("normal",new vt(M,3)),this.setAttribute("uv",new vt(m,2))}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}static fromJSON(e){return new i(e.radius,e.widthSegments,e.heightSegments,e.phiStart,e.phiLength,e.thetaStart,e.thetaLength)}};var An=class i extends Rt{constructor(e=1,t=.4,n=12,s=48,r=Math.PI*2,a=0,o=Math.PI*2){super(),this.type="TorusGeometry",this.parameters={radius:e,tube:t,radialSegments:n,tubularSegments:s,arc:r,thetaStart:a,thetaLength:o},n=Math.floor(n),s=Math.floor(s);let l=[],c=[],h=[],f=[],u=new D,d=new D,g=new D;for(let M=0;M<=n;M++){let m=a+M/n*o;for(let p=0;p<=s;p++){let T=p/s*r;d.x=(e+t*Math.cos(m))*Math.cos(T),d.y=(e+t*Math.cos(m))*Math.sin(T),d.z=t*Math.sin(m),c.push(d.x,d.y,d.z),u.x=e*Math.cos(T),u.y=e*Math.sin(T),g.subVectors(d,u).normalize(),h.push(g.x,g.y,g.z),f.push(p/s),f.push(M/n)}}for(let M=1;M<=n;M++)for(let m=1;m<=s;m++){let p=(s+1)*M+m-1,T=(s+1)*(M-1)+m-1,C=(s+1)*(M-1)+m,v=(s+1)*M+m;l.push(p,T,v),l.push(T,C,v)}this.setIndex(l),this.setAttribute("position",new vt(c,3)),this.setAttribute("normal",new vt(h,3)),this.setAttribute("uv",new vt(f,2))}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}static fromJSON(e){return new i(e.radius,e.tube,e.radialSegments,e.tubularSegments,e.arc,e.thetaStart,e.thetaLength)}};var Mr=class i extends Rt{constructor(e=new Hi(new D(-1,-1,0),new D(-1,1,0),new D(1,1,0)),t=64,n=1,s=8,r=!1){super(),this.type="TubeGeometry",this.parameters={path:e,tubularSegments:t,radius:n,radialSegments:s,closed:r};let a=e.computeFrenetFrames(t,r);this.tangents=a.tangents,this.normals=a.normals,this.binormals=a.binormals;let o=new D,l=new D,c=new Ue,h=new D,f=[],u=[],d=[],g=[];M(),this.setIndex(g),this.setAttribute("position",new vt(f,3)),this.setAttribute("normal",new vt(u,3)),this.setAttribute("uv",new vt(d,2));function M(){for(let C=0;C<t;C++)m(C);m(r===!1?t:0),T(),p()}function m(C){h=e.getPointAt(C/t,h);let v=a.normals[C],w=a.binormals[C];for(let S=0;S<=s;S++){let I=S/s*Math.PI*2,x=Math.sin(I),A=-Math.cos(I);l.x=A*v.x+x*w.x,l.y=A*v.y+x*w.y,l.z=A*v.z+x*w.z,l.normalize(),u.push(l.x,l.y,l.z),o.x=h.x+n*l.x,o.y=h.y+n*l.y,o.z=h.z+n*l.z,f.push(o.x,o.y,o.z)}}function p(){for(let C=1;C<=t;C++)for(let v=1;v<=s;v++){let w=(s+1)*(C-1)+(v-1),S=(s+1)*C+(v-1),I=(s+1)*C+v,x=(s+1)*(C-1)+v;g.push(w,S,x),g.push(S,I,x)}}function T(){for(let C=0;C<=t;C++)for(let v=0;v<=s;v++)c.x=C/t,c.y=v/s,d.push(c.x,c.y)}}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}toJSON(){let e=super.toJSON();return e.path=this.parameters.path.toJSON(),e}static fromJSON(e){return new i(new Od[e.path.type]().fromJSON(e.path),e.tubularSegments,e.radius,e.radialSegments,e.closed)}};function Yi(i){let e={};for(let t in i){e[t]={};for(let n in i[t]){let s=i[t][n];if(lu(s))s.isRenderTargetTexture?(Je("UniformsUtils: Textures of render targets cannot be cloned via cloneUniforms() or mergeUniforms()."),e[t][n]=null):e[t][n]=s.clone();else if(Array.isArray(s))if(lu(s[0])){let r=[];for(let a=0,o=s.length;a<o;a++)r[a]=s[a].clone();e[t][n]=r}else e[t][n]=s.slice();else e[t][n]=s}}return e}function an(i){let e={};for(let t=0;t<i.length;t++){let n=Yi(i[t]);for(let s in n)e[s]=n[s]}return e}function lu(i){return i&&(i.isColor||i.isMatrix3||i.isMatrix4||i.isVector2||i.isVector3||i.isVector4||i.isTexture||i.isQuaternion)}function Bd(i){let e=[];for(let t=0;t<i.length;t++)e.push(i[t].clone());return e}function fc(i){let e=i.getRenderTarget();return e===null?i.outputColorSpace:e.isXRRenderTarget===!0?e.texture.colorSpace:dt.workingColorSpace}var li={clone:Yi,merge:an},zd=`void main() {
	gl_Position = projectionMatrix * modelViewMatrix * vec4( position, 1.0 );
}`,Vd=`void main() {
	gl_FragColor = vec4( 1.0, 0.0, 0.0, 1.0 );
}`,Ot=class extends Fn{constructor(e){super(),this.isShaderMaterial=!0,this.type="ShaderMaterial",this.defines={},this.uniforms={},this.uniformsGroups=[],this.vertexShader=zd,this.fragmentShader=Vd,this.linewidth=1,this.wireframe=!1,this.wireframeLinewidth=1,this.fog=!1,this.lights=!1,this.clipping=!1,this.forceSinglePass=!0,this.extensions={clipCullDistance:!1,multiDraw:!1},this.defaultAttributeValues={color:[1,1,1],uv:[0,0],uv1:[0,0]},this.index0AttributeName=void 0,this.uniformsNeedUpdate=!1,this.glslVersion=null,e!==void 0&&this.setValues(e)}copy(e){return super.copy(e),this.fragmentShader=e.fragmentShader,this.vertexShader=e.vertexShader,this.uniforms=Yi(e.uniforms),this.uniformsGroups=Bd(e.uniformsGroups),this.defines=Object.assign({},e.defines),this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this.fog=e.fog,this.lights=e.lights,this.clipping=e.clipping,this.extensions=Object.assign({},e.extensions),this.glslVersion=e.glslVersion,this.defaultAttributeValues=Object.assign({},e.defaultAttributeValues),this.index0AttributeName=e.index0AttributeName,this.uniformsNeedUpdate=e.uniformsNeedUpdate,this}toJSON(e){let t=super.toJSON(e);t.glslVersion=this.glslVersion,t.uniforms={};for(let s in this.uniforms){let a=this.uniforms[s].value;a&&a.isTexture?t.uniforms[s]={type:"t",value:a.toJSON(e).uuid}:a&&a.isColor?t.uniforms[s]={type:"c",value:a.getHex()}:a&&a.isVector2?t.uniforms[s]={type:"v2",value:a.toArray()}:a&&a.isVector3?t.uniforms[s]={type:"v3",value:a.toArray()}:a&&a.isVector4?t.uniforms[s]={type:"v4",value:a.toArray()}:a&&a.isMatrix3?t.uniforms[s]={type:"m3",value:a.toArray()}:a&&a.isMatrix4?t.uniforms[s]={type:"m4",value:a.toArray()}:t.uniforms[s]={value:a}}Object.keys(this.defines).length>0&&(t.defines=this.defines),t.vertexShader=this.vertexShader,t.fragmentShader=this.fragmentShader,t.lights=this.lights,t.clipping=this.clipping;let n={};for(let s in this.extensions)this.extensions[s]===!0&&(n[s]=!0);return Object.keys(n).length>0&&(t.extensions=n),t}fromJSON(e,t){if(super.fromJSON(e,t),e.uniforms!==void 0)for(let n in e.uniforms){let s=e.uniforms[n];switch(this.uniforms[n]={},s.type){case"t":this.uniforms[n].value=t[s.value]||null;break;case"c":this.uniforms[n].value=new Ke().setHex(s.value);break;case"v2":this.uniforms[n].value=new Ue().fromArray(s.value);break;case"v3":this.uniforms[n].value=new D().fromArray(s.value);break;case"v4":this.uniforms[n].value=new Dt().fromArray(s.value);break;case"m3":this.uniforms[n].value=new nt().fromArray(s.value);break;case"m4":this.uniforms[n].value=new pt().fromArray(s.value);break;default:this.uniforms[n].value=s.value}}if(e.defines!==void 0&&(this.defines=e.defines),e.vertexShader!==void 0&&(this.vertexShader=e.vertexShader),e.fragmentShader!==void 0&&(this.fragmentShader=e.fragmentShader),e.glslVersion!==void 0&&(this.glslVersion=e.glslVersion),e.extensions!==void 0)for(let n in e.extensions)this.extensions[n]=e.extensions[n];return e.lights!==void 0&&(this.lights=e.lights),e.clipping!==void 0&&(this.clipping=e.clipping),this}},Cs=class extends Ot{constructor(e){super(e),this.isRawShaderMaterial=!0,this.type="RawShaderMaterial"}},jt=class extends Fn{constructor(e){super(),this.isMeshStandardMaterial=!0,this.type="MeshStandardMaterial",this.defines={STANDARD:""},this.color=new Ke(16777215),this.roughness=1,this.metalness=0,this.map=null,this.lightMap=null,this.lightMapIntensity=1,this.aoMap=null,this.aoMapIntensity=1,this.emissive=new Ke(0),this.emissiveIntensity=1,this.emissiveMap=null,this.bumpMap=null,this.bumpScale=1,this.normalMap=null,this.normalMapType=Wr,this.normalScale=new Ue(1,1),this.displacementMap=null,this.displacementScale=1,this.displacementBias=0,this.roughnessMap=null,this.metalnessMap=null,this.alphaMap=null,this.envMap=null,this.envMapRotation=new En,this.envMapIntensity=1,this.wireframe=!1,this.wireframeLinewidth=1,this.wireframeLinecap="round",this.wireframeLinejoin="round",this.flatShading=!1,this.fog=!0,this.setValues(e)}copy(e){return super.copy(e),this.defines={STANDARD:""},this.color.copy(e.color),this.roughness=e.roughness,this.metalness=e.metalness,this.map=e.map,this.lightMap=e.lightMap,this.lightMapIntensity=e.lightMapIntensity,this.aoMap=e.aoMap,this.aoMapIntensity=e.aoMapIntensity,this.emissive.copy(e.emissive),this.emissiveMap=e.emissiveMap,this.emissiveIntensity=e.emissiveIntensity,this.bumpMap=e.bumpMap,this.bumpScale=e.bumpScale,this.normalMap=e.normalMap,this.normalMapType=e.normalMapType,this.normalScale.copy(e.normalScale),this.displacementMap=e.displacementMap,this.displacementScale=e.displacementScale,this.displacementBias=e.displacementBias,this.roughnessMap=e.roughnessMap,this.metalnessMap=e.metalnessMap,this.alphaMap=e.alphaMap,this.envMap=e.envMap,this.envMapRotation.copy(e.envMapRotation),this.envMapIntensity=e.envMapIntensity,this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this.wireframeLinecap=e.wireframeLinecap,this.wireframeLinejoin=e.wireframeLinejoin,this.flatShading=e.flatShading,this.fog=e.fog,this}};var br=class extends Fn{constructor(e){super(),this.isMeshLambertMaterial=!0,this.type="MeshLambertMaterial",this.color=new Ke(16777215),this.map=null,this.lightMap=null,this.lightMapIntensity=1,this.aoMap=null,this.aoMapIntensity=1,this.emissive=new Ke(0),this.emissiveIntensity=1,this.emissiveMap=null,this.bumpMap=null,this.bumpScale=1,this.normalMap=null,this.normalMapType=Wr,this.normalScale=new Ue(1,1),this.displacementMap=null,this.displacementScale=1,this.displacementBias=0,this.specularMap=null,this.alphaMap=null,this.envMap=null,this.envMapRotation=new En,this.combine=co,this.reflectivity=1,this.envMapIntensity=1,this.refractionRatio=.98,this.wireframe=!1,this.wireframeLinewidth=1,this.wireframeLinecap="round",this.wireframeLinejoin="round",this.flatShading=!1,this.fog=!0,this.setValues(e)}copy(e){return super.copy(e),this.color.copy(e.color),this.map=e.map,this.lightMap=e.lightMap,this.lightMapIntensity=e.lightMapIntensity,this.aoMap=e.aoMap,this.aoMapIntensity=e.aoMapIntensity,this.emissive.copy(e.emissive),this.emissiveMap=e.emissiveMap,this.emissiveIntensity=e.emissiveIntensity,this.bumpMap=e.bumpMap,this.bumpScale=e.bumpScale,this.normalMap=e.normalMap,this.normalMapType=e.normalMapType,this.normalScale.copy(e.normalScale),this.displacementMap=e.displacementMap,this.displacementScale=e.displacementScale,this.displacementBias=e.displacementBias,this.specularMap=e.specularMap,this.alphaMap=e.alphaMap,this.envMap=e.envMap,this.envMapRotation.copy(e.envMapRotation),this.combine=e.combine,this.reflectivity=e.reflectivity,this.envMapIntensity=e.envMapIntensity,this.refractionRatio=e.refractionRatio,this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this.wireframeLinecap=e.wireframeLinecap,this.wireframeLinejoin=e.wireframeLinejoin,this.flatShading=e.flatShading,this.fog=e.fog,this}},Za=class extends Fn{constructor(e){super(),this.isMeshDepthMaterial=!0,this.type="MeshDepthMaterial",this.depthPacking=zu,this.map=null,this.alphaMap=null,this.displacementMap=null,this.displacementScale=1,this.displacementBias=0,this.wireframe=!1,this.wireframeLinewidth=1,this.setValues(e)}copy(e){return super.copy(e),this.depthPacking=e.depthPacking,this.map=e.map,this.alphaMap=e.alphaMap,this.displacementMap=e.displacementMap,this.displacementScale=e.displacementScale,this.displacementBias=e.displacementBias,this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this}},ja=class extends Fn{constructor(e){super(),this.isMeshDistanceMaterial=!0,this.type="MeshDistanceMaterial",this.map=null,this.alphaMap=null,this.displacementMap=null,this.displacementScale=1,this.displacementBias=0,this.setValues(e)}copy(e){return super.copy(e),this.map=e.map,this.alphaMap=e.alphaMap,this.displacementMap=e.displacementMap,this.displacementScale=e.displacementScale,this.displacementBias=e.displacementBias,this}};function hs(i,e){return!i||i.constructor===e?i:typeof e.BYTES_PER_ELEMENT=="number"?new e(i):Array.prototype.slice.call(i)}function Ol(i){return i!==void 0&&i.inTangents!==void 0&&i.outTangents!==void 0}var yi=class{constructor(e,t,n,s){this.parameterPositions=e,this._cachedIndex=0,this.resultBuffer=s!==void 0?s:new t.constructor(n),this.sampleValues=t,this.valueSize=n,this.settings=null,this.DefaultSettings_={}}evaluate(e){let t=this.parameterPositions,n=this._cachedIndex,s=t[n],r=t[n-1];n:{e:{let a;t:{i:if(!(e<s)){for(let o=n+2;;){if(s===void 0){if(e<r)break i;return n=t.length,this._cachedIndex=n,this.copySampleValue_(n-1)}if(n===o)break;if(r=s,s=t[++n],e<s)break e}a=t.length;break t}if(!(e>=r)){let o=t[1];e<o&&(n=2,r=o);for(let l=n-2;;){if(r===void 0)return this._cachedIndex=0,this.copySampleValue_(0);if(n===l)break;if(s=r,r=t[--n-1],e>=r)break e}a=n,n=0;break t}break n}for(;n<a;){let o=n+a>>>1;e<t[o]?a=o:n=o+1}if(s=t[n],r=t[n-1],r===void 0)return this._cachedIndex=0,this.copySampleValue_(0);if(s===void 0)return n=t.length,this._cachedIndex=n,this.copySampleValue_(n-1)}this._cachedIndex=n,this.intervalChanged_(n,r,s)}return this.interpolate_(n,r,e,s)}getSettings_(){return this.settings||this.DefaultSettings_}copySampleValue_(e){let t=this.resultBuffer,n=this.sampleValues,s=this.valueSize,r=e*s;for(let a=0;a!==s;++a)t[a]=n[r+a];return t}interpolate_(){throw new Error("THREE.Interpolant: Call to abstract method.")}intervalChanged_(){}},Ja=class extends yi{constructor(e,t,n,s){super(e,t,n,s),this._weightPrev=-0,this._offsetPrev=-0,this._weightNext=-0,this._offsetNext=-0,this.DefaultSettings_={endingStart:Vl,endingEnd:Vl}}intervalChanged_(e,t,n){let s=this.parameterPositions,r=e-2,a=e+1,o=s[r],l=s[a];if(o===void 0)switch(this.getSettings_().endingStart){case Hl:r=e,o=2*t-n;break;case Gl:r=s.length-2,o=t+s[r]-s[r+1];break;default:r=e,o=n}if(l===void 0)switch(this.getSettings_().endingEnd){case Hl:a=e,l=2*n-t;break;case Gl:a=1,l=n+s[1]-s[0];break;default:a=e-1,l=t}let c=(n-t)*.5,h=this.valueSize;this._weightPrev=c/(t-o),this._weightNext=c/(l-n),this._offsetPrev=r*h,this._offsetNext=a*h}interpolate_(e,t,n,s){let r=this.resultBuffer,a=this.sampleValues,o=this.valueSize,l=e*o,c=l-o,h=this._offsetPrev,f=this._offsetNext,u=this._weightPrev,d=this._weightNext,g=(n-t)/(s-t),M=g*g,m=M*g,p=-u*m+2*u*M-u*g,T=(1+u)*m+(-1.5-2*u)*M+(-.5+u)*g+1,C=(-1-d)*m+(1.5+d)*M+.5*g,v=d*m-d*M;for(let w=0;w!==o;++w)r[w]=p*a[h+w]+T*a[c+w]+C*a[l+w]+v*a[f+w];return r}},Ka=class extends yi{constructor(e,t,n,s){super(e,t,n,s)}interpolate_(e,t,n,s){let r=this.resultBuffer,a=this.sampleValues,o=this.valueSize,l=e*o,c=l-o,h=(n-t)/(s-t),f=1-h;for(let u=0;u!==o;++u)r[u]=a[c+u]*f+a[l+u]*h;return r}},Qa=class extends yi{constructor(e,t,n,s){super(e,t,n,s)}interpolate_(e){return this.copySampleValue_(e-1)}},eo=class extends yi{interpolate_(e,t,n,s){let r=this.resultBuffer,a=this.sampleValues,o=this.valueSize,l=e*o,c=l-o,h=this.inTangents,f=this.outTangents;if(!h||!f){let g=(n-t)/(s-t),M=1-g;for(let m=0;m!==o;++m)r[m]=a[c+m]*M+a[l+m]*g;return r}let u=o*2,d=e-1;for(let g=0;g!==o;++g){let M=a[c+g],m=a[l+g],p=d*u+g*2,T=f[p],C=f[p+1],v=e*u+g*2,w=h[v],S=h[v+1],I=Gd(n,t,T,w,s);r[g]=th(I,M,C,S,m)}return r}};function th(i,e,t,n,s){let r=1-i;return r*r*r*e+3*r*r*i*t+3*r*i*i*n+i*i*i*s}function Hd(i,e,t,n,s){let r=1-i;return 3*r*r*(t-e)+6*r*i*(n-t)+3*i*i*(s-n)}function Gd(i,e,t,n,s){let r=(i-e)/(s-e);for(let a=0;a<8;a++){let o=th(r,e,t,n,s)-i;if(Math.abs(o)<1e-10)break;let l=Hd(r,e,t,n,s);if(Math.abs(l)<1e-10)break;r=Math.max(0,Math.min(1,r-o/l))}return r}var bn=class{constructor(e,t,n,s){if(e===void 0)throw new Error("THREE.KeyframeTrack: track name is undefined");if(t===void 0||t.length===0)throw new Error("THREE.KeyframeTrack: no keyframes in track named "+e);this.name=e,this.times=hs(t,this.TimeBufferType),this.values=hs(n,this.ValueBufferType),this.setInterpolation(s||this.DefaultInterpolation)}static toJSON(e){let t=e.constructor,n;if(t.toJSON!==this.toJSON)n=t.toJSON(e);else{n={name:e.name,times:hs(e.times,Array),values:hs(e.values,Array)};let s=e.getInterpolation();s!==e.DefaultInterpolation&&(n.interpolation=s),Ol(e.settings)&&(n.settings={inTangents:hs(e.settings.inTangents,Array),outTangents:hs(e.settings.outTangents,Array)})}return n.type=e.ValueTypeName,n}InterpolantFactoryMethodDiscrete(e){return new Qa(this.times,this.values,this.getValueSize(),e)}InterpolantFactoryMethodLinear(e){return new Ka(this.times,this.values,this.getValueSize(),e)}InterpolantFactoryMethodSmooth(e){return new Ja(this.times,this.values,this.getValueSize(),e)}InterpolantFactoryMethodBezier(e){let t=new eo(this.times,this.values,this.getValueSize(),e);return this.settings&&(t.inTangents=this.settings.inTangents,t.outTangents=this.settings.outTangents),t}setInterpolation(e){let t;switch(e){case nr:t=this.InterpolantFactoryMethodDiscrete;break;case Ua:t=this.InterpolantFactoryMethodLinear;break;case Ta:t=this.InterpolantFactoryMethodSmooth;break;case zl:t=this.InterpolantFactoryMethodBezier;break}if(t===void 0){let n="unsupported interpolation for "+this.ValueTypeName+" keyframe track named "+this.name;if(this.createInterpolant===void 0)if(e!==this.DefaultInterpolation)this.setInterpolation(this.DefaultInterpolation);else throw new Error(n);return Je("KeyframeTrack:",n),this}return this.createInterpolant=t,this}getInterpolation(){switch(this.createInterpolant){case this.InterpolantFactoryMethodDiscrete:return nr;case this.InterpolantFactoryMethodLinear:return Ua;case this.InterpolantFactoryMethodSmooth:return Ta;case this.InterpolantFactoryMethodBezier:return zl}}getValueSize(){return this.values.length/this.times.length}shift(e){if(e!==0){let t=this.times;for(let n=0,s=t.length;n!==s;++n)t[n]+=e}return this}scale(e){if(e!==1){let t=this.times;for(let n=0,s=t.length;n!==s;++n)t[n]*=e;Ol(this.settings)&&(cu(this.settings.inTangents,e),cu(this.settings.outTangents,e))}return this}trim(e,t){let n=this.times,s=n.length,r=0,a=s-1;for(;r!==s&&n[r]<e;)++r;for(;a!==-1&&n[a]>t;)--a;if(++a,r!==0||a!==s){r>=a&&(a=Math.max(a,1),r=a-1);let o=this.getValueSize();this.times=n.slice(r,a),this.values=this.values.slice(r*o,a*o)}return this}validate(){let e=!0,t=this.getValueSize();t-Math.floor(t)!==0&&(et("KeyframeTrack: Invalid value size in track.",this),e=!1);let n=this.times,s=this.values,r=n.length;r===0&&(et("KeyframeTrack: Track is empty.",this),e=!1);let a=null;for(let o=0;o!==r;o++){let l=n[o];if(typeof l=="number"&&isNaN(l)){et("KeyframeTrack: Time is not a valid number.",this,o,l),e=!1;break}if(a!==null&&a>l){et("KeyframeTrack: Out of order keys.",this,o,l,a),e=!1;break}a=l}if(s!==void 0&&Zh(s))for(let o=0,l=s.length;o!==l;++o){let c=s[o];if(isNaN(c)){et("KeyframeTrack: Value is not a valid number.",this,o,c),e=!1;break}}return e}optimize(){let e=this.times.slice(),t=this.values.slice(),n=this.getValueSize(),s=this.getInterpolation()===Ta,r=e.length-1,a=1;for(let o=1;o<r;++o){let l=!1,c=e[o],h=e[o+1];if(c!==h&&(o!==1||c!==e[0]))if(s)l=!0;else{let f=o*n,u=f-n,d=f+n;for(let g=0;g!==n;++g){let M=t[f+g];if(M!==t[u+g]||M!==t[d+g]){l=!0;break}}}if(l){if(o!==a){e[a]=e[o];let f=o*n,u=a*n;for(let d=0;d!==n;++d)t[u+d]=t[f+d]}++a}}if(r>0){e[a]=e[r];for(let o=r*n,l=a*n,c=0;c!==n;++c)t[l+c]=t[o+c];++a}return a!==e.length?(this.times=e.slice(0,a),this.values=t.slice(0,a*n)):(this.times=e,this.values=t),this}clone(){let e=this.times.slice(),t=this.values.slice(),n=this.constructor,s=new n(this.name,e,t);return s.createInterpolant=this.createInterpolant,Ol(this.settings)&&(s.settings={inTangents:this.settings.inTangents.slice(),outTangents:this.settings.outTangents.slice()}),s}};function cu(i,e){for(let t=0,n=i.length;t!==n;t+=2)i[t]*=e}bn.prototype.ValueTypeName="";bn.prototype.TimeBufferType=Float32Array;bn.prototype.ValueBufferType=Float32Array;bn.prototype.DefaultInterpolation=Ua;var Mi=class extends bn{constructor(e,t,n){super(e,t,n)}};Mi.prototype.ValueTypeName="bool";Mi.prototype.ValueBufferType=Array;Mi.prototype.DefaultInterpolation=nr;Mi.prototype.InterpolantFactoryMethodLinear=void 0;Mi.prototype.InterpolantFactoryMethodSmooth=void 0;var to=class extends bn{constructor(e,t,n,s){super(e,t,n,s)}};to.prototype.ValueTypeName="color";var no=class extends bn{constructor(e,t,n,s){super(e,t,n,s)}};no.prototype.ValueTypeName="number";var io=class extends yi{constructor(e,t,n,s){super(e,t,n,s)}interpolate_(e,t,n,s){let r=this.resultBuffer,a=this.sampleValues,o=this.valueSize,l=(n-t)/(s-t),c=e*o;for(let h=c+o;c!==h;c+=4)Gt.slerpFlat(r,0,a,c-o,a,c,l);return r}},Sr=class extends bn{constructor(e,t,n,s){super(e,t,n,s)}InterpolantFactoryMethodLinear(e){return new io(this.times,this.values,this.getValueSize(),e)}};Sr.prototype.ValueTypeName="quaternion";Sr.prototype.InterpolantFactoryMethodSmooth=void 0;var bi=class extends bn{constructor(e,t,n){super(e,t,n)}};bi.prototype.ValueTypeName="string";bi.prototype.ValueBufferType=Array;bi.prototype.DefaultInterpolation=nr;bi.prototype.InterpolantFactoryMethodLinear=void 0;bi.prototype.InterpolantFactoryMethodSmooth=void 0;var so=class extends bn{constructor(e,t,n,s){super(e,t,n,s)}};so.prototype.ValueTypeName="vector";var ro=class{constructor(e,t,n){let s=this,r=!1,a=0,o=0,l,c=[];this.onStart=void 0,this.onLoad=e,this.onProgress=t,this.onError=n,this._abortController=null,this.itemStart=function(h){o++,r===!1&&s.onStart!==void 0&&s.onStart(h,a,o),r=!0},this.itemEnd=function(h){a++,s.onProgress!==void 0&&s.onProgress(h,a,o),a===o&&(r=!1,s.onLoad!==void 0&&s.onLoad())},this.itemError=function(h){s.onError!==void 0&&s.onError(h)},this.resolveURL=function(h){return h=h.normalize("NFC"),l?l(h):h},this.setURLModifier=function(h){return l=h,this},this.addHandler=function(h,f){return c.push(h,f),this},this.removeHandler=function(h){let f=c.indexOf(h);return f!==-1&&c.splice(f,2),this},this.getHandler=function(h){for(let f=0,u=c.length;f<u;f+=2){let d=c[f],g=c[f+1];if(d.global&&(d.lastIndex=0),d.test(h))return g}return null},this.abort=function(){return this.abortController.abort(),this._abortController=null,this}}get abortController(){return this._abortController||(this._abortController=new AbortController),this._abortController}},nh=new ro,ao=class{constructor(e){this.manager=e!==void 0?e:nh,this.crossOrigin="anonymous",this.withCredentials=!1,this.path="",this.resourcePath="",this.requestHeader={},typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("observe",{detail:this}))}load(){}loadAsync(e,t){let n=this;return new Promise(function(s,r){n.load(e,s,t,r)})}parse(){}setCrossOrigin(e){return this.crossOrigin=e,this}setWithCredentials(e){return this.withCredentials=e,this}setPath(e){return this.path=e,this}setResourcePath(e){return this.resourcePath=e,this}setRequestHeader(e){return this.requestHeader=e,this}abort(){return this}};ao.DEFAULT_MATERIAL_NAME="__DEFAULT";var Rs=class extends Ht{constructor(e,t=1){super(),this.isLight=!0,this.type="Light",this.color=new Ke(e),this.intensity=t}copy(e,t){return super.copy(e,t),this.color.copy(e.color),this.intensity=e.intensity,this}toJSON(e){let t=super.toJSON(e);return t.object.color=this.color.getHex(),t.object.intensity=this.intensity,t}},Tr=class extends Rs{constructor(e,t,n){super(e,n),this.isHemisphereLight=!0,this.type="HemisphereLight",this.position.copy(Ht.DEFAULT_UP),this.updateMatrix(),this.groundColor=new Ke(t)}copy(e,t){return super.copy(e,t),this.groundColor.copy(e.groundColor),this}toJSON(e){let t=super.toJSON(e);return t.object.groundColor=this.groundColor.getHex(),t}},Bl=new pt,uu=new D,hu=new D,Er=class{constructor(e){this.camera=e,this.intensity=1,this.bias=0,this.biasNode=null,this.normalBias=0,this.radius=1,this.blurSamples=8,this.mapSize=new Ue(512,512),this.mapType=xn,this.map=null,this.mapPass=null,this.matrix=new pt,this.autoUpdate=!0,this.needsUpdate=!1,this._frustum=new Ss,this._frameExtents=new Ue(1,1),this._viewportCount=1,this._viewports=[new Dt(0,0,1,1)]}getViewportCount(){return this._viewportCount}getCamera(){return this.camera}getFrustum(){return this._frustum}updateMatrices(e){let t=this.camera;uu.setFromMatrixPosition(e.matrixWorld),t.position.copy(uu),hu.setFromMatrixPosition(e.target.matrixWorld),t.lookAt(hu),t.updateMatrixWorld(),this._updateMatrix(t,this.matrix,this._frustum)}_updateMatrix(e,t,n,s){Bl.multiplyMatrices(e.projectionMatrix,e.matrixWorldInverse),n.setFromProjectionMatrix(Bl,e.coordinateSystem,e.reversedDepth);let r=this._frameExtents,a=s?s.z/r.x:1,o=s?s.w/r.y:1,l=s?s.x/r.x:0,c=s?s.y/r.y:0;e.coordinateSystem===_s||e.reversedDepth?t.set(.5*a,0,0,.5*a+l,0,.5*o,0,.5*o+c,0,0,1,0,0,0,0,1):t.set(.5*a,0,0,.5*a+l,0,.5*o,0,.5*o+c,0,0,.5,.5,0,0,0,1),t.multiply(Bl)}getViewport(e){return this._viewports[e]}getFrameExtents(){return this._frameExtents}dispose(){this.map&&this.map.dispose(),this.mapPass&&this.mapPass.dispose()}copy(e){return this.camera=e.camera.clone(),this.intensity=e.intensity,this.bias=e.bias,this.radius=e.radius,this.autoUpdate=e.autoUpdate,this.needsUpdate=e.needsUpdate,this.normalBias=e.normalBias,this.blurSamples=e.blurSamples,this.mapSize.copy(e.mapSize),this.biasNode=e.biasNode,this}clone(){return new this.constructor().copy(this)}toJSON(){let e={};return e.intensity=this.intensity,e.bias=this.bias,e.normalBias=this.normalBias,e.radius=this.radius,e.blurSamples=this.blurSamples,e.mapSize=this.mapSize.toArray(),e.camera=this.camera.toJSON(!1).object,delete e.camera.matrix,e}},ba=new D,Sa=new Gt,Vn=new D,wr=class extends Ht{constructor(){super(),this.isCamera=!0,this.type="Camera",this.matrixWorldInverse=new pt,this.projectionMatrix=new pt,this.projectionMatrixInverse=new pt,this.coordinateSystem=Un,this._reversedDepth=!1}get reversedDepth(){return this._reversedDepth}copy(e,t){return super.copy(e,t),this.matrixWorldInverse.copy(e.matrixWorldInverse),this.projectionMatrix.copy(e.projectionMatrix),this.projectionMatrixInverse.copy(e.projectionMatrixInverse),this.coordinateSystem=e.coordinateSystem,this}getWorldDirection(e){return super.getWorldDirection(e).negate()}updateMatrixWorld(e){super.updateMatrixWorld(e),this.matrixWorld.decompose(ba,Sa,Vn),Vn.x===1&&Vn.y===1&&Vn.z===1?this.matrixWorldInverse.copy(this.matrixWorld).invert():this.matrixWorldInverse.compose(ba,Sa,Vn.set(1,1,1)).invert()}updateWorldMatrix(e,t,n=!1){super.updateWorldMatrix(e,t,n),this.matrixWorld.decompose(ba,Sa,Vn),Vn.x===1&&Vn.y===1&&Vn.z===1?this.matrixWorldInverse.copy(this.matrixWorld).invert():this.matrixWorldInverse.compose(ba,Sa,Vn.set(1,1,1)).invert()}clone(){return new this.constructor().copy(this)}},_i=new D,du=new Ue,fu=new Ue,Jt=class extends wr{constructor(e=50,t=1,n=.1,s=2e3){super(),this.isPerspectiveCamera=!0,this.type="PerspectiveCamera",this.fov=e,this.zoom=1,this.near=n,this.far=s,this.focus=10,this.aspect=t,this.view=null,this.filmGauge=35,this.filmOffset=0,this.updateProjectionMatrix()}copy(e,t){return super.copy(e,t),this.fov=e.fov,this.zoom=e.zoom,this.near=e.near,this.far=e.far,this.focus=e.focus,this.aspect=e.aspect,this.view=e.view===null?null:Object.assign({},e.view),this.filmGauge=e.filmGauge,this.filmOffset=e.filmOffset,this}setFocalLength(e){let t=.5*this.getFilmHeight()/e;this.fov=vs*2*Math.atan(t),this.updateProjectionMatrix()}getFocalLength(){let e=Math.tan(Ks*.5*this.fov);return .5*this.getFilmHeight()/e}getEffectiveFOV(){return vs*2*Math.atan(Math.tan(Ks*.5*this.fov)/this.zoom)}getFilmWidth(){return this.filmGauge*Math.min(this.aspect,1)}getFilmHeight(){return this.filmGauge/Math.max(this.aspect,1)}getViewBounds(e,t,n){_i.set(-1,-1,.5).applyMatrix4(this.projectionMatrixInverse),t.set(_i.x,_i.y).multiplyScalar(-e/_i.z),_i.set(1,1,.5).applyMatrix4(this.projectionMatrixInverse),n.set(_i.x,_i.y).multiplyScalar(-e/_i.z)}getViewSize(e,t){return this.getViewBounds(e,du,fu),t.subVectors(fu,du)}setViewOffset(e,t,n,s,r,a){this.aspect=e/t,this.view===null&&(this.view={enabled:!0,fullWidth:1,fullHeight:1,offsetX:0,offsetY:0,width:1,height:1}),this.view.enabled=!0,this.view.fullWidth=e,this.view.fullHeight=t,this.view.offsetX=n,this.view.offsetY=s,this.view.width=r,this.view.height=a,this.updateProjectionMatrix()}clearViewOffset(){this.view!==null&&(this.view.enabled=!1),this.updateProjectionMatrix()}updateProjectionMatrix(){let e=this.near,t=e*Math.tan(Ks*.5*this.fov)/this.zoom,n=2*t,s=this.aspect*n,r=-.5*s,a=this.view;if(this.view!==null&&this.view.enabled){let l=a.fullWidth,c=a.fullHeight;r+=a.offsetX*s/l,t-=a.offsetY*n/c,s*=a.width/l,n*=a.height/c}let o=this.filmOffset;o!==0&&(r+=e*o/this.getFilmWidth()),this.projectionMatrix.makePerspective(r,r+s,t,t-n,e,this.far,this.coordinateSystem,this.reversedDepth),this.projectionMatrixInverse.copy(this.projectionMatrix).invert()}toJSON(e){let t=super.toJSON(e);return t.object.fov=this.fov,t.object.zoom=this.zoom,t.object.near=this.near,t.object.far=this.far,t.object.focus=this.focus,t.object.aspect=this.aspect,this.view!==null&&(t.object.view=Object.assign({},this.view)),t.object.filmGauge=this.filmGauge,t.object.filmOffset=this.filmOffset,t}};var ql=class extends Er{constructor(){super(new Jt(90,1,.5,500)),this.isPointLightShadow=!0}},ai=class extends Rs{constructor(e,t,n=0,s=2){super(e,t),this.isPointLight=!0,this.type="PointLight",this.distance=n,this.decay=s,this.shadow=new ql}get power(){return this.intensity*4*Math.PI}set power(e){this.intensity=e/(4*Math.PI)}dispose(){super.dispose(),this.shadow.dispose()}copy(e,t){return super.copy(e,t),this.distance=e.distance,this.decay=e.decay,this.shadow=e.shadow.clone(),this}toJSON(e){let t=super.toJSON(e);return t.object.distance=this.distance,t.object.decay=this.decay,t.object.shadow=this.shadow.toJSON(),t}},Si=class extends wr{constructor(e=-1,t=1,n=1,s=-1,r=.1,a=2e3){super(),this.isOrthographicCamera=!0,this.type="OrthographicCamera",this.zoom=1,this.view=null,this.left=e,this.right=t,this.top=n,this.bottom=s,this.near=r,this.far=a,this.updateProjectionMatrix()}copy(e,t){return super.copy(e,t),this.left=e.left,this.right=e.right,this.top=e.top,this.bottom=e.bottom,this.near=e.near,this.far=e.far,this.zoom=e.zoom,this.view=e.view===null?null:Object.assign({},e.view),this}setViewOffset(e,t,n,s,r,a){this.view===null&&(this.view={enabled:!0,fullWidth:1,fullHeight:1,offsetX:0,offsetY:0,width:1,height:1}),this.view.enabled=!0,this.view.fullWidth=e,this.view.fullHeight=t,this.view.offsetX=n,this.view.offsetY=s,this.view.width=r,this.view.height=a,this.updateProjectionMatrix()}clearViewOffset(){this.view!==null&&(this.view.enabled=!1),this.updateProjectionMatrix()}updateProjectionMatrix(){let e=(this.right-this.left)/(2*this.zoom),t=(this.top-this.bottom)/(2*this.zoom),n=(this.right+this.left)/2,s=(this.top+this.bottom)/2,r=n-e,a=n+e,o=s+t,l=s-t;if(this.view!==null&&this.view.enabled){let c=(this.right-this.left)/this.view.fullWidth/this.zoom,h=(this.top-this.bottom)/this.view.fullHeight/this.zoom;r+=c*this.view.offsetX,a=r+c*this.view.width,o-=h*this.view.offsetY,l=o-h*this.view.height}this.projectionMatrix.makeOrthographic(r,a,o,l,this.near,this.far,this.coordinateSystem,this.reversedDepth),this.projectionMatrixInverse.copy(this.projectionMatrix).invert()}toJSON(e){let t=super.toJSON(e);return t.object.zoom=this.zoom,t.object.left=this.left,t.object.right=this.right,t.object.top=this.top,t.object.bottom=this.bottom,t.object.near=this.near,t.object.far=this.far,this.view!==null&&(t.object.view=Object.assign({},this.view)),t}},Xl=class extends Er{constructor(){super(new Si(-5,5,5,-5,.5,500)),this.isDirectionalLightShadow=!0}},Gi=class extends Rs{constructor(e,t){super(e,t),this.isDirectionalLight=!0,this.type="DirectionalLight",this.position.copy(Ht.DEFAULT_UP),this.updateMatrix(),this.target=new Ht,this.shadow=new Xl}dispose(){super.dispose(),this.shadow.dispose()}copy(e){return super.copy(e),this.target=e.target.clone(),this.shadow=e.shadow.clone(),this}toJSON(e){let t=super.toJSON(e);return t.object.shadow=this.shadow.toJSON(),t.object.target=this.target.uuid,t}};var ds=-90,fs=1,oo=class extends Ht{constructor(e,t,n){super(),this.type="CubeCamera",this.renderTarget=n,this.coordinateSystem=null,this.activeMipmapLevel=0;let s=new Jt(ds,fs,e,t);s.layers=this.layers,this.add(s);let r=new Jt(ds,fs,e,t);r.layers=this.layers,this.add(r);let a=new Jt(ds,fs,e,t);a.layers=this.layers,this.add(a);let o=new Jt(ds,fs,e,t);o.layers=this.layers,this.add(o);let l=new Jt(ds,fs,e,t);l.layers=this.layers,this.add(l);let c=new Jt(ds,fs,e,t);c.layers=this.layers,this.add(c)}updateCoordinateSystem(){let e=this.coordinateSystem,t=this.children.concat(),[n,s,r,a,o,l]=t;for(let c of t)this.remove(c);if(e===Un)n.up.set(0,1,0),n.lookAt(1,0,0),s.up.set(0,1,0),s.lookAt(-1,0,0),r.up.set(0,0,-1),r.lookAt(0,1,0),a.up.set(0,0,1),a.lookAt(0,-1,0),o.up.set(0,1,0),o.lookAt(0,0,1),l.up.set(0,1,0),l.lookAt(0,0,-1);else if(e===_s)n.up.set(0,-1,0),n.lookAt(-1,0,0),s.up.set(0,-1,0),s.lookAt(1,0,0),r.up.set(0,0,1),r.lookAt(0,1,0),a.up.set(0,0,-1),a.lookAt(0,-1,0),o.up.set(0,-1,0),o.lookAt(0,0,1),l.up.set(0,-1,0),l.lookAt(0,0,-1);else throw new Error("THREE.CubeCamera.updateCoordinateSystem(): Invalid coordinate system: "+e);for(let c of t)this.add(c),c.updateMatrixWorld()}update(e,t){this.parent===null&&this.updateMatrixWorld();let{renderTarget:n,activeMipmapLevel:s}=this;this.coordinateSystem!==e.coordinateSystem&&(this.coordinateSystem=e.coordinateSystem,this.updateCoordinateSystem());let[r,a,o,l,c,h]=this.children,f=e.getRenderTarget(),u=e.getActiveCubeFace(),d=e.getActiveMipmapLevel(),g=e.xr.enabled;e.xr.enabled=!1;let M=n.texture.generateMipmaps;n.texture.generateMipmaps=!1;let m=!1;e.isWebGLRenderer===!0?m=e.state.buffers.depth.getReversed():m=e.reversedDepthBuffer,e.setRenderTarget(n,0,s),m&&e.autoClear===!1&&e.clearDepth(),e.render(t,r),e.setRenderTarget(n,1,s),m&&e.autoClear===!1&&e.clearDepth(),e.render(t,a),e.setRenderTarget(n,2,s),m&&e.autoClear===!1&&e.clearDepth(),e.render(t,o),e.setRenderTarget(n,3,s),m&&e.autoClear===!1&&e.clearDepth(),e.render(t,l),e.setRenderTarget(n,4,s),m&&e.autoClear===!1&&e.clearDepth(),e.render(t,c),n.texture.generateMipmaps=M,e.setRenderTarget(n,5,s),m&&e.autoClear===!1&&e.clearDepth(),e.render(t,h),e.setRenderTarget(f,u,d),e.xr.enabled=g,n.texture.needsPMREMUpdate=!0}},lo=class extends Jt{constructor(e=[]){super(),this.isArrayCamera=!0,this.isMultiViewCamera=!1,this.cameras=e}},Ar=class{constructor(){this._previousTime=0,this._currentTime=0,this._startTime=performance.now(),this._delta=0,this._elapsed=0,this._timescale=1,this._document=null,this._pageVisibilityHandler=null}connect(e){this._document=e,e.hidden!==void 0&&(this._pageVisibilityHandler=Wd.bind(this),e.addEventListener("visibilitychange",this._pageVisibilityHandler,!1))}disconnect(){this._pageVisibilityHandler!==null&&(this._document.removeEventListener("visibilitychange",this._pageVisibilityHandler),this._pageVisibilityHandler=null),this._document=null}getDelta(){return this._delta/1e3}getElapsed(){return this._elapsed/1e3}getTimescale(){return this._timescale}setTimescale(e){return this._timescale=e,this}reset(){return this._currentTime=performance.now()-this._startTime,this}dispose(){this.disconnect()}update(e){return this._pageVisibilityHandler!==null&&this._document.hidden===!0?this._delta=0:(this._previousTime=this._currentTime,this._currentTime=(e!==void 0?e:performance.now())-this._startTime,this._delta=(this._currentTime-this._previousTime)*this._timescale,this._elapsed+=this._delta),this}};function Wd(){this._document.hidden===!1&&this.reset()}var pc="\\[\\]\\.:\\/",qd=new RegExp("["+pc+"]","g"),mc="[^"+pc+"]",Xd="[^"+pc.replace("\\.","")+"]",$d=/((?:WC+[\/:])*)/.source.replace("WC",mc),Yd=/(WCOD+)?/.source.replace("WCOD",Xd),Zd=/(?:\.(WC+)(?:\[(.+)\])?)?/.source.replace("WC",mc),jd=/\.(WC+)(?:\[(.+)\])?/.source.replace("WC",mc),Jd=new RegExp("^"+$d+Yd+Zd+jd+"$"),Kd=["material","materials","bones","map"],$l=class{constructor(e,t,n){let s=n||Nt.parseTrackName(t);this._targetGroup=e,this._bindings=e.subscribe_(t,s)}getValue(e,t){this.bind();let n=this._targetGroup.nCachedObjects_,s=this._bindings[n];s!==void 0&&s.getValue(e,t)}setValue(e,t){let n=this._bindings;for(let s=this._targetGroup.nCachedObjects_,r=n.length;s!==r;++s)n[s].setValue(e,t)}bind(){let e=this._bindings;for(let t=this._targetGroup.nCachedObjects_,n=e.length;t!==n;++t)e[t].bind()}unbind(){let e=this._bindings;for(let t=this._targetGroup.nCachedObjects_,n=e.length;t!==n;++t)e[t].unbind()}},Nt=class i{constructor(e,t,n){this.path=t,this.parsedPath=n||i.parseTrackName(t),this.node=i.findNode(e,this.parsedPath.nodeName),this.rootNode=e,this.getValue=this._getValue_unbound,this.setValue=this._setValue_unbound}static create(e,t,n){return e&&e.isAnimationObjectGroup?new i.Composite(e,t,n):new i(e,t,n)}static sanitizeNodeName(e){return e.replace(/\s/g,"_").replace(qd,"")}static parseTrackName(e){let t=Jd.exec(e);if(t===null)throw new Error("THREE.PropertyBinding: Cannot parse trackName: "+e);let n={nodeName:t[2],objectName:t[3],objectIndex:t[4],propertyName:t[5],propertyIndex:t[6]},s=n.nodeName&&n.nodeName.lastIndexOf(".");if(s!==void 0&&s!==-1){let r=n.nodeName.substring(s+1);Kd.indexOf(r)!==-1&&(n.nodeName=n.nodeName.substring(0,s),n.objectName=r)}if(n.propertyName===null||n.propertyName.length===0)throw new Error("THREE.PropertyBinding: can not parse propertyName from trackName: "+e);return n}static findNode(e,t){if(t===void 0||t===""||t==="."||t===-1||t===e.name||t===e.uuid)return e;if(e.skeleton){let n=e.skeleton.getBoneByName(t);if(n!==void 0)return n}if(e.children){let n=function(r){for(let a=0;a<r.length;a++){let o=r[a];if(o.name===t||o.uuid===t)return o;let l=n(o.children);if(l)return l}return null},s=n(e.children);if(s)return s}return null}_getValue_unavailable(){}_setValue_unavailable(){}_getValue_direct(e,t){e[t]=this.targetObject[this.propertyName]}_getValue_array(e,t){let n=this.resolvedProperty;for(let s=0,r=n.length;s!==r;++s)e[t++]=n[s]}_getValue_arrayElement(e,t){e[t]=this.resolvedProperty[this.propertyIndex]}_getValue_toArray(e,t){this.resolvedProperty.toArray(e,t)}_setValue_direct(e,t){this.targetObject[this.propertyName]=e[t]}_setValue_direct_setNeedsUpdate(e,t){this.targetObject[this.propertyName]=e[t],this.targetObject.needsUpdate=!0}_setValue_direct_setMatrixWorldNeedsUpdate(e,t){this.targetObject[this.propertyName]=e[t],this.targetObject.matrixWorldNeedsUpdate=!0}_setValue_array(e,t){let n=this.resolvedProperty;for(let s=0,r=n.length;s!==r;++s)n[s]=e[t++]}_setValue_array_setNeedsUpdate(e,t){let n=this.resolvedProperty;for(let s=0,r=n.length;s!==r;++s)n[s]=e[t++];this.targetObject.needsUpdate=!0}_setValue_array_setMatrixWorldNeedsUpdate(e,t){let n=this.resolvedProperty;for(let s=0,r=n.length;s!==r;++s)n[s]=e[t++];this.targetObject.matrixWorldNeedsUpdate=!0}_setValue_arrayElement(e,t){this.resolvedProperty[this.propertyIndex]=e[t]}_setValue_arrayElement_setNeedsUpdate(e,t){this.resolvedProperty[this.propertyIndex]=e[t],this.targetObject.needsUpdate=!0}_setValue_arrayElement_setMatrixWorldNeedsUpdate(e,t){this.resolvedProperty[this.propertyIndex]=e[t],this.targetObject.matrixWorldNeedsUpdate=!0}_setValue_fromArray(e,t){this.resolvedProperty.fromArray(e,t)}_setValue_fromArray_setNeedsUpdate(e,t){this.resolvedProperty.fromArray(e,t),this.targetObject.needsUpdate=!0}_setValue_fromArray_setMatrixWorldNeedsUpdate(e,t){this.resolvedProperty.fromArray(e,t),this.targetObject.matrixWorldNeedsUpdate=!0}_getValue_unbound(e,t){this.bind(),this.getValue(e,t)}_setValue_unbound(e,t){this.bind(),this.setValue(e,t)}bind(){let e=this.node,t=this.parsedPath,n=t.objectName,s=t.propertyName,r=t.propertyIndex;if(e||(e=i.findNode(this.rootNode,t.nodeName),this.node=e),this.getValue=this._getValue_unavailable,this.setValue=this._setValue_unavailable,!e){Je("PropertyBinding: No target node found for track: "+this.path+".");return}if(n){let c=t.objectIndex;switch(n){case"materials":if(!e.material){et("PropertyBinding: Can not bind to material as node does not have a material.",this);return}if(!e.material.materials){et("PropertyBinding: Can not bind to material.materials as node.material does not have a materials array.",this);return}e=e.material.materials;break;case"bones":if(!e.skeleton){et("PropertyBinding: Can not bind to bones as node does not have a skeleton.",this);return}e=e.skeleton.bones;for(let h=0;h<e.length;h++)if(e[h].name===c){c=h;break}break;case"map":if("map"in e){e=e.map;break}if(!e.material){et("PropertyBinding: Can not bind to material as node does not have a material.",this);return}if(!e.material.map){et("PropertyBinding: Can not bind to material.map as node.material does not have a map.",this);return}e=e.material.map;break;default:if(e[n]===void 0){et("PropertyBinding: Can not bind to objectName of node undefined.",this);return}e=e[n]}if(c!==void 0){if(e[c]===void 0){et("PropertyBinding: Trying to bind to objectIndex of objectName, but is undefined.",this,e);return}e=e[c]}}let a=e[s];if(a===void 0){let c=t.nodeName;et("PropertyBinding: Trying to update property for track: "+c+"."+s+" but it wasn't found.",e);return}let o=this.Versioning.None;this.targetObject=e,e.isMaterial===!0?o=this.Versioning.NeedsUpdate:e.isObject3D===!0&&(o=this.Versioning.MatrixWorldNeedsUpdate);let l=this.BindingType.Direct;if(r!==void 0){if(s==="morphTargetInfluences"){if(!e.geometry){et("PropertyBinding: Can not bind to morphTargetInfluences because node does not have a geometry.",this);return}if(!e.geometry.morphAttributes){et("PropertyBinding: Can not bind to morphTargetInfluences because node does not have a geometry.morphAttributes.",this);return}e.morphTargetDictionary[r]!==void 0&&(r=e.morphTargetDictionary[r])}l=this.BindingType.ArrayElement,this.resolvedProperty=a,this.propertyIndex=r}else a.fromArray!==void 0&&a.toArray!==void 0?(l=this.BindingType.HasFromToArray,this.resolvedProperty=a):Array.isArray(a)?(l=this.BindingType.EntireArray,this.resolvedProperty=a):this.propertyName=s;this.getValue=this.GetterByBindingType[l],this.setValue=this.SetterByBindingTypeAndVersioning[l][o]}unbind(){this.node=null,this.getValue=this._getValue_unbound,this.setValue=this._setValue_unbound}};Nt.Composite=$l;Nt.prototype.BindingType={Direct:0,EntireArray:1,ArrayElement:2,HasFromToArray:3};Nt.prototype.Versioning={None:0,NeedsUpdate:1,MatrixWorldNeedsUpdate:2};Nt.prototype.GetterByBindingType=[Nt.prototype._getValue_direct,Nt.prototype._getValue_array,Nt.prototype._getValue_arrayElement,Nt.prototype._getValue_toArray];Nt.prototype.SetterByBindingTypeAndVersioning=[[Nt.prototype._setValue_direct,Nt.prototype._setValue_direct_setNeedsUpdate,Nt.prototype._setValue_direct_setMatrixWorldNeedsUpdate],[Nt.prototype._setValue_array,Nt.prototype._setValue_array_setNeedsUpdate,Nt.prototype._setValue_array_setMatrixWorldNeedsUpdate],[Nt.prototype._setValue_arrayElement,Nt.prototype._setValue_arrayElement_setNeedsUpdate,Nt.prototype._setValue_arrayElement_setMatrixWorldNeedsUpdate],[Nt.prototype._setValue_fromArray,Nt.prototype._setValue_fromArray_setNeedsUpdate,Nt.prototype._setValue_fromArray_setMatrixWorldNeedsUpdate]];var n_=new Float32Array(1);var pu=new pt,Cr=class{constructor(e,t,n=0,s=1/0){this.ray=new zi(e,t),this.near=n,this.far=s,this.camera=null,this.layers=new Ms,this.params={Mesh:{},Line:{threshold:1},LOD:{},Points:{threshold:1},Sprite:{}}}set(e,t){this.ray.set(e,t)}setFromCamera(e,t){t.isPerspectiveCamera?(this.ray.origin.setFromMatrixPosition(t.matrixWorld),this.ray.direction.set(e.x,e.y,.5).unproject(t).sub(this.ray.origin).normalize(),this.camera=t):t.isOrthographicCamera?(this.ray.origin.set(e.x,e.y,t.projectionMatrix.elements[14]).unproject(t),this.ray.direction.set(0,0,-1).transformDirection(t.matrixWorld),this.camera=t):et("Raycaster: Unsupported camera type: "+t.type)}setFromXRController(e){return pu.identity().extractRotation(e.matrixWorld),this.ray.origin.setFromMatrixPosition(e.matrixWorld),this.ray.direction.set(0,0,-1).applyMatrix4(pu),this}intersectObject(e,t=!0,n=[]){return Yl(e,this,n,t),n.sort(mu),n}intersectObjects(e,t=!0,n=[]){for(let s=0,r=e.length;s<r;s++)Yl(e[s],this,n,t);return n.sort(mu),n}};function mu(i,e){return i.distance-e.distance}function Yl(i,e,t,n){let s=!0;if(i.layers.test(e.layers)&&i.raycast(e,t)===!1&&(s=!1),s===!0&&n===!0){let r=i.children;for(let a=0,o=r.length;a<o;a++)Yl(r[a],e,t,!0)}}var Zl=class i{static{i.prototype.isMatrix2=!0}constructor(e,t,n,s){this.elements=[1,0,0,1],e!==void 0&&this.set(e,t,n,s)}identity(){return this.set(1,0,0,1),this}fromArray(e,t=0){for(let n=0;n<4;n++)this.elements[n]=e[n+t];return this}set(e,t,n,s){let r=this.elements;return r[0]=e,r[2]=t,r[1]=n,r[3]=s,this}};function gc(i,e,t,n){let s=Qd(n);switch(t){case ac:return i*e;case _o:return i*e/s.components*s.byteLength;case xo:return i*e/s.components*s.byteLength;case Ci:return i*e*2/s.components*s.byteLength;case vo:return i*e*2/s.components*s.byteLength;case oc:return i*e*3/s.components*s.byteLength;case Pn:return i*e*4/s.components*s.byteLength;case yo:return i*e*4/s.components*s.byteLength;case Or:case Br:return Math.floor((i+3)/4)*Math.floor((e+3)/4)*8;case zr:case Vr:return Math.floor((i+3)/4)*Math.floor((e+3)/4)*16;case bo:case To:return Math.max(i,16)*Math.max(e,8)/4;case Mo:case So:return Math.max(i,8)*Math.max(e,8)/2;case Eo:case wo:case Co:case Ro:return Math.floor((i+3)/4)*Math.floor((e+3)/4)*8;case Ao:case Hr:case Po:return Math.floor((i+3)/4)*Math.floor((e+3)/4)*16;case Io:return Math.floor((i+3)/4)*Math.floor((e+3)/4)*16;case Lo:return Math.floor((i+4)/5)*Math.floor((e+3)/4)*16;case No:return Math.floor((i+4)/5)*Math.floor((e+4)/5)*16;case Do:return Math.floor((i+5)/6)*Math.floor((e+4)/5)*16;case Uo:return Math.floor((i+5)/6)*Math.floor((e+5)/6)*16;case Fo:return Math.floor((i+7)/8)*Math.floor((e+4)/5)*16;case ko:return Math.floor((i+7)/8)*Math.floor((e+5)/6)*16;case Oo:return Math.floor((i+7)/8)*Math.floor((e+7)/8)*16;case Bo:return Math.floor((i+9)/10)*Math.floor((e+4)/5)*16;case zo:return Math.floor((i+9)/10)*Math.floor((e+5)/6)*16;case Vo:return Math.floor((i+9)/10)*Math.floor((e+7)/8)*16;case Ho:return Math.floor((i+9)/10)*Math.floor((e+9)/10)*16;case Go:return Math.floor((i+11)/12)*Math.floor((e+9)/10)*16;case Wo:return Math.floor((i+11)/12)*Math.floor((e+11)/12)*16;case qo:case Xo:case $o:return Math.ceil(i/4)*Math.ceil(e/4)*16;case Yo:case Zo:return Math.ceil(i/4)*Math.ceil(e/4)*8;case Gr:case jo:return Math.ceil(i/4)*Math.ceil(e/4)*16}throw new Error(`Unable to determine texture byte length for ${t} format.`)}function Qd(i){switch(i){case xn:case nc:return{byteLength:1,components:1};case Ls:case ic:case tn:return{byteLength:2,components:1};case mo:case go:return{byteLength:2,components:4};case Bn:case po:case Rn:return{byteLength:4,components:1};case sc:case rc:return{byteLength:4,components:3}}throw new Error(`THREE.TextureUtils: Unknown texture type ${i}.`)}typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("register",{detail:{revision:"186"}}));typeof window<"u"&&(window.__THREE__?Je("WARNING: Multiple instances of Three.js being imported."):window.__THREE__="186");function Th(){let i=null,e=!1,t=null,n=null;function s(r,a){n=i.requestAnimationFrame(s),t(r,a)}return{start:function(){e!==!0&&t!==null&&i!==null&&(n=i.requestAnimationFrame(s),e=!0)},stop:function(){i!==null&&i.cancelAnimationFrame(n),e=!1},setAnimationLoop:function(r){t=r},setContext:function(r){i=r}}}function tf(i){let e=new WeakMap;function t(o,l){let c=o.array,h=o.usage,f=c.byteLength,u=i.createBuffer();i.bindBuffer(l,u),i.bufferData(l,c,h),o.onUploadCallback();let d;if(c instanceof Float32Array)d=i.FLOAT;else if(typeof Float16Array<"u"&&c instanceof Float16Array)d=i.HALF_FLOAT;else if(c instanceof Uint16Array)o.isFloat16BufferAttribute?d=i.HALF_FLOAT:d=i.UNSIGNED_SHORT;else if(c instanceof Int16Array)d=i.SHORT;else if(c instanceof Uint32Array)d=i.UNSIGNED_INT;else if(c instanceof Int32Array)d=i.INT;else if(c instanceof Int8Array)d=i.BYTE;else if(c instanceof Uint8Array)d=i.UNSIGNED_BYTE;else if(c instanceof Uint8ClampedArray)d=i.UNSIGNED_BYTE;else throw new Error("THREE.WebGLAttributes: Unsupported buffer data format: "+c);return{buffer:u,type:d,bytesPerElement:c.BYTES_PER_ELEMENT,version:o.version,size:f}}function n(o,l,c){let h=l.array,f=l.updateRanges;if(i.bindBuffer(c,o),f.length===0)i.bufferSubData(c,0,h);else{f.sort((d,g)=>d.start-g.start);let u=0;for(let d=1;d<f.length;d++){let g=f[u],M=f[d];M.start<=g.start+g.count+1?g.count=Math.max(g.count,M.start+M.count-g.start):(++u,f[u]=M)}f.length=u+1;for(let d=0,g=f.length;d<g;d++){let M=f[d];i.bufferSubData(c,M.start*h.BYTES_PER_ELEMENT,h,M.start,M.count)}l.clearUpdateRanges()}l.onUploadCallback()}function s(o){return o.isInterleavedBufferAttribute&&(o=o.data),e.get(o)}function r(o){o.isInterleavedBufferAttribute&&(o=o.data);let l=e.get(o);l&&(i.deleteBuffer(l.buffer),e.delete(o))}function a(o,l){if(o.isInterleavedBufferAttribute&&(o=o.data),o.isGLBufferAttribute){let h=e.get(o);(!h||h.version<o.version)&&e.set(o,{buffer:o.buffer,type:o.type,bytesPerElement:o.elementSize,version:o.version});return}let c=e.get(o);if(c===void 0)e.set(o,t(o,l));else if(c.version<o.version){if(c.size!==o.array.byteLength)throw new Error("THREE.WebGLAttributes: The size of the buffer attribute's array buffer does not match the original size. Resizing buffer attributes is not supported.");n(c.buffer,o,l),c.version=o.version}}return{get:s,remove:r,update:a}}var nf=`#ifdef USE_ALPHAHASH
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
#endif`,Mf=`#if NUM_CLIPPING_PLANES > 0
	vClipPosition = - mvPosition.xyz;
#endif`,bf=`#if defined( USE_COLOR ) || defined( USE_COLOR_ALPHA )
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
#endif`,Mp=`float faceDirection = gl_FrontFacing ? 1.0 : - 1.0;
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
vec3 nonPerturbedNormal = normal;`,bp=`#ifdef USE_NORMALMAP_OBJECTSPACE
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
}`,Mm=`#define MATCAP
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
}`,bm=`#define MATCAP
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
}`,lt={alphahash_fragment:nf,alphahash_pars_fragment:sf,alphamap_fragment:rf,alphamap_pars_fragment:af,alphatest_fragment:of,alphatest_pars_fragment:lf,aomap_fragment:cf,aomap_pars_fragment:uf,batching_pars_vertex:hf,batching_vertex:df,begin_vertex:ff,beginnormal_vertex:pf,bsdfs:mf,iridescence_fragment:gf,bumpmap_pars_fragment:_f,clipping_planes_fragment:xf,clipping_planes_pars_fragment:vf,clipping_planes_pars_vertex:yf,clipping_planes_vertex:Mf,color_fragment:bf,color_pars_fragment:Sf,color_pars_vertex:Tf,color_vertex:Ef,common:wf,cube_uv_reflection_fragment:Af,defaultnormal_vertex:Cf,displacementmap_pars_vertex:Rf,displacementmap_vertex:Pf,emissivemap_fragment:If,emissivemap_pars_fragment:Lf,colorspace_fragment:Nf,colorspace_pars_fragment:Df,envmap_fragment:Uf,envmap_common_pars_fragment:Ff,envmap_pars_fragment:kf,envmap_pars_vertex:Of,envmap_physical_pars_fragment:Zf,envmap_vertex:Bf,fog_vertex:zf,fog_pars_vertex:Vf,fog_fragment:Hf,fog_pars_fragment:Gf,gradientmap_pars_fragment:Wf,lightmap_pars_fragment:qf,lights_lambert_fragment:Xf,lights_lambert_pars_fragment:$f,lights_pars_begin:Yf,lights_toon_fragment:jf,lights_toon_pars_fragment:Jf,lights_phong_fragment:Kf,lights_phong_pars_fragment:Qf,lights_physical_fragment:ep,lights_physical_pars_fragment:tp,lights_fragment_begin:np,lights_fragment_maps:ip,lights_fragment_end:sp,lightprobes_pars_fragment:rp,logdepthbuf_fragment:ap,logdepthbuf_pars_fragment:op,logdepthbuf_pars_vertex:lp,logdepthbuf_vertex:cp,map_fragment:up,map_pars_fragment:hp,map_particle_fragment:dp,map_particle_pars_fragment:fp,metalnessmap_fragment:pp,metalnessmap_pars_fragment:mp,morphinstance_vertex:gp,morphcolor_vertex:_p,morphnormal_vertex:xp,morphtarget_pars_vertex:vp,morphtarget_vertex:yp,normal_fragment_begin:Mp,normal_fragment_maps:bp,normal_pars_fragment:Sp,normal_pars_vertex:Tp,normal_vertex:Ep,normalmap_pars_fragment:wp,clearcoat_normal_fragment_begin:Ap,clearcoat_normal_fragment_maps:Cp,clearcoat_pars_fragment:Rp,iridescence_pars_fragment:Pp,opaque_fragment:Ip,packing:Lp,premultiplied_alpha_fragment:Np,project_vertex:Dp,dithering_fragment:Up,dithering_pars_fragment:Fp,roughnessmap_fragment:kp,roughnessmap_pars_fragment:Op,shadowmap_pars_fragment:Bp,shadowmap_pars_vertex:zp,shadowmap_vertex:Vp,shadowmask_pars_fragment:Hp,skinbase_vertex:Gp,skinning_pars_vertex:Wp,skinning_vertex:qp,skinnormal_vertex:Xp,specularmap_fragment:$p,specularmap_pars_fragment:Yp,tonemapping_fragment:Zp,tonemapping_pars_fragment:jp,transmission_fragment:Jp,transmission_pars_fragment:Kp,uv_pars_fragment:Qp,uv_pars_vertex:em,uv_vertex:tm,worldpos_vertex:nm,background_vert:im,background_frag:sm,backgroundCube_vert:rm,backgroundCube_frag:am,cube_vert:om,cube_frag:lm,depth_vert:cm,depth_frag:um,distance_vert:hm,distance_frag:dm,equirect_vert:fm,equirect_frag:pm,linedashed_vert:mm,linedashed_frag:gm,meshbasic_vert:_m,meshbasic_frag:xm,meshlambert_vert:vm,meshlambert_frag:ym,meshmatcap_vert:Mm,meshmatcap_frag:bm,meshnormal_vert:Sm,meshnormal_frag:Tm,meshphong_vert:Em,meshphong_frag:wm,meshphysical_vert:Am,meshphysical_frag:Cm,meshtoon_vert:Rm,meshtoon_frag:Pm,points_vert:Im,points_frag:Lm,shadow_vert:Nm,shadow_frag:Dm,sprite_vert:Um,sprite_frag:Fm},De={common:{diffuse:{value:new Ke(16777215)},opacity:{value:1},map:{value:null},mapTransform:{value:new nt},alphaMap:{value:null},alphaMapTransform:{value:new nt},alphaTest:{value:0}},specularmap:{specularMap:{value:null},specularMapTransform:{value:new nt}},envmap:{envMap:{value:null},envMapRotation:{value:new nt},reflectivity:{value:1},ior:{value:1.5},refractionRatio:{value:.98},dfgLUT:{value:null}},aomap:{aoMap:{value:null},aoMapIntensity:{value:1},aoMapTransform:{value:new nt}},lightmap:{lightMap:{value:null},lightMapIntensity:{value:1},lightMapTransform:{value:new nt}},bumpmap:{bumpMap:{value:null},bumpMapTransform:{value:new nt},bumpScale:{value:1}},normalmap:{normalMap:{value:null},normalMapTransform:{value:new nt},normalScale:{value:new Ue(1,1)}},displacementmap:{displacementMap:{value:null},displacementMapTransform:{value:new nt},displacementScale:{value:1},displacementBias:{value:0}},emissivemap:{emissiveMap:{value:null},emissiveMapTransform:{value:new nt}},metalnessmap:{metalnessMap:{value:null},metalnessMapTransform:{value:new nt}},roughnessmap:{roughnessMap:{value:null},roughnessMapTransform:{value:new nt}},gradientmap:{gradientMap:{value:null}},fog:{fogDensity:{value:25e-5},fogNear:{value:1},fogFar:{value:2e3},fogColor:{value:new Ke(16777215)}},lights:{ambientLightColor:{value:[]},lightProbe:{value:[]},sunLights:{value:[],properties:{direction:{},color:{}}},sunLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{}}},sunShadowMatrix:{value:[]},sunShadowCascade:{value:[]},directionalLights:{value:[],properties:{direction:{},color:{}}},directionalLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{}}},directionalShadowMatrix:{value:[]},spotLights:{value:[],properties:{color:{},position:{},direction:{},distance:{},coneCos:{},penumbraCos:{},decay:{}}},spotLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{}}},spotLightMap:{value:[]},spotLightMatrix:{value:[]},pointLights:{value:[],properties:{color:{},position:{},decay:{},distance:{}}},pointLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{},shadowCameraNear:{},shadowCameraFar:{}}},pointShadowMatrix:{value:[]},hemisphereLights:{value:[],properties:{direction:{},skyColor:{},groundColor:{}}},rectAreaLights:{value:[],properties:{color:{},position:{},width:{},height:{}}},ltc_1:{value:null},ltc_2:{value:null},probesSH:{value:null},probesMin:{value:new D},probesMax:{value:new D},probesResolution:{value:new D}},points:{diffuse:{value:new Ke(16777215)},opacity:{value:1},size:{value:1},scale:{value:1},map:{value:null},alphaMap:{value:null},alphaMapTransform:{value:new nt},alphaTest:{value:0},uvTransform:{value:new nt}},sprite:{diffuse:{value:new Ke(16777215)},opacity:{value:1},center:{value:new Ue(.5,.5)},rotation:{value:0},map:{value:null},mapTransform:{value:new nt},alphaMap:{value:null},alphaMapTransform:{value:new nt},alphaTest:{value:0}}},jn={basic:{uniforms:an([De.common,De.specularmap,De.envmap,De.aomap,De.lightmap,De.fog]),vertexShader:lt.meshbasic_vert,fragmentShader:lt.meshbasic_frag},lambert:{uniforms:an([De.common,De.specularmap,De.envmap,De.aomap,De.lightmap,De.emissivemap,De.bumpmap,De.normalmap,De.displacementmap,De.fog,De.lights,{emissive:{value:new Ke(0)},envMapIntensity:{value:1}}]),vertexShader:lt.meshlambert_vert,fragmentShader:lt.meshlambert_frag},phong:{uniforms:an([De.common,De.specularmap,De.envmap,De.aomap,De.lightmap,De.emissivemap,De.bumpmap,De.normalmap,De.displacementmap,De.fog,De.lights,{emissive:{value:new Ke(0)},specular:{value:new Ke(1118481)},shininess:{value:30},envMapIntensity:{value:1}}]),vertexShader:lt.meshphong_vert,fragmentShader:lt.meshphong_frag},standard:{uniforms:an([De.common,De.envmap,De.aomap,De.lightmap,De.emissivemap,De.bumpmap,De.normalmap,De.displacementmap,De.roughnessmap,De.metalnessmap,De.fog,De.lights,{emissive:{value:new Ke(0)},roughness:{value:1},metalness:{value:0},envMapIntensity:{value:1}}]),vertexShader:lt.meshphysical_vert,fragmentShader:lt.meshphysical_frag},toon:{uniforms:an([De.common,De.aomap,De.lightmap,De.emissivemap,De.bumpmap,De.normalmap,De.displacementmap,De.gradientmap,De.fog,De.lights,{emissive:{value:new Ke(0)}}]),vertexShader:lt.meshtoon_vert,fragmentShader:lt.meshtoon_frag},matcap:{uniforms:an([De.common,De.bumpmap,De.normalmap,De.displacementmap,De.fog,{matcap:{value:null}}]),vertexShader:lt.meshmatcap_vert,fragmentShader:lt.meshmatcap_frag},points:{uniforms:an([De.points,De.fog]),vertexShader:lt.points_vert,fragmentShader:lt.points_frag},dashed:{uniforms:an([De.common,De.fog,{scale:{value:1},dashSize:{value:1},totalSize:{value:2}}]),vertexShader:lt.linedashed_vert,fragmentShader:lt.linedashed_frag},depth:{uniforms:an([De.common,De.displacementmap]),vertexShader:lt.depth_vert,fragmentShader:lt.depth_frag},normal:{uniforms:an([De.common,De.bumpmap,De.normalmap,De.displacementmap,{opacity:{value:1}}]),vertexShader:lt.meshnormal_vert,fragmentShader:lt.meshnormal_frag},sprite:{uniforms:an([De.sprite,De.fog]),vertexShader:lt.sprite_vert,fragmentShader:lt.sprite_frag},background:{uniforms:{uvTransform:{value:new nt},t2D:{value:null},backgroundIntensity:{value:1}},vertexShader:lt.background_vert,fragmentShader:lt.background_frag},backgroundCube:{uniforms:{envMap:{value:null},backgroundBlurriness:{value:0},backgroundIntensity:{value:1},backgroundRotation:{value:new nt}},vertexShader:lt.backgroundCube_vert,fragmentShader:lt.backgroundCube_frag},cube:{uniforms:{tCube:{value:null},tFlip:{value:-1},opacity:{value:1}},vertexShader:lt.cube_vert,fragmentShader:lt.cube_frag},equirect:{uniforms:{tEquirect:{value:null}},vertexShader:lt.equirect_vert,fragmentShader:lt.equirect_frag},distance:{uniforms:an([De.common,De.displacementmap,{referencePosition:{value:new D},nearDistance:{value:1},farDistance:{value:1e3}}]),vertexShader:lt.distance_vert,fragmentShader:lt.distance_frag},shadow:{uniforms:an([De.lights,De.fog,{color:{value:new Ke(0)},opacity:{value:1}}]),vertexShader:lt.shadow_vert,fragmentShader:lt.shadow_frag}};jn.physical={uniforms:an([jn.standard.uniforms,{clearcoat:{value:0},clearcoatMap:{value:null},clearcoatMapTransform:{value:new nt},clearcoatNormalMap:{value:null},clearcoatNormalMapTransform:{value:new nt},clearcoatNormalScale:{value:new Ue(1,1)},clearcoatRoughness:{value:0},clearcoatRoughnessMap:{value:null},clearcoatRoughnessMapTransform:{value:new nt},dispersion:{value:0},retroreflectivity:{value:0},iridescence:{value:0},iridescenceMap:{value:null},iridescenceMapTransform:{value:new nt},iridescenceIOR:{value:1.3},iridescenceThicknessMinimum:{value:100},iridescenceThicknessMaximum:{value:400},iridescenceThicknessMap:{value:null},iridescenceThicknessMapTransform:{value:new nt},sheen:{value:0},sheenColor:{value:new Ke(0)},sheenColorMap:{value:null},sheenColorMapTransform:{value:new nt},sheenRoughness:{value:1},sheenRoughnessMap:{value:null},sheenRoughnessMapTransform:{value:new nt},transmission:{value:0},transmissionMap:{value:null},transmissionMapTransform:{value:new nt},transmissionSamplerSize:{value:new Ue},transmissionSamplerMap:{value:null},thickness:{value:0},thicknessMap:{value:null},thicknessMapTransform:{value:new nt},attenuationDistance:{value:0},attenuationColor:{value:new Ke(0)},specularColor:{value:new Ke(1,1,1)},specularColorMap:{value:null},specularColorMapTransform:{value:new nt},specularIntensity:{value:1},specularIntensityMap:{value:null},specularIntensityMapTransform:{value:new nt},anisotropyVector:{value:new Ue},anisotropyMap:{value:null},anisotropyMapTransform:{value:new nt}}]),vertexShader:lt.meshphysical_vert,fragmentShader:lt.meshphysical_frag};var el={r:0,b:0,g:0},km=new pt,Eh=new nt;Eh.set(-1,0,0,0,1,0,0,0,1);function Om(i,e,t,n,s,r){let a=new Ke(0),o=s===!0?0:1,l,c,h=null,f=0,u=null;function d(T){let C=T.isScene===!0?T.background:null;if(C&&C.isTexture){let v=T.backgroundBlurriness>0;C=e.get(C,v)}return C}function g(T){let C=!1,v=d(T);v===null?m(a,o):v&&v.isColor&&(m(v,1),C=!0);let w=i.xr.getEnvironmentBlendMode();w==="additive"?t.buffers.color.setClear(0,0,0,1,r):w==="alpha-blend"&&t.buffers.color.setClear(0,0,0,0,r),(i.autoClear||C)&&(t.buffers.depth.setTest(!0),t.buffers.depth.setMask(!0),t.buffers.color.setMask(!0),i.clear(i.autoClearColor,i.autoClearDepth,i.autoClearStencil))}function M(T,C){let v=d(C);v&&(v.isCubeTexture||v.mapping===Fr)?(c===void 0&&(c=new yt(new kn(1,1,1),new Ot({name:"BackgroundCubeMaterial",uniforms:Yi(jn.backgroundCube.uniforms),vertexShader:jn.backgroundCube.vertexShader,fragmentShader:jn.backgroundCube.fragmentShader,side:en,depthTest:!1,depthWrite:!1,fog:!1,allowOverride:!1})),c.geometry.deleteAttribute("normal"),c.geometry.deleteAttribute("uv"),c.onBeforeRender=function(w,S,I){this.matrixWorld.copyPosition(I.matrixWorld)},Object.defineProperty(c.material,"envMap",{get:function(){return this.uniforms.envMap.value}}),n.update(c)),c.material.uniforms.envMap.value=v,c.material.uniforms.backgroundBlurriness.value=C.backgroundBlurriness,c.material.uniforms.backgroundIntensity.value=C.backgroundIntensity,c.material.uniforms.backgroundRotation.value.setFromMatrix4(km.makeRotationFromEuler(C.backgroundRotation)).transpose(),v.isCubeTexture&&v.isRenderTargetTexture===!1&&c.material.uniforms.backgroundRotation.value.premultiply(Eh),c.material.toneMapped=dt.getTransfer(v.colorSpace)!==bt,(h!==v||f!==v.version||u!==i.toneMapping)&&(c.material.needsUpdate=!0,h=v,f=v.version,u=i.toneMapping),c.layers.enableAll(),T.unshift(c,c.geometry,c.material,0,0,null)):v&&v.isTexture&&(l===void 0&&(l=new yt(new yr(2,2),new Ot({name:"BackgroundMaterial",uniforms:Yi(jn.background.uniforms),vertexShader:jn.background.vertexShader,fragmentShader:jn.background.fragmentShader,side:Ti,depthTest:!1,depthWrite:!1,fog:!1,allowOverride:!1})),l.geometry.deleteAttribute("normal"),Object.defineProperty(l.material,"map",{get:function(){return this.uniforms.t2D.value}}),n.update(l)),l.material.uniforms.t2D.value=v,l.material.uniforms.backgroundIntensity.value=C.backgroundIntensity,l.material.toneMapped=dt.getTransfer(v.colorSpace)!==bt,v.matrixAutoUpdate===!0&&v.updateMatrix(),l.material.uniforms.uvTransform.value.copy(v.matrix),(h!==v||f!==v.version||u!==i.toneMapping)&&(l.material.needsUpdate=!0,h=v,f=v.version,u=i.toneMapping),l.layers.enableAll(),T.unshift(l,l.geometry,l.material,0,0,null))}function m(T,C){T.getRGB(el,fc(i)),t.buffers.color.setClear(el.r,el.g,el.b,C,r)}function p(){c!==void 0&&(c.geometry.dispose(),c.material.dispose(),c=void 0),l!==void 0&&(l.geometry.dispose(),l.material.dispose(),l=void 0)}return{getClearColor:function(){return a},setClearColor:function(T,C=1){a.set(T),o=C,m(a,o)},getClearAlpha:function(){return o},setClearAlpha:function(T){o=T,m(a,o)},render:g,addToRenderList:M,dispose:p}}function Bm(i,e){let t=i.getParameter(i.MAX_VERTEX_ATTRIBS),n={},s=u(null),r=s,a=!1;function o(k,V,$,U,W){let ee=!1,ie=f(k,U,$,V);r!==ie&&(r=ie,c(r.object)),ee=d(k,U,$,W),ee&&g(k,U,$,W),W!==null&&e.update(W,i.ELEMENT_ARRAY_BUFFER),(ee||a)&&(a=!1,v(k,V,$,U),W!==null&&i.bindBuffer(i.ELEMENT_ARRAY_BUFFER,e.get(W).buffer))}function l(){return i.createVertexArray()}function c(k){return i.bindVertexArray(k)}function h(k){return i.deleteVertexArray(k)}function f(k,V,$,U){let W=U.wireframe===!0,ee=n[V.id];ee===void 0&&(ee={},n[V.id]=ee);let ie=k.isInstancedMesh===!0?k.id:0,Z=ee[ie];Z===void 0&&(Z={},ee[ie]=Z);let Q=Z[$.id];Q===void 0&&(Q={},Z[$.id]=Q);let ue=Q[W];return ue===void 0&&(ue=u(l()),Q[W]=ue),ue}function u(k){let V=[],$=[],U=[];for(let W=0;W<t;W++)V[W]=0,$[W]=0,U[W]=0;return{geometry:null,program:null,wireframe:!1,newAttributes:V,enabledAttributes:$,attributeDivisors:U,object:k,attributes:{},index:null}}function d(k,V,$,U){let W=r.attributes,ee=V.attributes,ie=0,Z=$.getAttributes();for(let Q in Z)if(Z[Q].location>=0){let se=W[Q],Ge=ee[Q];if(Ge===void 0&&(Q==="instanceMatrix"&&k.instanceMatrix&&(Ge=k.instanceMatrix),Q==="instanceColor"&&k.instanceColor&&(Ge=k.instanceColor)),se===void 0||se.attribute!==Ge||Ge&&se.data!==Ge.data)return!0;ie++}return r.attributesNum!==ie||r.index!==U}function g(k,V,$,U){let W={},ee=V.attributes,ie=0,Z=$.getAttributes();for(let Q in Z)if(Z[Q].location>=0){let se=ee[Q];se===void 0&&(Q==="instanceMatrix"&&k.instanceMatrix&&(se=k.instanceMatrix),Q==="instanceColor"&&k.instanceColor&&(se=k.instanceColor));let Ge={};Ge.attribute=se,se&&se.data&&(Ge.data=se.data),W[Q]=Ge,ie++}r.attributes=W,r.attributesNum=ie,r.index=U}function M(){let k=r.newAttributes;for(let V=0,$=k.length;V<$;V++)k[V]=0}function m(k){p(k,0)}function p(k,V){let $=r.newAttributes,U=r.enabledAttributes,W=r.attributeDivisors;$[k]=1,U[k]===0&&(i.enableVertexAttribArray(k),U[k]=1),W[k]!==V&&(i.vertexAttribDivisor(k,V),W[k]=V)}function T(){let k=r.newAttributes,V=r.enabledAttributes;for(let $=0,U=V.length;$<U;$++)V[$]!==k[$]&&(i.disableVertexAttribArray($),V[$]=0)}function C(k,V,$,U,W,ee,ie){ie===!0?i.vertexAttribIPointer(k,V,$,W,ee):i.vertexAttribPointer(k,V,$,U,W,ee)}function v(k,V,$,U){M();let W=U.attributes,ee=$.getAttributes(),ie=V.defaultAttributeValues;for(let Z in ee){let Q=ee[Z];if(Q.location>=0){let ue=W[Z];if(ue===void 0&&(Z==="instanceMatrix"&&k.instanceMatrix&&(ue=k.instanceMatrix),Z==="instanceColor"&&k.instanceColor&&(ue=k.instanceColor)),ue!==void 0){let se=ue.normalized,Ge=ue.itemSize,Pe=e.get(ue);if(Pe===void 0)continue;let ot=Pe.buffer,$e=Pe.type,Xe=Pe.bytesPerElement,K=$e===i.INT||$e===i.UNSIGNED_INT||ue.gpuType===po;if(ue.isInterleavedBufferAttribute){let re=ue.data,Se=re.stride,Le=ue.offset;if(re.isInstancedInterleavedBuffer){for(let Ie=0;Ie<Q.locationSize;Ie++)p(Q.location+Ie,re.meshPerAttribute);k.isInstancedMesh!==!0&&U._maxInstanceCount===void 0&&(U._maxInstanceCount=re.meshPerAttribute*re.count)}else for(let Ie=0;Ie<Q.locationSize;Ie++)m(Q.location+Ie);i.bindBuffer(i.ARRAY_BUFFER,ot);for(let Ie=0;Ie<Q.locationSize;Ie++)C(Q.location+Ie,Ge/Q.locationSize,$e,se,Se*Xe,(Le+Ge/Q.locationSize*Ie)*Xe,K)}else{if(ue.isInstancedBufferAttribute){for(let re=0;re<Q.locationSize;re++)p(Q.location+re,ue.meshPerAttribute);k.isInstancedMesh!==!0&&U._maxInstanceCount===void 0&&(U._maxInstanceCount=ue.meshPerAttribute*ue.count)}else for(let re=0;re<Q.locationSize;re++)m(Q.location+re);i.bindBuffer(i.ARRAY_BUFFER,ot);for(let re=0;re<Q.locationSize;re++)C(Q.location+re,Ge/Q.locationSize,$e,se,Ge*Xe,Ge/Q.locationSize*re*Xe,K)}}else if(ie!==void 0){let se=ie[Z];if(se!==void 0)switch(se.length){case 2:i.vertexAttrib2fv(Q.location,se);break;case 3:i.vertexAttrib3fv(Q.location,se);break;case 4:i.vertexAttrib4fv(Q.location,se);break;default:i.vertexAttrib1fv(Q.location,se)}}}}T()}function w(){A();for(let k in n){let V=n[k];for(let $ in V){let U=V[$];for(let W in U){let ee=U[W];for(let ie in ee)h(ee[ie].object),delete ee[ie];delete U[W]}}delete n[k]}}function S(k){if(n[k.id]===void 0)return;let V=n[k.id];for(let $ in V){let U=V[$];for(let W in U){let ee=U[W];for(let ie in ee)h(ee[ie].object),delete ee[ie];delete U[W]}}delete n[k.id]}function I(k){for(let V in n){let $=n[V];for(let U in $){let W=$[U];if(W[k.id]===void 0)continue;let ee=W[k.id];for(let ie in ee)h(ee[ie].object),delete ee[ie];delete W[k.id]}}}function x(k){for(let V in n){let $=n[V],U=k.isInstancedMesh===!0?k.id:0,W=$[U];if(W!==void 0){for(let ee in W){let ie=W[ee];for(let Z in ie)h(ie[Z].object),delete ie[Z];delete W[ee]}delete $[U],Object.keys($).length===0&&delete n[V]}}}function A(){N(),a=!0,r!==s&&(r=s,c(r.object))}function N(){s.geometry=null,s.program=null,s.wireframe=!1}return{setup:o,reset:A,resetDefaultState:N,dispose:w,releaseStatesOfGeometry:S,releaseStatesOfObject:x,releaseStatesOfProgram:I,initAttributes:M,enableAttribute:m,disableUnusedAttributes:T}}function zm(i,e,t){let n;function s(l){n=l}function r(l,c){i.drawArrays(n,l,c),t.update(c,n,1)}function a(l,c,h){h!==0&&(i.drawArraysInstanced(n,l,c,h),t.update(c,n,h))}function o(l,c,h){if(h===0)return;e.get("WEBGL_multi_draw").multiDrawArraysWEBGL(n,l,0,c,0,h);let u=0;for(let d=0;d<h;d++)u+=c[d];t.update(u,n,1)}this.setMode=s,this.render=r,this.renderInstances=a,this.renderMultiDraw=o}function Vm(i,e,t,n){let s;function r(){if(s!==void 0)return s;if(e.has("EXT_texture_filter_anisotropic")===!0){let I=e.get("EXT_texture_filter_anisotropic");s=i.getParameter(I.MAX_TEXTURE_MAX_ANISOTROPY_EXT)}else s=0;return s}function a(I){return!(I!==Pn&&n.convert(I)!==i.getParameter(i.IMPLEMENTATION_COLOR_READ_FORMAT))}function o(I){let x=I===tn&&(e.has("EXT_color_buffer_half_float")||e.has("EXT_color_buffer_float"));return!(I!==xn&&I!==Rn&&!x&&n.convert(I)!==i.getParameter(i.IMPLEMENTATION_COLOR_READ_TYPE))}function l(I){if(I==="highp"){if(i.getShaderPrecisionFormat(i.VERTEX_SHADER,i.HIGH_FLOAT).precision>0&&i.getShaderPrecisionFormat(i.FRAGMENT_SHADER,i.HIGH_FLOAT).precision>0)return"highp";I="mediump"}return I==="mediump"&&i.getShaderPrecisionFormat(i.VERTEX_SHADER,i.MEDIUM_FLOAT).precision>0&&i.getShaderPrecisionFormat(i.FRAGMENT_SHADER,i.MEDIUM_FLOAT).precision>0?"mediump":"lowp"}let c=t.precision!==void 0?t.precision:"highp",h=l(c);h!==c&&(Je("WebGLRenderer:",c,"not supported, using",h,"instead."),c=h);let f=t.logarithmicDepthBuffer===!0,u=t.reversedDepthBuffer===!0&&e.has("EXT_clip_control");t.reversedDepthBuffer===!0&&u===!1&&Je("WebGLRenderer: Unable to use reversed depth buffer due to missing EXT_clip_control extension. Fallback to default depth buffer.");let d=i.getParameter(i.MAX_TEXTURE_IMAGE_UNITS),g=i.getParameter(i.MAX_VERTEX_TEXTURE_IMAGE_UNITS),M=i.getParameter(i.MAX_TEXTURE_SIZE),m=i.getParameter(i.MAX_CUBE_MAP_TEXTURE_SIZE),p=i.getParameter(i.MAX_VERTEX_ATTRIBS),T=i.getParameter(i.MAX_VERTEX_UNIFORM_VECTORS),C=i.getParameter(i.MAX_VARYING_VECTORS),v=i.getParameter(i.MAX_FRAGMENT_UNIFORM_VECTORS),w=i.getParameter(i.MAX_SAMPLES),S=i.getParameter(i.SAMPLES);return{isWebGL2:!0,getMaxAnisotropy:r,getMaxPrecision:l,textureFormatReadable:a,textureTypeReadable:o,precision:c,logarithmicDepthBuffer:f,reversedDepthBuffer:u,maxTextures:d,maxVertexTextures:g,maxTextureSize:M,maxCubemapSize:m,maxAttributes:p,maxVertexUniforms:T,maxVaryings:C,maxFragmentUniforms:v,maxSamples:w,samples:S}}function Hm(i){let e=this,t=null,n=0,s=!1,r=!1,a=new Dn,o=new nt,l={value:null,needsUpdate:!1};this.uniform=l,this.numPlanes=0,this.numIntersection=0,this.init=function(f,u){let d=f.length!==0||u||n!==0||s;return s=u,n=f.length,d},this.beginShadows=function(){r=!0,h(null)},this.endShadows=function(){r=!1},this.setGlobalState=function(f,u){t=h(f,u,0)},this.setState=function(f,u,d){let g=f.clippingPlanes,M=f.clipIntersection,m=f.clipShadows,p=i.get(f);if(!s||g===null||g.length===0||r&&!m)r?h(null):c();else{let T=r?0:n,C=T*4,v=p.clippingState||null;l.value=v,v=h(g,u,C,d);for(let w=0;w!==C;++w)v[w]=t[w];p.clippingState=v,this.numIntersection=M?this.numPlanes:0,this.numPlanes+=T}};function c(){l.value!==t&&(l.value=t,l.needsUpdate=n>0),e.numPlanes=n,e.numIntersection=0}function h(f,u,d,g){let M=f!==null?f.length:0,m=null;if(M!==0){if(m=l.value,g!==!0||m===null){let p=d+M*4,T=u.matrixWorldInverse;o.getNormalMatrix(T),(m===null||m.length<p)&&(m=new Float32Array(p));for(let C=0,v=d;C!==M;++C,v+=4)a.copy(f[C]).applyMatrix4(T,o),a.normal.toArray(m,v),m[v+3]=a.constant}l.value=m,l.needsUpdate=!0}return e.numPlanes=M,e.numIntersection=0,m}}var Fs=4,Gm=6,Wm=20,qm=256,qr=new Si,ih=new Ke,_c=null,xc=0,vc=0,yc=!1,Xm=new D,Zi=new D,Os=class{constructor(e){this._renderer=e,this._pingPongRenderTarget=null,this._lodMax=0,this._cubeSize=0,this._sizeLods=[],this._lodMeshes=[],this._backgroundBox=null,this._cubemapMaterial=null,this._equirectMaterial=null,this._blurMaterial=null,this._ggxMaterial=null}fromScene(e,t=0,n=.1,s=100,r={}){let{size:a=256,position:o=Xm}=r;_c=this._renderer.getRenderTarget(),xc=this._renderer.getActiveCubeFace(),vc=this._renderer.getActiveMipmapLevel(),yc=this._renderer.xr.enabled,this._renderer.xr.enabled=!1,this._setSize(a);let l=this._allocateTargets();return l.depthBuffer=!0,this._sceneToCubeUV(e,n,s,l,o),t>0&&this._blur(l,0,0,t),this._applyPMREM(l),this._cleanup(l),l}fromEquirectangular(e,t=null){return this._fromTexture(e,t)}fromCubemap(e,t=null){return this._fromTexture(e,t)}compileCubemapShader(){this._cubemapMaterial===null&&(this._cubemapMaterial=ah(),this._compileMaterial(this._cubemapMaterial))}compileEquirectangularShader(){this._equirectMaterial===null&&(this._equirectMaterial=rh(),this._compileMaterial(this._equirectMaterial))}dispose(){this._dispose(),this._cubemapMaterial!==null&&this._cubemapMaterial.dispose(),this._equirectMaterial!==null&&this._equirectMaterial.dispose(),this._backgroundBox!==null&&(this._backgroundBox.geometry.dispose(),this._backgroundBox.material.dispose())}_setSize(e){this._lodMax=Math.floor(Math.log2(e)),this._cubeSize=Math.pow(2,this._lodMax)}_dispose(){this._blurMaterial!==null&&this._blurMaterial.dispose(),this._ggxMaterial!==null&&this._ggxMaterial.dispose(),this._pingPongRenderTarget!==null&&this._pingPongRenderTarget.dispose();for(let e=0;e<this._lodMeshes.length;e++)this._lodMeshes[e].geometry.dispose()}_cleanup(e){this._renderer.setRenderTarget(_c,xc,vc),this._renderer.xr.enabled=yc,e.scissorTest=!1,Us(e,0,0,e.width,e.height)}_fromTexture(e,t){e.mapping===Ei||e.mapping===$i?this._setSize(e.image.length===0?16:e.image[0].width||e.image[0].image.width):this._setSize(e.image.width/4),_c=this._renderer.getRenderTarget(),xc=this._renderer.getActiveCubeFace(),vc=this._renderer.getActiveMipmapLevel(),yc=this._renderer.xr.enabled,this._renderer.xr.enabled=!1;let n=t||this._allocateTargets();return this._textureToCubeUV(e,n),this._applyPMREM(n),this._cleanup(n),n}_allocateTargets(){let e=3*Math.max(this._cubeSize,112),t=4*this._cubeSize,n={magFilter:Qt,minFilter:Qt,generateMipmaps:!1,type:tn,format:Pn,colorSpace:ir,depthBuffer:!1},s=sh(e,t,n);if(this._pingPongRenderTarget===null||this._pingPongRenderTarget.width!==e||this._pingPongRenderTarget.height!==t){this._pingPongRenderTarget!==null&&this._dispose(),this._pingPongRenderTarget=sh(e,t,n);let{_lodMax:r}=this;({lodMeshes:this._lodMeshes,sizeLods:this._sizeLods}=$m(r)),this._blurMaterial=Zm(r,e,t),this._ggxMaterial=Ym(r,e,t)}return s}_compileMaterial(e){let t=new yt(new Rt,e);this._renderer.compile(t,qr)}_sceneToCubeUV(e,t,n,s,r){let l=new Jt(90,1,t,n),c=[1,-1,1,1,1,1],h=[1,1,1,-1,-1,-1],f=this._renderer,u=f.autoClear,d=f.toneMapping;f.getClearColor(ih),f.toneMapping=On,f.autoClear=!1,f.state.buffers.depth.getReversed()&&(f.setRenderTarget(s),f.clearDepth(),f.setRenderTarget(null)),this._backgroundBox===null&&(this._backgroundBox=new yt(new kn,new fn({name:"PMREM.Background",side:en,depthWrite:!1,depthTest:!1})));let M=this._backgroundBox,m=M.material,p=!1,T=e.background;T?T.isColor&&(m.color.copy(T),e.background=null,p=!0):(m.color.copy(ih),p=!0);for(let C=0;C<6;C++){let v=C%3;v===0?(l.up.set(0,c[C],0),l.position.set(r.x,r.y,r.z),l.lookAt(r.x+h[C],r.y,r.z)):v===1?(l.up.set(0,0,c[C]),l.position.set(r.x,r.y,r.z),l.lookAt(r.x,r.y+h[C],r.z)):(l.up.set(0,c[C],0),l.position.set(r.x,r.y,r.z),l.lookAt(r.x,r.y,r.z+h[C]));let w=this._cubeSize;Us(s,v*w,C>2?w:0,w,w),f.setRenderTarget(s),p&&f.render(M,l),f.render(e,l)}f.toneMapping=d,f.autoClear=u,e.background=T}_textureToCubeUV(e,t){let n=this._renderer,s=e.mapping===Ei||e.mapping===$i;s?(this._cubemapMaterial===null&&(this._cubemapMaterial=ah()),this._cubemapMaterial.uniforms.flipEnvMap.value=e.isRenderTargetTexture===!1?-1:1):this._equirectMaterial===null&&(this._equirectMaterial=rh());let r=s?this._cubemapMaterial:this._equirectMaterial,a=this._lodMeshes[0];a.material=r;let o=r.uniforms;o.envMap.value=e;let l=this._cubeSize;Us(t,0,0,3*l,2*l),n.setRenderTarget(t),n.render(a,qr)}_applyPMREM(e){let t=this._renderer,n=t.autoClear;t.autoClear=!1;let s=this._lodMeshes.length;for(let r=1;r<s;r++)this._applyGGXFilter(e,r-1,r);t.autoClear=n}_applyGGXFilter(e,t,n){let s=this._renderer,r=this._pingPongRenderTarget,a=this._ggxMaterial,o=this._lodMeshes[n];o.material=a;let l=a.uniforms,c=n/(this._lodMeshes.length-1),h=t/(this._lodMeshes.length-1),f=Math.sqrt(c*c-h*h),u=c*1.25,d=f*u,{_lodMax:g}=this,M=this._sizeLods[n],m=3*M*(n>g-Fs?n-g+Fs:0),p=4*(this._cubeSize-M);l.envMap.value=e.texture,l.roughness.value=d,l.mipInt.value=g-t,Us(r,m,p,3*M,2*M),s.setRenderTarget(r),s.render(o,qr),l.envMap.value=r.texture,l.roughness.value=0,l.mipInt.value=g-n,Us(e,m,p,3*M,2*M),s.setRenderTarget(e),s.render(o,qr)}_blur(e,t,n,s){let r=this._pingPongRenderTarget,a=Math.min(s,Math.PI)/Math.SQRT2;this._blurPass(e,r,t,n,a),this._blurPass(r,e,n,n,a)}_blurPass(e,t,n,s,r){let a=this._renderer,o=this._blurMaterial,l=this._lodMeshes[s];l.material=o;let c=o.uniforms;c.envMap.value=e.texture,c.sigma.value=r,c.mipInt.value=this._lodMax-n;let h=this._sizeLods[s],f=3*h*(s>this._lodMax-Fs?s-this._lodMax+Fs:0),u=4*(this._cubeSize-h);Us(t,f,u,3*h,2*h),a.setRenderTarget(t),a.render(l,qr)}};function $m(i){let e=[],t=[],n=i,s=i-Fs+1+Gm;for(let r=0;r<s;r++){let a=Math.pow(2,n);e.push(a);let o=1/(a-2),l=-o,c=1+o,h=[l,l,c,l,c,c,l,l,c,c,l,c],f=6,u=6,d=3,g=new Float32Array(d*u*f),M=new Float32Array(d*u*f);for(let p=0;p<f;p++){let T=p%3*2/3-1,C=p>2?0:-1,v=[T,C,0,T+2/3,C,0,T+2/3,C+1,0,T,C,0,T+2/3,C+1,0,T,C+1,0];g.set(v,d*u*p);for(let w=0;w<u;w++){let S=h[w*2]*2-1,I=h[w*2+1]*2-1;p===0?Zi.set(1,I,S):p===1?Zi.set(-S,1,-I):p===2?Zi.set(-S,I,1):p===3?Zi.set(-1,I,-S):p===4?Zi.set(-S,-1,I):Zi.set(S,I,-1),Zi.toArray(M,(p*u+w)*d)}}let m=new Rt;m.setAttribute("position",new Kt(g,d)),m.setAttribute("outputDirection",new Kt(M,d)),t.push(new yt(m,null)),n>Fs&&n--}return{lodMeshes:t,sizeLods:e}}function sh(i,e,t){let n=new Vt(i,e,t);return n.texture.mapping=Fr,n.texture.name="PMREM.cubeUv",n.scissorTest=!0,n}function Us(i,e,t,n,s){i.viewport.set(e,t,n,s),i.scissor.set(e,t,n,s)}function Ym(i,e,t){return new Ot({name:"PMREMGGXConvolution",defines:{GGX_SAMPLES:qm,CUBEUV_TEXEL_WIDTH:1/e,CUBEUV_TEXEL_HEIGHT:1/t,CUBEUV_MAX_MIP:`${i}.0`},uniforms:{envMap:{value:null},roughness:{value:0},mipInt:{value:0}},vertexShader:sl(),fragmentShader:`

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
		`,blending:Cn,depthTest:!1,depthWrite:!1})}function Zm(i,e,t){return new Ot({name:"SphericalGaussianBlur",defines:{SAMPLES:Wm,CUBEUV_TEXEL_WIDTH:1/e,CUBEUV_TEXEL_HEIGHT:1/t,CUBEUV_MAX_MIP:`${i}.0`},uniforms:{envMap:{value:null},sigma:{value:0},mipInt:{value:0}},vertexShader:sl(),fragmentShader:`

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
		`,blending:Cn,depthTest:!1,depthWrite:!1})}function rh(){return new Ot({name:"EquirectangularToCubeUV",uniforms:{envMap:{value:null}},vertexShader:sl(),fragmentShader:`

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
		`,blending:Cn,depthTest:!1,depthWrite:!1})}function ah(){return new Ot({name:"CubemapToCubeUV",uniforms:{envMap:{value:null},flipEnvMap:{value:-1}},vertexShader:sl(),fragmentShader:`

			precision mediump float;
			precision mediump int;

			uniform float flipEnvMap;

			varying vec3 vOutputDirection;

			uniform samplerCube envMap;

			void main() {

				gl_FragColor = textureCube( envMap, vec3( flipEnvMap * vOutputDirection.x, vOutputDirection.yz ) );

			}
		`,blending:Cn,depthTest:!1,depthWrite:!1})}function sl(){return`

		precision mediump float;
		precision mediump int;

		attribute vec3 outputDirection;

		varying vec3 vOutputDirection;

		void main() {

			vOutputDirection = outputDirection;
			gl_Position = vec4( position, 1.0 );

		}
	`}var nl=class extends Vt{constructor(e=1,t={}){super(e,e,t),this.isWebGLCubeRenderTarget=!0;let n={width:e,height:e,depth:1},s=[n,n,n,n,n,n];this.texture=new pr(s),this._setTextureOptions(t),this.texture.isRenderTargetTexture=!0}fromEquirectangularTexture(e,t){this.texture.type=t.type,this.texture.colorSpace=t.colorSpace,this.texture.generateMipmaps=t.generateMipmaps,this.texture.minFilter=t.minFilter,this.texture.magFilter=t.magFilter;let n={uniforms:{tEquirect:{value:null}},vertexShader:`

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
			`},s=new kn(5,5,5),r=new Ot({name:"CubemapFromEquirect",uniforms:Yi(n.uniforms),vertexShader:n.vertexShader,fragmentShader:n.fragmentShader,side:en,blending:Cn});r.uniforms.tEquirect.value=t;let a=new yt(s,r),o=t.minFilter;return t.minFilter===wi&&(t.minFilter=Qt),new oo(1,10,this).update(e,a),t.minFilter=o,a.geometry.dispose(),a.material.dispose(),this}clear(e,t=!0,n=!0,s=!0){let r=e.getRenderTarget();for(let a=0;a<6;a++)e.setRenderTarget(this,a),e.clear(t,n,s);e.setRenderTarget(r)}};function jm(i){let e=new WeakMap,t=new WeakMap,n=null;function s(u,d=!1){return u==null?null:d?a(u):r(u)}function r(u){if(u&&u.isTexture){let d=u.mapping;if(d===uo||d===ho)if(e.has(u)){let g=e.get(u).texture;return o(g,u.mapping)}else{let g=u.image;if(g&&g.height>0){let M=new nl(g.height);return M.fromEquirectangularTexture(i,u),e.set(u,M),u.addEventListener("dispose",c),o(M.texture,u.mapping)}else return null}}return u}function a(u){if(u&&u.isTexture){let d=u.mapping,g=d===uo||d===ho,M=d===Ei||d===$i;if(g||M){let m=t.get(u),p=m!==void 0?m.texture.pmremVersion:0;if(u.isRenderTargetTexture&&u.pmremVersion!==p)return n===null&&(n=new Os(i)),m=g?n.fromEquirectangular(u,m):n.fromCubemap(u,m),m.texture.pmremVersion=u.pmremVersion,t.set(u,m),m.texture;if(m!==void 0)return m.texture;{let T=u.image;return g&&T&&T.height>0||M&&T&&l(T)?(n===null&&(n=new Os(i)),m=g?n.fromEquirectangular(u):n.fromCubemap(u),m.texture.pmremVersion=u.pmremVersion,t.set(u,m),u.addEventListener("dispose",h),m.texture):null}}}return u}function o(u,d){return d===uo?u.mapping=Ei:d===ho&&(u.mapping=$i),u}function l(u){let d=0,g=6;for(let M=0;M<g;M++)u[M]!==void 0&&d++;return d===g}function c(u){let d=u.target;d.removeEventListener("dispose",c);let g=e.get(d);g!==void 0&&(e.delete(d),g.dispose())}function h(u){let d=u.target;d.removeEventListener("dispose",h);let g=t.get(d);g!==void 0&&(t.delete(d),g.dispose())}function f(){e=new WeakMap,t=new WeakMap,n!==null&&(n.dispose(),n=null)}return{get:s,dispose:f}}function Jm(i){let e={};function t(n){if(e[n]!==void 0)return e[n];let s=i.getExtension(n);return e[n]=s,s}return{has:function(n){return t(n)!==null},init:function(){t("EXT_color_buffer_float"),t("WEBGL_clip_cull_distance"),t("OES_texture_float_linear"),t("EXT_color_buffer_half_float"),t("WEBGL_multisampled_render_to_texture"),t("WEBGL_render_shared_exponent")},get:function(n){let s=t(n);return s===null&&Oi("WebGLRenderer: "+n+" extension not supported."),s}}}function Km(i,e,t,n){let s={},r=new WeakMap;function a(f){let u=f.target;u.index!==null&&e.remove(u.index);for(let g in u.attributes)e.remove(u.attributes[g]);u.removeEventListener("dispose",a),delete s[u.id];let d=r.get(u);d&&(e.remove(d),r.delete(u)),n.releaseStatesOfGeometry(u),u.isInstancedBufferGeometry===!0&&delete u._maxInstanceCount,t.memory.geometries--}function o(f,u){return s[u.id]===!0||(u.addEventListener("dispose",a),s[u.id]=!0,t.memory.geometries++),u}function l(f){let u=f.attributes;for(let d in u)e.update(u[d],i.ARRAY_BUFFER)}function c(f){let u=[],d=f.index,g=f.attributes.position,M=0;if(g===void 0)return;if(d!==null){let T=d.array;M=d.version;for(let C=0,v=T.length;C<v;C+=3){let w=T[C+0],S=T[C+1],I=T[C+2];u.push(w,S,S,I,I,w)}}else{let T=g.array;M=g.version;for(let C=0,v=T.length/3-1;C<v;C+=3){let w=C+0,S=C+1,I=C+2;u.push(w,S,S,I,I,w)}}let m=new(g.count>=65535?cr:lr)(u,1);m.version=M;let p=r.get(f);p&&e.remove(p),r.set(f,m)}function h(f){let u=r.get(f);if(u){let d=f.index;d!==null&&u.version<d.version&&c(f)}else c(f);return r.get(f)}return{get:o,update:l,getWireframeAttribute:h}}function Qm(i,e,t){let n;function s(f){n=f}let r,a;function o(f){r=f.type,a=f.bytesPerElement}function l(f,u){i.drawElements(n,u,r,f*a),t.update(u,n,1)}function c(f,u,d){d!==0&&(i.drawElementsInstanced(n,u,r,f*a,d),t.update(u,n,d))}function h(f,u,d){if(d===0)return;e.get("WEBGL_multi_draw").multiDrawElementsWEBGL(n,u,0,r,f,0,d);let M=0;for(let m=0;m<d;m++)M+=u[m];t.update(M,n,1)}this.setMode=s,this.setIndex=o,this.render=l,this.renderInstances=c,this.renderMultiDraw=h}function eg(i){let e={geometries:0,textures:0},t={frame:0,calls:0,triangles:0,points:0,lines:0};function n(r,a,o){switch(t.calls++,a){case i.TRIANGLES:t.triangles+=o*(r/3);break;case i.LINES:t.lines+=o*(r/2);break;case i.LINE_STRIP:t.lines+=o*(r-1);break;case i.LINE_LOOP:t.lines+=o*r;break;case i.POINTS:t.points+=o*r;break;default:et("WebGLInfo: Unknown draw mode:",a);break}}function s(){t.calls=0,t.triangles=0,t.points=0,t.lines=0}return{memory:e,render:t,programs:null,autoReset:!0,reset:s,update:n}}function tg(i,e,t){let n=new WeakMap,s=new Dt;function r(a,o,l){let c=a.morphTargetInfluences,h=o.morphAttributes.position||o.morphAttributes.normal||o.morphAttributes.color,f=h!==void 0?h.length:0,u=n.get(o);if(u===void 0||u.count!==f){let A=function(){I.dispose(),n.delete(o),o.removeEventListener("dispose",A)};u!==void 0&&u.texture.dispose();let d=o.morphAttributes.position!==void 0,g=o.morphAttributes.normal!==void 0,M=o.morphAttributes.color!==void 0,m=o.morphAttributes.position||[],p=o.morphAttributes.normal||[],T=o.morphAttributes.color||[],C=0;d===!0&&(C=1),g===!0&&(C=2),M===!0&&(C=3);let v=o.attributes.position.count*C,w=1;v>e.maxTextureSize&&(w=Math.ceil(v/e.maxTextureSize),v=e.maxTextureSize);let S=new Float32Array(v*w*4*f),I=new ar(S,v,w,f);I.type=Rn,I.needsUpdate=!0;let x=C*4;for(let N=0;N<f;N++){let k=m[N],V=p[N],$=T[N],U=v*w*4*N;for(let W=0;W<k.count;W++){let ee=W*x;d===!0&&(s.fromBufferAttribute(k,W),S[U+ee+0]=s.x,S[U+ee+1]=s.y,S[U+ee+2]=s.z,S[U+ee+3]=0),g===!0&&(s.fromBufferAttribute(V,W),S[U+ee+4]=s.x,S[U+ee+5]=s.y,S[U+ee+6]=s.z,S[U+ee+7]=0),M===!0&&(s.fromBufferAttribute($,W),S[U+ee+8]=s.x,S[U+ee+9]=s.y,S[U+ee+10]=s.z,S[U+ee+11]=$.itemSize===4?s.w:1)}}u={count:f,texture:I,size:new Ue(v,w)},n.set(o,u),o.addEventListener("dispose",A)}if(a.isInstancedMesh===!0&&a.morphTexture!==null)l.getUniforms().setValue(i,"morphTexture",a.morphTexture,t);else{let d=0;for(let M=0;M<c.length;M++)d+=c[M];let g=o.morphTargetsRelative?1:1-d;l.getUniforms().setValue(i,"morphTargetBaseInfluence",g),l.getUniforms().setValue(i,"morphTargetInfluences",c)}l.getUniforms().setValue(i,"morphTargetsTexture",u.texture,t),l.getUniforms().setValue(i,"morphTargetsTextureSize",u.size)}return{update:r}}function ng(i,e,t,n,s){let r=new WeakMap;function a(c){let h=s.render.frame,f=c.geometry,u=e.get(c,f);if(r.get(u)!==h&&(e.update(u),r.set(u,h)),c.isInstancedMesh&&(c.hasEventListener("dispose",l)===!1&&c.addEventListener("dispose",l),r.get(c)!==h&&(t.update(c.instanceMatrix,i.ARRAY_BUFFER),c.instanceColor!==null&&t.update(c.instanceColor,i.ARRAY_BUFFER),r.set(c,h))),c.isSkinnedMesh){let d=c.skeleton;r.get(d)!==h&&(d.update(),r.set(d,h))}return u}function o(){r=new WeakMap}function l(c){let h=c.target;h.removeEventListener("dispose",l),n.releaseStatesOfObject(h),t.remove(h.instanceMatrix),h.instanceColor!==null&&t.remove(h.instanceColor)}return{update:a,dispose:o}}var ig={[Pr]:"LINEAR_TONE_MAPPING",[Ir]:"REINHARD_TONE_MAPPING",[Lr]:"CINEON_TONE_MAPPING",[Xi]:"ACES_FILMIC_TONE_MAPPING",[Dr]:"AGX_TONE_MAPPING",[Ur]:"NEUTRAL_TONE_MAPPING",[Nr]:"CUSTOM_TONE_MAPPING"};function sg(i,e,t,n,s,r){let a=new Vt(e,t,{type:i,depthBuffer:s,stencilBuffer:r,samples:n?4:0,storeMultisampledDepthBuffer:!1,storeMultisampledStencilBuffer:!1,resolveDepthBuffer:!1,resolveStencilBuffer:!1}),o=null,l=null,c=new Rt;c.setAttribute("position",new vt([-1,3,0,-1,-1,0,3,-1,0],3)),c.setAttribute("uv",new vt([0,2,0,0,2,0],2));let h=new Cs({uniforms:{tDiffuse:{value:null}},vertexShader:`
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
			}`,depthTest:!1,depthWrite:!1}),f=new yt(c,h),u=new Si(-1,1,1,-1,0,1),d=null,g=null,M=!1,m,p=null,T=[],C=!1;this.setSize=function(v,w){a.setSize(v,w),o!==null&&o.setSize(v,w),l!==null&&l.setSize(v,w);for(let S=0;S<T.length;S++){let I=T[S];I.setSize&&I.setSize(v,w)}},this.setEffects=function(v){T=v,C=T.length>0&&T[0].isRenderPass===!0;let w=a.width,S=a.height;T.length>0&&o===null&&(o=new Vt(w,S,{type:tn,depthBuffer:!1,stencilBuffer:!1}),l=new Vt(w,S,{type:tn,depthBuffer:!1,stencilBuffer:!1}));for(let I=0;I<T.length;I++){let x=T[I];x.setSize&&x.setSize(w,S)}},this.begin=function(v,w){if(M||v.toneMapping===On&&T.length===0)return!1;if(p=w,w!==null){let S=w.width,I=w.height;(a.width!==S||a.height!==I)&&this.setSize(S,I)}return C===!1&&v.setRenderTarget(a),m=v.toneMapping,v.toneMapping=On,!0},this.hasRenderPass=function(){return C},this.end=function(v,w){v.toneMapping=m,M=!0;let S=a,I=o;for(let x=0;x<T.length;x++){let A=T[x];A.enabled!==!1&&(A.render(v,I,S,w),A.needsSwap!==!1&&(S=I,I=I===o?l:o))}if(d!==v.outputColorSpace||g!==v.toneMapping){d=v.outputColorSpace,g=v.toneMapping,h.defines={},dt.getTransfer(d)===bt&&(h.defines.SRGB_TRANSFER="");let x=ig[g];x&&(h.defines[x]=""),h.needsUpdate=!0}h.uniforms.tDiffuse.value=S.texture,v.setRenderTarget(p),v.render(f,u),p=null,M=!1},this.isCompositing=function(){return M},this.dispose=function(){a.dispose(),o!==null&&o.dispose(),l!==null&&l.dispose(),c.dispose(),h.dispose()}}var wh=new mn,Sc=new vi(1,1),Ah=new ar,Ch=new Oa,Rh=new pr,oh=[],lh=[],ch=new Float32Array(16),uh=new Float32Array(9),hh=new Float32Array(4);function Bs(i,e,t){let n=i[0];if(n<=0||n>0)return i;let s=e*t,r=oh[s];if(r===void 0&&(r=new Float32Array(s),oh[s]=r),e!==0){n.toArray(r,0);for(let a=1,o=0;a!==e;++a)o+=t,i[a].toArray(r,o)}return r}function Wt(i,e){if(i.length!==e.length)return!1;for(let t=0,n=i.length;t<n;t++)if(i[t]!==e[t])return!1;return!0}function qt(i,e){for(let t=0,n=e.length;t<n;t++)i[t]=e[t]}function rl(i,e){let t=lh[e];t===void 0&&(t=new Int32Array(e),lh[e]=t);for(let n=0;n!==e;++n)t[n]=i.allocateTextureUnit();return t}function rg(i,e){let t=this.cache;t[0]!==e&&(i.uniform1f(this.addr,e),t[0]=e)}function ag(i,e){let t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y)&&(i.uniform2f(this.addr,e.x,e.y),t[0]=e.x,t[1]=e.y);else{if(Wt(t,e))return;i.uniform2fv(this.addr,e),qt(t,e)}}function og(i,e){let t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z)&&(i.uniform3f(this.addr,e.x,e.y,e.z),t[0]=e.x,t[1]=e.y,t[2]=e.z);else if(e.r!==void 0)(t[0]!==e.r||t[1]!==e.g||t[2]!==e.b)&&(i.uniform3f(this.addr,e.r,e.g,e.b),t[0]=e.r,t[1]=e.g,t[2]=e.b);else{if(Wt(t,e))return;i.uniform3fv(this.addr,e),qt(t,e)}}function lg(i,e){let t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z||t[3]!==e.w)&&(i.uniform4f(this.addr,e.x,e.y,e.z,e.w),t[0]=e.x,t[1]=e.y,t[2]=e.z,t[3]=e.w);else{if(Wt(t,e))return;i.uniform4fv(this.addr,e),qt(t,e)}}function cg(i,e){let t=this.cache,n=e.elements;if(n===void 0){if(Wt(t,e))return;i.uniformMatrix2fv(this.addr,!1,e),qt(t,e)}else{if(Wt(t,n))return;hh.set(n),i.uniformMatrix2fv(this.addr,!1,hh),qt(t,n)}}function ug(i,e){let t=this.cache,n=e.elements;if(n===void 0){if(Wt(t,e))return;i.uniformMatrix3fv(this.addr,!1,e),qt(t,e)}else{if(Wt(t,n))return;uh.set(n),i.uniformMatrix3fv(this.addr,!1,uh),qt(t,n)}}function hg(i,e){let t=this.cache,n=e.elements;if(n===void 0){if(Wt(t,e))return;i.uniformMatrix4fv(this.addr,!1,e),qt(t,e)}else{if(Wt(t,n))return;ch.set(n),i.uniformMatrix4fv(this.addr,!1,ch),qt(t,n)}}function dg(i,e){let t=this.cache;t[0]!==e&&(i.uniform1i(this.addr,e),t[0]=e)}function fg(i,e){let t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y)&&(i.uniform2i(this.addr,e.x,e.y),t[0]=e.x,t[1]=e.y);else{if(Wt(t,e))return;i.uniform2iv(this.addr,e),qt(t,e)}}function pg(i,e){let t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z)&&(i.uniform3i(this.addr,e.x,e.y,e.z),t[0]=e.x,t[1]=e.y,t[2]=e.z);else{if(Wt(t,e))return;i.uniform3iv(this.addr,e),qt(t,e)}}function mg(i,e){let t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z||t[3]!==e.w)&&(i.uniform4i(this.addr,e.x,e.y,e.z,e.w),t[0]=e.x,t[1]=e.y,t[2]=e.z,t[3]=e.w);else{if(Wt(t,e))return;i.uniform4iv(this.addr,e),qt(t,e)}}function gg(i,e){let t=this.cache;t[0]!==e&&(i.uniform1ui(this.addr,e),t[0]=e)}function _g(i,e){let t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y)&&(i.uniform2ui(this.addr,e.x,e.y),t[0]=e.x,t[1]=e.y);else{if(Wt(t,e))return;i.uniform2uiv(this.addr,e),qt(t,e)}}function xg(i,e){let t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z)&&(i.uniform3ui(this.addr,e.x,e.y,e.z),t[0]=e.x,t[1]=e.y,t[2]=e.z);else{if(Wt(t,e))return;i.uniform3uiv(this.addr,e),qt(t,e)}}function vg(i,e){let t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z||t[3]!==e.w)&&(i.uniform4ui(this.addr,e.x,e.y,e.z,e.w),t[0]=e.x,t[1]=e.y,t[2]=e.z,t[3]=e.w);else{if(Wt(t,e))return;i.uniform4uiv(this.addr,e),qt(t,e)}}function yg(i,e,t){let n=this.cache,s=t.allocateTextureUnit();n[0]!==s&&(i.uniform1i(this.addr,s),n[0]=s);let r;this.type===i.SAMPLER_2D_SHADOW?(Sc.compareFunction=t.isReversedDepthBuffer()?Ko:Jo,r=Sc):r=wh,t.setTexture2D(e||r,s)}function Mg(i,e,t){let n=this.cache,s=t.allocateTextureUnit();n[0]!==s&&(i.uniform1i(this.addr,s),n[0]=s),t.setTexture3D(e||Ch,s)}function bg(i,e,t){let n=this.cache,s=t.allocateTextureUnit();n[0]!==s&&(i.uniform1i(this.addr,s),n[0]=s),t.setTextureCube(e||Rh,s)}function Sg(i,e,t){let n=this.cache,s=t.allocateTextureUnit();n[0]!==s&&(i.uniform1i(this.addr,s),n[0]=s),t.setTexture2DArray(e||Ah,s)}function Tg(i){switch(i){case 5126:return rg;case 35664:return ag;case 35665:return og;case 35666:return lg;case 35674:return cg;case 35675:return ug;case 35676:return hg;case 5124:case 35670:return dg;case 35667:case 35671:return fg;case 35668:case 35672:return pg;case 35669:case 35673:return mg;case 5125:return gg;case 36294:return _g;case 36295:return xg;case 36296:return vg;case 35678:case 36198:case 36298:case 36306:case 35682:return yg;case 35679:case 36299:case 36307:return Mg;case 35680:case 36300:case 36308:case 36293:return bg;case 36289:case 36303:case 36311:case 36292:return Sg}}function Eg(i,e){i.uniform1fv(this.addr,e)}function wg(i,e){let t=Bs(e,this.size,2);i.uniform2fv(this.addr,t)}function Ag(i,e){let t=Bs(e,this.size,3);i.uniform3fv(this.addr,t)}function Cg(i,e){let t=Bs(e,this.size,4);i.uniform4fv(this.addr,t)}function Rg(i,e){let t=Bs(e,this.size,4);i.uniformMatrix2fv(this.addr,!1,t)}function Pg(i,e){let t=Bs(e,this.size,9);i.uniformMatrix3fv(this.addr,!1,t)}function Ig(i,e){let t=Bs(e,this.size,16);i.uniformMatrix4fv(this.addr,!1,t)}function Lg(i,e){i.uniform1iv(this.addr,e)}function Ng(i,e){i.uniform2iv(this.addr,e)}function Dg(i,e){i.uniform3iv(this.addr,e)}function Ug(i,e){i.uniform4iv(this.addr,e)}function Fg(i,e){i.uniform1uiv(this.addr,e)}function kg(i,e){i.uniform2uiv(this.addr,e)}function Og(i,e){i.uniform3uiv(this.addr,e)}function Bg(i,e){i.uniform4uiv(this.addr,e)}function zg(i,e,t){let n=this.cache,s=e.length,r=rl(t,s);Wt(n,r)||(i.uniform1iv(this.addr,r),qt(n,r));let a;this.type===i.SAMPLER_2D_SHADOW?a=Sc:a=wh;for(let o=0;o!==s;++o)t.setTexture2D(e[o]||a,r[o])}function Vg(i,e,t){let n=this.cache,s=e.length,r=rl(t,s);Wt(n,r)||(i.uniform1iv(this.addr,r),qt(n,r));for(let a=0;a!==s;++a)t.setTexture3D(e[a]||Ch,r[a])}function Hg(i,e,t){let n=this.cache,s=e.length,r=rl(t,s);Wt(n,r)||(i.uniform1iv(this.addr,r),qt(n,r));for(let a=0;a!==s;++a)t.setTextureCube(e[a]||Rh,r[a])}function Gg(i,e,t){let n=this.cache,s=e.length,r=rl(t,s);Wt(n,r)||(i.uniform1iv(this.addr,r),qt(n,r));for(let a=0;a!==s;++a)t.setTexture2DArray(e[a]||Ah,r[a])}function Wg(i){switch(i){case 5126:return Eg;case 35664:return wg;case 35665:return Ag;case 35666:return Cg;case 35674:return Rg;case 35675:return Pg;case 35676:return Ig;case 5124:case 35670:return Lg;case 35667:case 35671:return Ng;case 35668:case 35672:return Dg;case 35669:case 35673:return Ug;case 5125:return Fg;case 36294:return kg;case 36295:return Og;case 36296:return Bg;case 35678:case 36198:case 36298:case 36306:case 35682:return zg;case 35679:case 36299:case 36307:return Vg;case 35680:case 36300:case 36308:case 36293:return Hg;case 36289:case 36303:case 36311:case 36292:return Gg}}var Tc=class{constructor(e,t,n){this.id=e,this.addr=n,this.cache=[],this.type=t.type,this.setValue=Tg(t.type)}},Ec=class{constructor(e,t,n){this.id=e,this.addr=n,this.cache=[],this.type=t.type,this.size=t.size,this.setValue=Wg(t.type)}},wc=class{constructor(e){this.id=e,this.seq=[],this.map={}}setValue(e,t,n){let s=this.seq;for(let r=0,a=s.length;r!==a;++r){let o=s[r];o.setValue(e,t[o.id],n)}}},Mc=/(\w+)(\])?(\[|\.)?/g;function dh(i,e){i.seq.push(e),i.map[e.id]=e}function qg(i,e,t){let n=i.name,s=n.length;for(Mc.lastIndex=0;;){let r=Mc.exec(n),a=Mc.lastIndex,o=r[1],l=r[2]==="]",c=r[3];if(l&&(o=o|0),c===void 0||c==="["&&a+2===s){dh(t,c===void 0?new Tc(o,i,e):new Ec(o,i,e));break}else{let f=t.map[o];f===void 0&&(f=new wc(o),dh(t,f)),t=f}}}var ks=class{constructor(e,t){this.seq=[],this.map={};let n=e.getProgramParameter(t,e.ACTIVE_UNIFORMS);for(let a=0;a<n;++a){let o=e.getActiveUniform(t,a),l=e.getUniformLocation(t,o.name);qg(o,l,this)}let s=[],r=[];for(let a of this.seq)a.type===e.SAMPLER_2D_SHADOW||a.type===e.SAMPLER_CUBE_SHADOW||a.type===e.SAMPLER_2D_ARRAY_SHADOW?s.push(a):r.push(a);s.length>0&&(this.seq=s.concat(r))}setValue(e,t,n,s){let r=this.map[t];r!==void 0&&r.setValue(e,n,s)}setOptional(e,t,n){let s=t[n];s!==void 0&&this.setValue(e,n,s)}static upload(e,t,n,s){for(let r=0,a=t.length;r!==a;++r){let o=t[r],l=n[o.id];l.needsUpdate!==!1&&o.setValue(e,l.value,s)}}static seqWithValue(e,t){let n=[];for(let s=0,r=e.length;s!==r;++s){let a=e[s];a.id in t&&n.push(a)}return n}};function fh(i,e,t){let n=i.createShader(e);return i.shaderSource(n,t),i.compileShader(n),n}var Xg=37297,$g=0;function Yg(i,e){let t=i.split(`
`),n=[],s=Math.max(e-6,0),r=Math.min(e+6,t.length);for(let a=s;a<r;a++){let o=a+1;n.push(`${o===e?">":" "} ${o}: ${t[a]}`)}return n.join(`
`)}var ph=new nt;function Zg(i){dt._getMatrix(ph,dt.workingColorSpace,i);let e=`mat3( ${ph.elements.map(t=>t.toFixed(4))} )`;switch(dt.getTransfer(i)){case sr:return[e,"LinearTransferOETF"];case bt:return[e,"sRGBTransferOETF"];default:return Je("WebGLProgram: Unsupported color space: ",i),[e,"LinearTransferOETF"]}}function mh(i,e,t){let n=i.getShaderParameter(e,i.COMPILE_STATUS),r=(i.getShaderInfoLog(e)||"").trim();if(n&&r==="")return"";let a=/ERROR: 0:(\d+)/.exec(r);if(a){let o=parseInt(a[1]);return t.toUpperCase()+`

`+r+`

`+Yg(i.getShaderSource(e),o)}else return r}function jg(i,e){let t=Zg(e);return[`vec4 ${i}( vec4 value ) {`,`	return ${t[1]}( vec4( value.rgb * ${t[0]}, value.a ) );`,"}"].join(`
`)}var Jg={[Pr]:"Linear",[Ir]:"Reinhard",[Lr]:"Cineon",[Xi]:"ACESFilmic",[Dr]:"AgX",[Ur]:"Neutral",[Nr]:"Custom"};function Kg(i,e){let t=Jg[e];return t===void 0?(Je("WebGLProgram: Unsupported toneMapping:",e),"vec3 "+i+"( vec3 color ) { return LinearToneMapping( color ); }"):"vec3 "+i+"( vec3 color ) { return "+t+"ToneMapping( color ); }"}var tl=new D;function Qg(){dt.getLuminanceCoefficients(tl);let i=tl.x.toFixed(4),e=tl.y.toFixed(4),t=tl.z.toFixed(4);return["float luminance( const in vec3 rgb ) {",`	const vec3 weights = vec3( ${i}, ${e}, ${t} );`,"	return dot( weights, rgb );","}"].join(`
`)}function e0(i){return[i.extensionClipCullDistance?"#extension GL_ANGLE_clip_cull_distance : require":"",i.extensionMultiDraw?"#extension GL_ANGLE_multi_draw : require":""].filter($r).join(`
`)}function t0(i){let e=[];for(let t in i){let n=i[t];n!==!1&&e.push("#define "+t+" "+n)}return e.join(`
`)}function n0(i,e){let t={},n=i.getProgramParameter(e,i.ACTIVE_ATTRIBUTES);for(let s=0;s<n;s++){let r=i.getActiveAttrib(e,s),a=r.name,o=1;r.type===i.FLOAT_MAT2&&(o=2),r.type===i.FLOAT_MAT3&&(o=3),r.type===i.FLOAT_MAT4&&(o=4),t[a]={type:r.type,location:i.getAttribLocation(e,a),locationSize:o}}return t}function $r(i){return i!==""}function gh(i,e){let t=e.numSpotLightShadows+e.numSpotLightMaps-e.numSpotLightShadowsWithMaps;return i.replace(/NUM_SUN_LIGHTS/g,e.numSunLights).replace(/NUM_DIR_LIGHTS/g,e.numDirLights).replace(/NUM_SPOT_LIGHTS/g,e.numSpotLights).replace(/NUM_SPOT_LIGHT_MAPS/g,e.numSpotLightMaps).replace(/NUM_SPOT_LIGHT_COORDS/g,t).replace(/NUM_RECT_AREA_LIGHTS/g,e.numRectAreaLights).replace(/NUM_POINT_LIGHTS/g,e.numPointLights).replace(/NUM_HEMI_LIGHTS/g,e.numHemiLights).replace(/NUM_SUN_LIGHT_SHADOWS/g,e.numSunLightShadows).replace(/NUM_DIR_LIGHT_SHADOWS/g,e.numDirLightShadows).replace(/NUM_SPOT_LIGHT_SHADOWS_WITH_MAPS/g,e.numSpotLightShadowsWithMaps).replace(/NUM_SPOT_LIGHT_SHADOWS/g,e.numSpotLightShadows).replace(/NUM_POINT_LIGHT_SHADOWS/g,e.numPointLightShadows)}function _h(i,e){return i.replace(/NUM_CLIPPING_PLANES/g,e.numClippingPlanes).replace(/UNION_CLIPPING_PLANES/g,e.numClippingPlanes-e.numClipIntersection)}var i0=/^[ \t]*#include +<([\w\d./]+)>/gm;function Ac(i){return i.replace(i0,r0)}var s0=new Map;function r0(i,e){let t=lt[e];if(t===void 0){let n=s0.get(e);if(n!==void 0)t=lt[n],Je('WebGLRenderer: Shader chunk "%s" has been deprecated. Use "%s" instead.',e,n);else throw new Error("THREE.WebGLProgram: Can not resolve #include <"+e+">")}return Ac(t)}var a0=/#pragma unroll_loop_start\s+for\s*\(\s*int\s+i\s*=\s*(\d+)\s*;\s*i\s*<\s*(\d+)\s*;\s*i\s*\+\+\s*\)\s*{([\s\S]+?)}\s+#pragma unroll_loop_end/g;function xh(i){return i.replace(a0,o0)}function o0(i,e,t,n){let s="";for(let r=parseInt(e);r<parseInt(t);r++)s+=n.replace(/\[\s*i\s*\]/g,"[ "+r+" ]").replace(/UNROLLED_LOOP_INDEX/g,r);return s}function vh(i){let e=`precision ${i.precision} float;
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
#define LOW_PRECISION`),e}var l0={[Rr]:"SHADOWMAP_TYPE_PCF",[Ps]:"SHADOWMAP_TYPE_VSM"};function c0(i){return l0[i.shadowMapType]||"SHADOWMAP_TYPE_BASIC"}var u0={[Ei]:"ENVMAP_TYPE_CUBE",[$i]:"ENVMAP_TYPE_CUBE",[Fr]:"ENVMAP_TYPE_CUBE_UV"};function h0(i){return i.envMap===!1?"ENVMAP_TYPE_CUBE":u0[i.envMapMode]||"ENVMAP_TYPE_CUBE"}var d0={[$i]:"ENVMAP_MODE_REFRACTION"};function f0(i){return i.envMap===!1?"ENVMAP_MODE_REFLECTION":d0[i.envMapMode]||"ENVMAP_MODE_REFLECTION"}var p0={[co]:"ENVMAP_BLENDING_MULTIPLY",[ku]:"ENVMAP_BLENDING_MIX",[Ou]:"ENVMAP_BLENDING_ADD"};function m0(i){return i.envMap===!1?"ENVMAP_BLENDING_NONE":p0[i.combine]||"ENVMAP_BLENDING_NONE"}function g0(i){let e=i.envMapCubeUVHeight;if(e===null)return null;let t=Math.log2(e)-2,n=1/e;return{texelWidth:1/(3*Math.max(Math.pow(2,t),112)),texelHeight:n,maxMip:t}}function _0(i,e,t,n){let s=i.getContext(),r=t.defines,a=t.vertexShader,o=t.fragmentShader,l=c0(t),c=h0(t),h=f0(t),f=m0(t),u=g0(t),d=e0(t),g=t0(r),M=s.createProgram(),m,p,T=t.glslVersion?"#version "+t.glslVersion+`
`:"";t.isRawShaderMaterial?(m=["#define SHADER_TYPE "+t.shaderType,"#define SHADER_NAME "+t.shaderName,g].filter($r).join(`
`),m.length>0&&(m+=`
`),p=["#define SHADER_TYPE "+t.shaderType,"#define SHADER_NAME "+t.shaderName,g].filter($r).join(`
`),p.length>0&&(p+=`
`)):(m=[vh(t),"#define SHADER_TYPE "+t.shaderType,"#define SHADER_NAME "+t.shaderName,g,t.extensionClipCullDistance?"#define USE_CLIP_DISTANCE":"",t.batching?"#define USE_BATCHING":"",t.batchingColor?"#define USE_BATCHING_COLOR":"",t.instancing?"#define USE_INSTANCING":"",t.instancingColor?"#define USE_INSTANCING_COLOR":"",t.instancingMorph?"#define USE_INSTANCING_MORPH":"",t.useFog&&t.fog?"#define USE_FOG":"",t.useFog&&t.fogExp2?"#define FOG_EXP2":"",t.map?"#define USE_MAP":"",t.envMap?"#define USE_ENVMAP":"",t.envMap?"#define "+h:"",t.lightMap?"#define USE_LIGHTMAP":"",t.aoMap?"#define USE_AOMAP":"",t.bumpMap?"#define USE_BUMPMAP":"",t.normalMap?"#define USE_NORMALMAP":"",t.normalMapObjectSpace?"#define USE_NORMALMAP_OBJECTSPACE":"",t.normalMapTangentSpace?"#define USE_NORMALMAP_TANGENTSPACE":"",t.displacementMap?"#define USE_DISPLACEMENTMAP":"",t.emissiveMap?"#define USE_EMISSIVEMAP":"",t.anisotropy?"#define USE_ANISOTROPY":"",t.anisotropyMap?"#define USE_ANISOTROPYMAP":"",t.clearcoatMap?"#define USE_CLEARCOATMAP":"",t.clearcoatRoughnessMap?"#define USE_CLEARCOAT_ROUGHNESSMAP":"",t.clearcoatNormalMap?"#define USE_CLEARCOAT_NORMALMAP":"",t.iridescenceMap?"#define USE_IRIDESCENCEMAP":"",t.iridescenceThicknessMap?"#define USE_IRIDESCENCE_THICKNESSMAP":"",t.specularMap?"#define USE_SPECULARMAP":"",t.specularColorMap?"#define USE_SPECULAR_COLORMAP":"",t.specularIntensityMap?"#define USE_SPECULAR_INTENSITYMAP":"",t.roughnessMap?"#define USE_ROUGHNESSMAP":"",t.metalnessMap?"#define USE_METALNESSMAP":"",t.alphaMap?"#define USE_ALPHAMAP":"",t.alphaHash?"#define USE_ALPHAHASH":"",t.transmission?"#define USE_TRANSMISSION":"",t.transmissionMap?"#define USE_TRANSMISSIONMAP":"",t.thicknessMap?"#define USE_THICKNESSMAP":"",t.sheenColorMap?"#define USE_SHEEN_COLORMAP":"",t.sheenRoughnessMap?"#define USE_SHEEN_ROUGHNESSMAP":"",t.mapUv?"#define MAP_UV "+t.mapUv:"",t.alphaMapUv?"#define ALPHAMAP_UV "+t.alphaMapUv:"",t.lightMapUv?"#define LIGHTMAP_UV "+t.lightMapUv:"",t.aoMapUv?"#define AOMAP_UV "+t.aoMapUv:"",t.emissiveMapUv?"#define EMISSIVEMAP_UV "+t.emissiveMapUv:"",t.bumpMapUv?"#define BUMPMAP_UV "+t.bumpMapUv:"",t.normalMapUv?"#define NORMALMAP_UV "+t.normalMapUv:"",t.displacementMapUv?"#define DISPLACEMENTMAP_UV "+t.displacementMapUv:"",t.metalnessMapUv?"#define METALNESSMAP_UV "+t.metalnessMapUv:"",t.roughnessMapUv?"#define ROUGHNESSMAP_UV "+t.roughnessMapUv:"",t.anisotropyMapUv?"#define ANISOTROPYMAP_UV "+t.anisotropyMapUv:"",t.clearcoatMapUv?"#define CLEARCOATMAP_UV "+t.clearcoatMapUv:"",t.clearcoatNormalMapUv?"#define CLEARCOAT_NORMALMAP_UV "+t.clearcoatNormalMapUv:"",t.clearcoatRoughnessMapUv?"#define CLEARCOAT_ROUGHNESSMAP_UV "+t.clearcoatRoughnessMapUv:"",t.iridescenceMapUv?"#define IRIDESCENCEMAP_UV "+t.iridescenceMapUv:"",t.iridescenceThicknessMapUv?"#define IRIDESCENCE_THICKNESSMAP_UV "+t.iridescenceThicknessMapUv:"",t.sheenColorMapUv?"#define SHEEN_COLORMAP_UV "+t.sheenColorMapUv:"",t.sheenRoughnessMapUv?"#define SHEEN_ROUGHNESSMAP_UV "+t.sheenRoughnessMapUv:"",t.specularMapUv?"#define SPECULARMAP_UV "+t.specularMapUv:"",t.specularColorMapUv?"#define SPECULAR_COLORMAP_UV "+t.specularColorMapUv:"",t.specularIntensityMapUv?"#define SPECULAR_INTENSITYMAP_UV "+t.specularIntensityMapUv:"",t.transmissionMapUv?"#define TRANSMISSIONMAP_UV "+t.transmissionMapUv:"",t.thicknessMapUv?"#define THICKNESSMAP_UV "+t.thicknessMapUv:"",t.vertexTangents&&t.flatShading===!1?"#define USE_TANGENT":"",t.vertexNormals?"#define HAS_NORMAL":"",t.vertexColors?"#define USE_COLOR":"",t.vertexAlphas?"#define USE_COLOR_ALPHA":"",t.vertexUv1s?"#define USE_UV1":"",t.vertexUv2s?"#define USE_UV2":"",t.vertexUv3s?"#define USE_UV3":"",t.pointsUvs?"#define USE_POINTS_UV":"",t.flatShading?"#define FLAT_SHADED":"",t.skinning?"#define USE_SKINNING":"",t.morphTargets?"#define USE_MORPHTARGETS":"",t.morphNormals&&t.flatShading===!1?"#define USE_MORPHNORMALS":"",t.morphColors?"#define USE_MORPHCOLORS":"",t.morphTargetsCount>0?"#define MORPHTARGETS_TEXTURE_STRIDE "+t.morphTextureStride:"",t.morphTargetsCount>0?"#define MORPHTARGETS_COUNT "+t.morphTargetsCount:"",t.doubleSided?"#define DOUBLE_SIDED":"",t.flipSided?"#define FLIP_SIDED":"",t.shadowMapEnabled?"#define USE_SHADOWMAP":"",t.shadowMapEnabled?"#define "+l:"",t.sizeAttenuation?"#define USE_SIZEATTENUATION":"",t.numLightProbes>0?"#define USE_LIGHT_PROBES":"",t.logarithmicDepthBuffer?"#define USE_LOGARITHMIC_DEPTH_BUFFER":"",t.reversedDepthBuffer?"#define USE_REVERSED_DEPTH_BUFFER":"","uniform mat4 modelMatrix;","uniform mat4 modelViewMatrix;","uniform mat4 projectionMatrix;","uniform mat4 viewMatrix;","uniform mat3 normalMatrix;","uniform vec3 cameraPosition;","uniform bool isOrthographic;","#ifdef USE_INSTANCING","	attribute mat4 instanceMatrix;","#endif","#ifdef USE_INSTANCING_COLOR","	attribute vec3 instanceColor;","#endif","#ifdef USE_INSTANCING_MORPH","	uniform sampler2D morphTexture;","#endif","attribute vec3 position;","attribute vec3 normal;","attribute vec2 uv;","#ifdef USE_UV1","	attribute vec2 uv1;","#endif","#ifdef USE_UV2","	attribute vec2 uv2;","#endif","#ifdef USE_UV3","	attribute vec2 uv3;","#endif","#ifdef USE_TANGENT","	attribute vec4 tangent;","#endif","#if defined( USE_COLOR_ALPHA )","	attribute vec4 color;","#elif defined( USE_COLOR )","	attribute vec3 color;","#endif","#ifdef USE_SKINNING","	attribute vec4 skinIndex;","	attribute vec4 skinWeight;","#endif",`
`].filter($r).join(`
`),p=[vh(t),"#define SHADER_TYPE "+t.shaderType,"#define SHADER_NAME "+t.shaderName,g,t.useFog&&t.fog?"#define USE_FOG":"",t.useFog&&t.fogExp2?"#define FOG_EXP2":"",t.alphaToCoverage?"#define ALPHA_TO_COVERAGE":"",t.map?"#define USE_MAP":"",t.matcap?"#define USE_MATCAP":"",t.envMap?"#define USE_ENVMAP":"",t.envMap?"#define "+c:"",t.envMap?"#define "+h:"",t.envMap?"#define "+f:"",u?"#define CUBEUV_TEXEL_WIDTH "+u.texelWidth:"",u?"#define CUBEUV_TEXEL_HEIGHT "+u.texelHeight:"",u?"#define CUBEUV_MAX_MIP "+u.maxMip+".0":"",t.lightMap?"#define USE_LIGHTMAP":"",t.aoMap?"#define USE_AOMAP":"",t.bumpMap?"#define USE_BUMPMAP":"",t.normalMap?"#define USE_NORMALMAP":"",t.normalMapObjectSpace?"#define USE_NORMALMAP_OBJECTSPACE":"",t.normalMapTangentSpace?"#define USE_NORMALMAP_TANGENTSPACE":"",t.packedNormalMap?"#define USE_PACKED_NORMALMAP":"",t.emissiveMap?"#define USE_EMISSIVEMAP":"",t.anisotropy?"#define USE_ANISOTROPY":"",t.anisotropyMap?"#define USE_ANISOTROPYMAP":"",t.clearcoat?"#define USE_CLEARCOAT":"",t.clearcoatMap?"#define USE_CLEARCOATMAP":"",t.clearcoatRoughnessMap?"#define USE_CLEARCOAT_ROUGHNESSMAP":"",t.clearcoatNormalMap?"#define USE_CLEARCOAT_NORMALMAP":"",t.dispersion?"#define USE_DISPERSION":"",t.retroreflection?"#define USE_RETROREFLECTION":"",t.iridescence?"#define USE_IRIDESCENCE":"",t.iridescenceMap?"#define USE_IRIDESCENCEMAP":"",t.iridescenceThicknessMap?"#define USE_IRIDESCENCE_THICKNESSMAP":"",t.specularMap?"#define USE_SPECULARMAP":"",t.specularColorMap?"#define USE_SPECULAR_COLORMAP":"",t.specularIntensityMap?"#define USE_SPECULAR_INTENSITYMAP":"",t.roughnessMap?"#define USE_ROUGHNESSMAP":"",t.metalnessMap?"#define USE_METALNESSMAP":"",t.alphaMap?"#define USE_ALPHAMAP":"",t.alphaTest?"#define USE_ALPHATEST":"",t.alphaHash?"#define USE_ALPHAHASH":"",t.sheen?"#define USE_SHEEN":"",t.sheenColorMap?"#define USE_SHEEN_COLORMAP":"",t.sheenRoughnessMap?"#define USE_SHEEN_ROUGHNESSMAP":"",t.transmission?"#define USE_TRANSMISSION":"",t.transmissionMap?"#define USE_TRANSMISSIONMAP":"",t.thicknessMap?"#define USE_THICKNESSMAP":"",t.vertexTangents&&t.flatShading===!1?"#define USE_TANGENT":"",t.vertexColors||t.instancingColor?"#define USE_COLOR":"",t.vertexAlphas||t.batchingColor?"#define USE_COLOR_ALPHA":"",t.vertexUv1s?"#define USE_UV1":"",t.vertexUv2s?"#define USE_UV2":"",t.vertexUv3s?"#define USE_UV3":"",t.pointsUvs?"#define USE_POINTS_UV":"",t.gradientMap?"#define USE_GRADIENTMAP":"",t.flatShading?"#define FLAT_SHADED":"",t.doubleSided?"#define DOUBLE_SIDED":"",t.flipSided?"#define FLIP_SIDED":"",t.shadowMapEnabled?"#define USE_SHADOWMAP":"",t.shadowMapEnabled?"#define "+l:"",t.premultipliedAlpha?"#define PREMULTIPLIED_ALPHA":"",t.numLightProbes>0?"#define USE_LIGHT_PROBES":"",t.numLightProbeGrids>0?"#define USE_LIGHT_PROBES_GRID":"",t.decodeVideoTexture?"#define DECODE_VIDEO_TEXTURE":"",t.decodeVideoTextureEmissive?"#define DECODE_VIDEO_TEXTURE_EMISSIVE":"",t.logarithmicDepthBuffer?"#define USE_LOGARITHMIC_DEPTH_BUFFER":"",t.reversedDepthBuffer?"#define USE_REVERSED_DEPTH_BUFFER":"","uniform mat4 viewMatrix;","uniform vec3 cameraPosition;","uniform bool isOrthographic;",t.toneMapping!==On?"#define TONE_MAPPING":"",t.toneMapping!==On?lt.tonemapping_pars_fragment:"",t.toneMapping!==On?Kg("toneMapping",t.toneMapping):"",t.dithering?"#define DITHERING":"",t.opaque?"#define OPAQUE":"",lt.colorspace_pars_fragment,jg("linearToOutputTexel",t.outputColorSpace),Qg(),t.useDepthPacking?"#define DEPTH_PACKING "+t.depthPacking:"",`
`].filter($r).join(`
`)),a=Ac(a),a=gh(a,t),a=_h(a,t),o=Ac(o),o=gh(o,t),o=_h(o,t),a=xh(a),o=xh(o),t.isRawShaderMaterial!==!0&&(T=`#version 300 es
`,m=[d,"#define attribute in","#define varying out","#define texture2D texture"].join(`
`)+`
`+m,p=["#define varying in",t.glslVersion===cc?"":"layout(location = 0) out highp vec4 pc_fragColor;",t.glslVersion===cc?"":"#define gl_FragColor pc_fragColor","#define gl_FragDepthEXT gl_FragDepth","#define texture2D texture","#define textureCube texture","#define texture2DProj textureProj","#define texture2DLodEXT textureLod","#define texture2DProjLodEXT textureProjLod","#define textureCubeLodEXT textureLod","#define texture2DGradEXT textureGrad","#define texture2DProjGradEXT textureProjGrad","#define textureCubeGradEXT textureGrad"].join(`
`)+`
`+p);let C=T+m+a,v=T+p+o,w=fh(s,s.VERTEX_SHADER,C),S=fh(s,s.FRAGMENT_SHADER,v);s.attachShader(M,w),s.attachShader(M,S),t.index0AttributeName!==void 0?s.bindAttribLocation(M,0,t.index0AttributeName):t.hasPositionAttribute===!0&&s.bindAttribLocation(M,0,"position"),s.linkProgram(M);function I(k){if(i.debug.checkShaderErrors){let V=s.getProgramInfoLog(M)||"",$=s.getShaderInfoLog(w)||"",U=s.getShaderInfoLog(S)||"",W=V.trim(),ee=$.trim(),ie=U.trim(),Z=!0,Q=!0;if(s.getProgramParameter(M,s.LINK_STATUS)===!1)if(Z=!1,typeof i.debug.onShaderError=="function")i.debug.onShaderError(s,M,w,S);else{let ue=mh(s,w,"vertex"),se=mh(s,S,"fragment");et("WebGLProgram: Shader Error "+s.getError()+" - VALIDATE_STATUS "+s.getProgramParameter(M,s.VALIDATE_STATUS)+`

Material Name: `+k.name+`
Material Type: `+k.type+`

Program Info Log: `+W+`
`+ue+`
`+se)}else W!==""?Je("WebGLProgram: Program Info Log:",W):(ee===""||ie==="")&&(Q=!1);Q&&(k.diagnostics={runnable:Z,programLog:W,vertexShader:{log:ee,prefix:m},fragmentShader:{log:ie,prefix:p}})}s.deleteShader(w),s.deleteShader(S),x=new ks(s,M),A=n0(s,M)}let x;this.getUniforms=function(){return x===void 0&&I(this),x};let A;this.getAttributes=function(){return A===void 0&&I(this),A};let N=t.rendererExtensionParallelShaderCompile===!1;return this.isReady=function(){return N===!1&&(N=s.getProgramParameter(M,Xg)),N},this.destroy=function(){n.releaseStatesOfProgram(this),s.deleteProgram(M),this.program=void 0},this.type=t.shaderType,this.name=t.shaderName,this.id=$g++,this.cacheKey=e,this.usedTimes=1,this.program=M,this.vertexShader=w,this.fragmentShader=S,this}var x0=0,Cc=class{constructor(){this.shaderCache=new Map,this.materialCache=new Map}update(e,t,n){let s=this._getShaderCacheForMaterial(e);return s.has(t)===!1&&(s.add(t),t.usedTimes++),s.has(n)===!1&&(s.add(n),n.usedTimes++),this}remove(e){let t=this.materialCache.get(e);for(let n of t)n.usedTimes--,n.usedTimes===0&&this.shaderCache.delete(n.code);return this.materialCache.delete(e),this}getVertexShaderStage(e){return this._getShaderStage(e.vertexShader)}getFragmentShaderStage(e){return this._getShaderStage(e.fragmentShader)}dispose(){this.shaderCache.clear(),this.materialCache.clear()}_getShaderCacheForMaterial(e){let t=this.materialCache,n=t.get(e);return n===void 0&&(n=new Set,t.set(e,n)),n}_getShaderStage(e){let t=this.shaderCache,n=t.get(e);return n===void 0&&(n=new Rc(e),t.set(e,n)),n}},Rc=class{constructor(e){this.id=x0++,this.code=e,this.usedTimes=0}};function v0(i){return i===Ci||i===Hr||i===Gr}function y0(i,e,t,n,s,r){let a=new Ms,o=new Cc,l=new Set,c=[],h=new Map,f=n.logarithmicDepthBuffer,u=n.precision,d={MeshDepthMaterial:"depth",MeshDistanceMaterial:"distance",MeshNormalMaterial:"normal",MeshBasicMaterial:"basic",MeshLambertMaterial:"lambert",MeshPhongMaterial:"phong",MeshToonMaterial:"toon",MeshStandardMaterial:"physical",MeshPhysicalMaterial:"physical",MeshMatcapMaterial:"matcap",LineBasicMaterial:"basic",LineDashedMaterial:"dashed",PointsMaterial:"points",ShadowMaterial:"shadow",SpriteMaterial:"sprite"};function g(x){return l.add(x),x===0?"uv":`uv${x}`}function M(x,A,N,k,V,$){let U=k.fog,W=V.geometry,ee=x.isMeshStandardMaterial||x.isMeshLambertMaterial||x.isMeshPhongMaterial?k.environment:null,ie=x.isMeshStandardMaterial||x.isMeshLambertMaterial&&!x.envMap||x.isMeshPhongMaterial&&!x.envMap,Z=e.get(x.envMap||ee,ie),Q=Z&&Z.mapping===Fr?Z.image.height:null,ue=d[x.type];x.precision!==null&&(u=n.getMaxPrecision(x.precision),u!==x.precision&&Je("WebGLProgram.getParameters:",x.precision,"not supported, using",u,"instead."));let se=W.morphAttributes.position||W.morphAttributes.normal||W.morphAttributes.color,Ge=se!==void 0?se.length:0,Pe=0;W.morphAttributes.position!==void 0&&(Pe=1),W.morphAttributes.normal!==void 0&&(Pe=2),W.morphAttributes.color!==void 0&&(Pe=3);let ot,$e,Xe,K;if(ue){let St=jn[ue];ot=St.vertexShader,$e=St.fragmentShader}else{ot=x.vertexShader,$e=x.fragmentShader;let St=o.getVertexShaderStage(x),mt=o.getFragmentShaderStage(x);o.update(x,St,mt),Xe=St.id,K=mt.id}let re=i.getRenderTarget(),Se=i.state.buffers.depth.getReversed(),Le=V.isInstancedMesh===!0,Ie=V.isBatchedMesh===!0,Ze=!!x.map,ht=!!x.matcap,st=!!Z,it=!!x.aoMap,Qe=!!x.lightMap,rt=!!x.bumpMap&&x.wireframe===!1,gt=!!x.normalMap,Ct=!!x.displacementMap,Ut=!!x.emissiveMap,_t=!!x.metalnessMap,Et=!!x.roughnessMap,B=x.anisotropy>0,wt=x.clearcoat>0,ct=x.dispersion>0,P=x.retroreflectivity>0,_=x.iridescence>0,G=x.sheen>0,j=x.transmission>0,oe=B&&!!x.anisotropyMap,Me=wt&&!!x.clearcoatMap,Ee=wt&&!!x.clearcoatNormalMap,L=wt&&!!x.clearcoatRoughnessMap,z=_&&!!x.iridescenceMap,ne=_&&!!x.iridescenceThicknessMap,_e=G&&!!x.sheenColorMap,ce=G&&!!x.sheenRoughnessMap,pe=!!x.specularMap,ye=!!x.specularColorMap,we=!!x.specularIntensityMap,ke=j&&!!x.transmissionMap,O=j&&!!x.thicknessMap,Te=!!x.gradientMap,Y=!!x.alphaMap,be=x.alphaTest>0,Ae=!!x.alphaHash,de=!!x.extensions,Ve=On;x.toneMapped&&(re===null||re.isXRRenderTarget===!0)&&(Ve=i.toneMapping);let ze={shaderID:ue,shaderType:x.type,shaderName:x.name,vertexShader:ot,fragmentShader:$e,defines:x.defines,customVertexShaderID:Xe,customFragmentShaderID:K,isRawShaderMaterial:x.isRawShaderMaterial===!0,glslVersion:x.glslVersion,precision:u,batching:Ie,batchingColor:Ie&&V._colorsTexture!==null,instancing:Le,instancingColor:Le&&V.instanceColor!==null,instancingMorph:Le&&V.morphTexture!==null,outputColorSpace:re===null?i.outputColorSpace:re.isXRRenderTarget===!0?re.texture.colorSpace:dt.workingColorSpace,alphaToCoverage:!!x.alphaToCoverage,map:Ze,matcap:ht,envMap:st,envMapMode:st&&Z.mapping,envMapCubeUVHeight:Q,aoMap:it,lightMap:Qe,bumpMap:rt,normalMap:gt,displacementMap:Ct,emissiveMap:Ut,normalMapObjectSpace:gt&&x.normalMapType===Vu,normalMapTangentSpace:gt&&x.normalMapType===Wr,packedNormalMap:gt&&x.normalMapType===Wr&&v0(x.normalMap.format),metalnessMap:_t,roughnessMap:Et,anisotropy:B,anisotropyMap:oe,clearcoat:wt,clearcoatMap:Me,clearcoatNormalMap:Ee,clearcoatRoughnessMap:L,dispersion:ct,retroreflection:P,iridescence:_,iridescenceMap:z,iridescenceThicknessMap:ne,sheen:G,sheenColorMap:_e,sheenRoughnessMap:ce,specularMap:pe,specularColorMap:ye,specularIntensityMap:we,transmission:j,transmissionMap:ke,thicknessMap:O,gradientMap:Te,opaque:x.transparent===!1&&x.blending===Is&&x.alphaToCoverage===!1,alphaMap:Y,alphaTest:be,alphaHash:Ae,combine:x.combine,mapUv:Ze&&g(x.map.channel),aoMapUv:it&&g(x.aoMap.channel),lightMapUv:Qe&&g(x.lightMap.channel),bumpMapUv:rt&&g(x.bumpMap.channel),normalMapUv:gt&&g(x.normalMap.channel),displacementMapUv:Ct&&g(x.displacementMap.channel),emissiveMapUv:Ut&&g(x.emissiveMap.channel),metalnessMapUv:_t&&g(x.metalnessMap.channel),roughnessMapUv:Et&&g(x.roughnessMap.channel),anisotropyMapUv:oe&&g(x.anisotropyMap.channel),clearcoatMapUv:Me&&g(x.clearcoatMap.channel),clearcoatNormalMapUv:Ee&&g(x.clearcoatNormalMap.channel),clearcoatRoughnessMapUv:L&&g(x.clearcoatRoughnessMap.channel),iridescenceMapUv:z&&g(x.iridescenceMap.channel),iridescenceThicknessMapUv:ne&&g(x.iridescenceThicknessMap.channel),sheenColorMapUv:_e&&g(x.sheenColorMap.channel),sheenRoughnessMapUv:ce&&g(x.sheenRoughnessMap.channel),specularMapUv:pe&&g(x.specularMap.channel),specularColorMapUv:ye&&g(x.specularColorMap.channel),specularIntensityMapUv:we&&g(x.specularIntensityMap.channel),transmissionMapUv:ke&&g(x.transmissionMap.channel),thicknessMapUv:O&&g(x.thicknessMap.channel),alphaMapUv:Y&&g(x.alphaMap.channel),vertexTangents:!!W.attributes.tangent&&(gt||B),vertexNormals:!!W.attributes.normal,vertexColors:x.vertexColors,vertexAlphas:x.vertexColors===!0&&!!W.attributes.color&&W.attributes.color.itemSize===4,pointsUvs:V.isPoints===!0&&!!W.attributes.uv&&(Ze||Y),fog:!!U,useFog:x.fog===!0,fogExp2:!!U&&U.isFogExp2,flatShading:x.wireframe===!1&&(x.flatShading===!0||W.attributes.normal===void 0&&gt===!1&&(x.isMeshLambertMaterial||x.isMeshPhongMaterial||x.isMeshStandardMaterial||x.isMeshPhysicalMaterial)),sizeAttenuation:x.sizeAttenuation===!0,logarithmicDepthBuffer:f,reversedDepthBuffer:Se,skinning:V.isSkinnedMesh===!0,hasPositionAttribute:W.attributes.position!==void 0,morphTargets:W.morphAttributes.position!==void 0,morphNormals:W.morphAttributes.normal!==void 0,morphColors:W.morphAttributes.color!==void 0,morphTargetsCount:Ge,morphTextureStride:Pe,numSunLights:A.sun.length,numDirLights:A.directional.length,numPointLights:A.point.length,numSpotLights:A.spot.length,numSpotLightMaps:A.spotLightMap.length,numRectAreaLights:A.rectArea.length,numHemiLights:A.hemi.length,numSunLightShadows:A.sunShadowMap.length,numDirLightShadows:A.directionalShadowMap.length,numPointLightShadows:A.pointShadowMap.length,numSpotLightShadows:A.spotShadowMap.length,numSpotLightShadowsWithMaps:A.numSpotLightShadowsWithMaps,numLightProbes:A.numLightProbes,numLightProbeGrids:$.length,numClippingPlanes:r.numPlanes,numClipIntersection:r.numIntersection,dithering:x.dithering,shadowMapEnabled:i.shadowMap.enabled&&N.length>0,shadowMapType:i.shadowMap.type,toneMapping:Ve,decodeVideoTexture:Ze&&x.map.isVideoTexture===!0&&dt.getTransfer(x.map.colorSpace)===bt,decodeVideoTextureEmissive:Ut&&x.emissiveMap.isVideoTexture===!0&&dt.getTransfer(x.emissiveMap.colorSpace)===bt,premultipliedAlpha:x.premultipliedAlpha,doubleSided:x.side===Yn,flipSided:x.side===en,useDepthPacking:x.depthPacking>=0,depthPacking:x.depthPacking||0,index0AttributeName:x.index0AttributeName,extensionClipCullDistance:de&&x.extensions.clipCullDistance===!0&&t.has("WEBGL_clip_cull_distance"),extensionMultiDraw:(de&&x.extensions.multiDraw===!0||Ie)&&t.has("WEBGL_multi_draw"),rendererExtensionParallelShaderCompile:t.has("KHR_parallel_shader_compile"),customProgramCacheKey:x.customProgramCacheKey()};return ze.vertexUv1s=l.has(1),ze.vertexUv2s=l.has(2),ze.vertexUv3s=l.has(3),l.clear(),ze}function m(x){let A=[];if(x.shaderID?A.push(x.shaderID):(A.push(x.customVertexShaderID),A.push(x.customFragmentShaderID)),x.defines!==void 0)for(let N in x.defines)A.push(N),A.push(x.defines[N]);return x.isRawShaderMaterial===!1&&(p(A,x),T(A,x),A.push(i.outputColorSpace)),A.push(x.customProgramCacheKey),A.join()}function p(x,A){x.push(A.precision),x.push(A.outputColorSpace),x.push(A.envMapMode),x.push(A.envMapCubeUVHeight),x.push(A.mapUv),x.push(A.alphaMapUv),x.push(A.lightMapUv),x.push(A.aoMapUv),x.push(A.bumpMapUv),x.push(A.normalMapUv),x.push(A.displacementMapUv),x.push(A.emissiveMapUv),x.push(A.metalnessMapUv),x.push(A.roughnessMapUv),x.push(A.anisotropyMapUv),x.push(A.clearcoatMapUv),x.push(A.clearcoatNormalMapUv),x.push(A.clearcoatRoughnessMapUv),x.push(A.iridescenceMapUv),x.push(A.iridescenceThicknessMapUv),x.push(A.sheenColorMapUv),x.push(A.sheenRoughnessMapUv),x.push(A.specularMapUv),x.push(A.specularColorMapUv),x.push(A.specularIntensityMapUv),x.push(A.transmissionMapUv),x.push(A.thicknessMapUv),x.push(A.combine),x.push(A.fogExp2),x.push(A.sizeAttenuation),x.push(A.morphTargetsCount),x.push(A.morphAttributeCount),x.push(A.numSunLights),x.push(A.numDirLights),x.push(A.numPointLights),x.push(A.numSpotLights),x.push(A.numSpotLightMaps),x.push(A.numHemiLights),x.push(A.numRectAreaLights),x.push(A.numSunLightShadows),x.push(A.numDirLightShadows),x.push(A.numPointLightShadows),x.push(A.numSpotLightShadows),x.push(A.numSpotLightShadowsWithMaps),x.push(A.numLightProbes),x.push(A.shadowMapType),x.push(A.toneMapping),x.push(A.numClippingPlanes),x.push(A.numClipIntersection),x.push(A.depthPacking)}function T(x,A){a.disableAll(),A.instancing&&a.enable(0),A.instancingColor&&a.enable(1),A.instancingMorph&&a.enable(2),A.matcap&&a.enable(3),A.envMap&&a.enable(4),A.normalMapObjectSpace&&a.enable(5),A.normalMapTangentSpace&&a.enable(6),A.clearcoat&&a.enable(7),A.iridescence&&a.enable(8),A.alphaTest&&a.enable(9),A.vertexColors&&a.enable(10),A.vertexAlphas&&a.enable(11),A.vertexUv1s&&a.enable(12),A.vertexUv2s&&a.enable(13),A.vertexUv3s&&a.enable(14),A.vertexTangents&&a.enable(15),A.anisotropy&&a.enable(16),A.alphaHash&&a.enable(17),A.batching&&a.enable(18),A.dispersion&&a.enable(19),A.retroreflection&&a.enable(24),A.batchingColor&&a.enable(20),A.gradientMap&&a.enable(21),A.packedNormalMap&&a.enable(22),A.vertexNormals&&a.enable(23),x.push(a.mask),a.disableAll(),A.fog&&a.enable(0),A.useFog&&a.enable(1),A.flatShading&&a.enable(2),A.logarithmicDepthBuffer&&a.enable(3),A.reversedDepthBuffer&&a.enable(4),A.skinning&&a.enable(5),A.morphTargets&&a.enable(6),A.morphNormals&&a.enable(7),A.morphColors&&a.enable(8),A.premultipliedAlpha&&a.enable(9),A.shadowMapEnabled&&a.enable(10),A.doubleSided&&a.enable(11),A.flipSided&&a.enable(12),A.useDepthPacking&&a.enable(13),A.dithering&&a.enable(14),A.transmission&&a.enable(15),A.sheen&&a.enable(16),A.opaque&&a.enable(17),A.pointsUvs&&a.enable(18),A.decodeVideoTexture&&a.enable(19),A.decodeVideoTextureEmissive&&a.enable(20),A.alphaToCoverage&&a.enable(21),A.numLightProbeGrids>0&&a.enable(22),A.hasPositionAttribute&&a.enable(23),x.push(a.mask)}function C(x){let A=d[x.type],N;if(A){let k=jn[A];N=li.clone(k.uniforms)}else N=x.uniforms;return N}function v(x,A){let N=h.get(A);return N!==void 0?++N.usedTimes:(N=new _0(i,A,x,s),c.push(N),h.set(A,N)),N}function w(x){if(--x.usedTimes===0){let A=c.indexOf(x);c[A]=c[c.length-1],c.pop(),h.delete(x.cacheKey),x.destroy()}}function S(x){o.remove(x)}function I(){o.dispose()}return{getParameters:M,getProgramCacheKey:m,getUniforms:C,acquireProgram:v,releaseProgram:w,releaseShaderCache:S,programs:c,dispose:I}}function M0(){let i=new WeakMap;function e(a){return i.has(a)}function t(a){let o=i.get(a);return o===void 0&&(o={},i.set(a,o)),o}function n(a){i.delete(a)}function s(a,o,l){i.get(a)[o]=l}function r(){i=new WeakMap}return{has:e,get:t,remove:n,update:s,dispose:r}}function b0(i,e){return i.groupOrder!==e.groupOrder?i.groupOrder-e.groupOrder:i.renderOrder!==e.renderOrder?i.renderOrder-e.renderOrder:i.material.id!==e.material.id?i.material.id-e.material.id:i.materialVariant!==e.materialVariant?i.materialVariant-e.materialVariant:i.z!==e.z?i.z-e.z:i.id-e.id}function yh(i,e){return i.groupOrder!==e.groupOrder?i.groupOrder-e.groupOrder:i.renderOrder!==e.renderOrder?i.renderOrder-e.renderOrder:i.z!==e.z?e.z-i.z:i.id-e.id}function Mh(){let i=[],e=0,t=[],n=[],s=[];function r(){e=0,t.length=0,n.length=0,s.length=0}function a(u){let d=0;return u.isInstancedMesh&&(d+=2),u.isSkinnedMesh&&(d+=1),d}function o(u,d,g,M,m,p){let T=i[e];return T===void 0?(T={id:u.id,object:u,geometry:d,material:g,materialVariant:a(u),groupOrder:M,renderOrder:u.renderOrder,z:m,group:p},i[e]=T):(T.id=u.id,T.object=u,T.geometry=d,T.material=g,T.materialVariant=a(u),T.groupOrder=M,T.renderOrder=u.renderOrder,T.z=m,T.group=p),e++,T}function l(u,d,g,M,m,p,T){T.reversedDepth===!0&&(m=-m);let C=o(u,d,g,M,m,p);g.transmission>0?n.push(C):g.transparent===!0?s.push(C):t.push(C)}function c(u,d,g,M,m,p){let T=o(u,d,g,M,m,p);g.transmission>0?n.unshift(T):g.transparent===!0?s.unshift(T):t.unshift(T)}function h(u,d){t.length>1&&t.sort(u||b0),n.length>1&&n.sort(d||yh),s.length>1&&s.sort(d||yh)}function f(){for(let u=e,d=i.length;u<d;u++){let g=i[u];if(g.id===null)break;g.id=null,g.object=null,g.geometry=null,g.material=null,g.group=null}}return{opaque:t,transmissive:n,transparent:s,init:r,push:l,unshift:c,finish:f,sort:h}}function S0(){let i=new WeakMap;function e(n,s){let r=i.get(n),a;return r===void 0?(a=new Mh,i.set(n,[a])):s>=r.length?(a=new Mh,r.push(a)):a=r[s],a}function t(){i=new WeakMap}return{get:e,dispose:t}}function T0(){let i={};return{get:function(e){if(i[e.id]!==void 0)return i[e.id];let t;switch(e.type){case"SunLight":case"DirectionalLight":t={direction:new D,color:new Ke};break;case"SpotLight":t={position:new D,direction:new D,color:new Ke,distance:0,coneCos:0,penumbraCos:0,decay:0};break;case"PointLight":t={position:new D,color:new Ke,distance:0,decay:0};break;case"HemisphereLight":t={direction:new D,skyColor:new Ke,groundColor:new Ke};break;case"RectAreaLight":t={color:new Ke,position:new D,halfWidth:new D,halfHeight:new D};break}return i[e.id]=t,t}}}function E0(){let i={};return{get:function(e){if(i[e.id]!==void 0)return i[e.id];let t;switch(e.type){case"SunLight":case"DirectionalLight":t={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new Ue};break;case"SpotLight":t={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new Ue};break;case"PointLight":t={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new Ue,shadowCameraNear:1,shadowCameraFar:1e3};break}return i[e.id]=t,t}}}var w0=0;function A0(i,e){return(e.castShadow?2:0)-(i.castShadow?2:0)+(e.map?1:0)-(i.map?1:0)}function C0(i){let e=new T0,t=E0(),n={version:0,hash:{sunLength:-1,directionalLength:-1,pointLength:-1,spotLength:-1,rectAreaLength:-1,hemiLength:-1,numSunShadows:-1,numDirectionalShadows:-1,numPointShadows:-1,numSpotShadows:-1,numSpotMaps:-1,numLightProbes:-1},ambient:[0,0,0],probe:[],sun:[],sunShadow:[],sunShadowMap:[],sunShadowMatrix:[],sunShadowCascade:[],directional:[],directionalShadow:[],directionalShadowMap:[],directionalShadowMatrix:[],spot:[],spotLightMap:[],spotShadow:[],spotShadowMap:[],spotLightMatrix:[],rectArea:[],rectAreaLTC1:null,rectAreaLTC2:null,point:[],pointShadow:[],pointShadowMap:[],pointShadowMatrix:[],hemi:[],numSpotLightShadowsWithMaps:0,numLightProbes:0};for(let c=0;c<9;c++)n.probe.push(new D);let s=new D,r=new pt,a=new pt;function o(c){let h=0,f=0,u=0;for(let V=0;V<9;V++)n.probe[V].set(0,0,0);let d=0,g=0,M=0,m=0,p=0,T=0,C=0,v=0,w=0,S=0,I=0,x=0,A=0,N=0;c.sort(A0);for(let V=0,$=c.length;V<$;V++){let U=c[V],W=U.color,ee=U.intensity,ie=U.distance,Z=null;if(U.shadow&&U.shadow.map&&(U.shadow.map.texture.format===Ci?Z=U.shadow.map.texture:Z=U.shadow.map.depthTexture||U.shadow.map.texture),U.isAmbientLight)h+=W.r*ee,f+=W.g*ee,u+=W.b*ee;else if(U.isLightProbe){for(let Q=0;Q<9;Q++)n.probe[Q].addScaledVector(U.sh.coefficients[Q],ee);N++}else if(U.isSunLight){let Q=e.get(U);if(Q.color.copy(U.color).multiplyScalar(U.intensity),U.castShadow){let ue=U.shadow,se=t.get(U);se.shadowIntensity=ue.intensity,se.shadowBias=ue.bias,se.shadowNormalBias=ue.normalBias,se.shadowRadius=ue.radius,se.shadowMapSize.copy(ue.mapSize).multiply(ue.getFrameExtents()),n.sunShadow[g]=se,n.sunShadowMap[g]=Z;let Ge=ue.getViewportCount();for(let Pe=0;Pe<Ge;Pe++)n.sunShadowMatrix[M+Pe]=ue.getMatrix(Pe),n.sunShadowCascade[M+Pe]=ue._cascadeData[Pe];M+=Ge,g++}n.sun[d]=Q,d++}else if(U.isDirectionalLight){let Q=e.get(U);if(Q.color.copy(U.color).multiplyScalar(U.intensity),U.castShadow){let ue=U.shadow,se=t.get(U);se.shadowIntensity=ue.intensity,se.shadowBias=ue.bias,se.shadowNormalBias=ue.normalBias,se.shadowRadius=ue.radius,se.shadowMapSize=ue.mapSize,n.directionalShadow[m]=se,n.directionalShadowMap[m]=Z,n.directionalShadowMatrix[m]=U.shadow.matrix,w++}n.directional[m]=Q,m++}else if(U.isSpotLight){let Q=e.get(U);Q.position.setFromMatrixPosition(U.matrixWorld),Q.color.copy(W).multiplyScalar(ee),Q.distance=ie,Q.coneCos=Math.cos(U.angle),Q.penumbraCos=Math.cos(U.angle*(1-U.penumbra)),Q.decay=U.decay,n.spot[T]=Q;let ue=U.shadow;if(U.map&&(n.spotLightMap[x]=U.map,x++,ue.updateMatrices(U),U.castShadow&&A++),n.spotLightMatrix[T]=ue.matrix,U.castShadow){let se=t.get(U);se.shadowIntensity=ue.intensity,se.shadowBias=ue.bias,se.shadowNormalBias=ue.normalBias,se.shadowRadius=ue.radius,se.shadowMapSize=ue.mapSize,n.spotShadow[T]=se,n.spotShadowMap[T]=Z,I++}T++}else if(U.isRectAreaLight){let Q=e.get(U);Q.color.copy(W).multiplyScalar(ee),Q.halfWidth.set(U.width*.5,0,0),Q.halfHeight.set(0,U.height*.5,0),n.rectArea[C]=Q,C++}else if(U.isPointLight){let Q=e.get(U);if(Q.color.copy(U.color).multiplyScalar(U.intensity),Q.distance=U.distance,Q.decay=U.decay,U.castShadow){let ue=U.shadow,se=t.get(U);se.shadowIntensity=ue.intensity,se.shadowBias=ue.bias,se.shadowNormalBias=ue.normalBias,se.shadowRadius=ue.radius,se.shadowMapSize=ue.mapSize,se.shadowCameraNear=ue.camera.near,se.shadowCameraFar=ue.camera.far,n.pointShadow[p]=se,n.pointShadowMap[p]=Z,n.pointShadowMatrix[p]=U.shadow.matrix,S++}n.point[p]=Q,p++}else if(U.isHemisphereLight){let Q=e.get(U);Q.skyColor.copy(U.color).multiplyScalar(ee),Q.groundColor.copy(U.groundColor).multiplyScalar(ee),n.hemi[v]=Q,v++}}C>0&&(i.has("OES_texture_float_linear")===!0?(n.rectAreaLTC1=De.LTC_FLOAT_1,n.rectAreaLTC2=De.LTC_FLOAT_2):(n.rectAreaLTC1=De.LTC_HALF_1,n.rectAreaLTC2=De.LTC_HALF_2)),n.ambient[0]=h,n.ambient[1]=f,n.ambient[2]=u;let k=n.hash;(k.sunLength!==d||k.directionalLength!==m||k.pointLength!==p||k.spotLength!==T||k.rectAreaLength!==C||k.hemiLength!==v||k.numSunShadows!==g||k.numDirectionalShadows!==w||k.numPointShadows!==S||k.numSpotShadows!==I||k.numSpotMaps!==x||k.numLightProbes!==N)&&(n.sun.length=d,n.directional.length=m,n.spot.length=T,n.rectArea.length=C,n.point.length=p,n.hemi.length=v,n.sunShadow.length=g,n.sunShadowMap.length=g,n.sunShadowMatrix.length=M,n.sunShadowCascade.length=M,n.directionalShadow.length=w,n.directionalShadowMap.length=w,n.directionalShadowMatrix.length=w,n.pointShadow.length=S,n.pointShadowMap.length=S,n.pointShadowMatrix.length=S,n.spotShadow.length=I,n.spotShadowMap.length=I,n.spotLightMatrix.length=I+x-A,n.spotLightMap.length=x,n.numSpotLightShadowsWithMaps=A,n.numLightProbes=N,k.sunLength=d,k.directionalLength=m,k.pointLength=p,k.spotLength=T,k.rectAreaLength=C,k.hemiLength=v,k.numSunShadows=g,k.numDirectionalShadows=w,k.numPointShadows=S,k.numSpotShadows=I,k.numSpotMaps=x,k.numLightProbes=N,n.version=w0++)}function l(c,h){let f=0,u=0,d=0,g=0,M=0,m=0,p=h.matrixWorldInverse;for(let T=0,C=c.length;T<C;T++){let v=c[T];if(v.isSunLight){let w=n.sun[f];w.direction.setFromMatrixPosition(v.matrixWorld),w.direction.transformDirection(p),f++}else if(v.isDirectionalLight){let w=n.directional[u];w.direction.setFromMatrixPosition(v.matrixWorld),s.setFromMatrixPosition(v.target.matrixWorld),w.direction.sub(s),w.direction.transformDirection(p),u++}else if(v.isSpotLight){let w=n.spot[g];w.position.setFromMatrixPosition(v.matrixWorld),w.position.applyMatrix4(p),w.direction.setFromMatrixPosition(v.matrixWorld),s.setFromMatrixPosition(v.target.matrixWorld),w.direction.sub(s),w.direction.transformDirection(p),g++}else if(v.isRectAreaLight){let w=n.rectArea[M];w.position.setFromMatrixPosition(v.matrixWorld),w.position.applyMatrix4(p),a.identity(),r.copy(v.matrixWorld),r.premultiply(p),a.extractRotation(r),w.halfWidth.set(v.width*.5,0,0),w.halfHeight.set(0,v.height*.5,0),w.halfWidth.applyMatrix4(a),w.halfHeight.applyMatrix4(a),M++}else if(v.isPointLight){let w=n.point[d];w.position.setFromMatrixPosition(v.matrixWorld),w.position.applyMatrix4(p),d++}else if(v.isHemisphereLight){let w=n.hemi[m];w.direction.setFromMatrixPosition(v.matrixWorld),w.direction.transformDirection(p),m++}}}return{setup:o,setupView:l,state:n}}function bh(i){let e=new C0(i),t=[],n=[],s=[];function r(u){f.camera=u,t.length=0,n.length=0,s.length=0}function a(u){t.push(u)}function o(u){n.push(u)}function l(u){s.push(u)}function c(){e.setup(t)}function h(u){e.setupView(t,u)}let f={lightsArray:t,shadowsArray:n,lightProbeGridArray:s,camera:null,lights:e,transmissionRenderTarget:{},textureUnits:0};return{init:r,state:f,setupLights:c,setupLightsView:h,pushLight:a,pushShadow:o,pushLightProbeGrid:l}}function R0(i){let e=new WeakMap;function t(s,r=0){let a=e.get(s),o;return a===void 0?(o=new bh(i),e.set(s,[o])):r>=a.length?(o=new bh(i),a.push(o)):o=a[r],o}function n(){e=new WeakMap}return{get:t,dispose:n}}var P0=`void main() {
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
}`,L0=[new D(1,0,0),new D(-1,0,0),new D(0,1,0),new D(0,-1,0),new D(0,0,1),new D(0,0,-1)],N0=[new D(0,-1,0),new D(0,-1,0),new D(0,0,1),new D(0,0,-1),new D(0,-1,0),new D(0,-1,0)],Sh=new pt,Xr=new D,bc=new D;function D0(i,e,t){let n=new Ss,s=new Ue,r=new Ue,a=new Dt,o=new Za,l=new ja,c={},h=t.maxTextureSize,f={[Ti]:en,[en]:Ti,[Yn]:Yn},u=new Ot({defines:{VSM_SAMPLES:8},uniforms:{shadow_pass:{value:null},resolution:{value:new Ue},radius:{value:4}},vertexShader:P0,fragmentShader:I0}),d=u.clone();d.defines.HORIZONTAL_PASS=1;let g=new Rt;g.setAttribute("position",new Kt(new Float32Array([-1,-1,.5,3,-1,.5,-1,3,.5]),3));let M=new yt(g,u),m=this;this.enabled=!1,this.autoUpdate=!0,this.needsUpdate=!1,this.type=Rr;let p=this.type;this.render=function(S,I,x){if(m.enabled===!1||m.autoUpdate===!1&&m.needsUpdate===!1||S.length===0)return;this.type===xu&&(Je("WebGLShadowMap: PCFSoftShadowMap has been removed. Using PCFShadowMap instead."),this.type=Rr);let A=i.getRenderTarget(),N=i.getActiveCubeFace(),k=i.getActiveMipmapLevel(),V=i.state;V.setBlending(Cn),V.buffers.depth.getReversed()===!0?V.buffers.color.setClear(0,0,0,0):V.buffers.color.setClear(1,1,1,1),V.buffers.depth.setTest(!0),V.setScissorTest(!1);let $=p!==this.type;$&&I.traverse(function(U){U.material&&(Array.isArray(U.material)?U.material.forEach(W=>W.needsUpdate=!0):U.material.needsUpdate=!0)});for(let U=0,W=S.length;U<W;U++){let ee=S[U],ie=ee.shadow;if(ie===void 0){Je("WebGLShadowMap:",ee,"has no shadow.");continue}if(ie.autoUpdate===!1&&ie.needsUpdate===!1)continue;s.copy(ie.mapSize);let Z=ie.getFrameExtents();s.multiply(Z),r.copy(ie.mapSize),(s.x>h||s.y>h)&&(s.x>h&&(r.x=Math.floor(h/Z.x),s.x=r.x*Z.x,ie.mapSize.x=r.x),s.y>h&&(r.y=Math.floor(h/Z.y),s.y=r.y*Z.y,ie.mapSize.y=r.y));let Q=i.state.buffers.depth.getReversed();if(ie.camera._reversedDepth=Q,ie.map===null||$===!0){if(ie.map!==null&&(ie.map.depthTexture!==null&&(ie.map.depthTexture.dispose(),ie.map.depthTexture=null),ie.map.dispose()),this.type===Ps){if(ee.isPointLight){Je("WebGLShadowMap: VSM shadow maps are not supported for PointLights. Use PCF or BasicShadowMap instead.");continue}ie.map=new Vt(s.x,s.y,{format:Ci,type:tn,minFilter:Qt,magFilter:Qt,generateMipmaps:!1}),ie.map.texture.name=ee.name+".shadowMap",ie.map.depthTexture=new vi(s.x,s.y,Rn),ie.map.depthTexture.name=ee.name+".shadowMapDepth",ie.map.depthTexture.format=Gn,ie.map.depthTexture.compareFunction=null,ie.map.depthTexture.minFilter=Zt,ie.map.depthTexture.magFilter=Zt}else ee.isPointLight?(ie.map=new nl(s.x),ie.map.depthTexture=new Va(s.x,Bn)):(ie.map=new Vt(s.x,s.y),ie.map.depthTexture=new vi(s.x,s.y,Bn)),ie.map.depthTexture.name=ee.name+".shadowMap",ie.map.depthTexture.format=Gn,this.type===Rr?(ie.map.depthTexture.compareFunction=Q?Ko:Jo,ie.map.depthTexture.minFilter=Qt,ie.map.depthTexture.magFilter=Qt):(ie.map.depthTexture.compareFunction=null,ie.map.depthTexture.minFilter=Zt,ie.map.depthTexture.magFilter=Zt);ie.camera.updateProjectionMatrix()}ie.map.isWebGLCubeRenderTarget!==!0&&(ie.map.width!==s.x||ie.map.height!==s.y)&&ie.map.setSize(s.x,s.y);let ue=ie.map.isWebGLCubeRenderTarget?6:ie.getViewportCount();ee.isPointLight!==!0&&ie.updateMatrices(ee,x);for(let se=0;se<ue;se++){let Ge=ie.getCamera(se);if(ee.isPointLight){let Pe=ie.camera,ot=ie.matrix,$e=ee.distance||Pe.far;$e!==Pe.far&&(Pe.far=$e,Pe.updateProjectionMatrix()),Xr.setFromMatrixPosition(ee.matrixWorld),Pe.position.copy(Xr),bc.copy(Pe.position),bc.add(L0[se]),Pe.up.copy(N0[se]),Pe.lookAt(bc),Pe.updateMatrixWorld(),ot.makeTranslation(-Xr.x,-Xr.y,-Xr.z),Sh.multiplyMatrices(Pe.projectionMatrix,Pe.matrixWorldInverse),ie._frustum.setFromProjectionMatrix(Sh,Pe.coordinateSystem,Pe.reversedDepth)}if(ie.map.isWebGLCubeRenderTarget)i.setRenderTarget(ie.map,se),i.clear();else{se===0&&(i.setRenderTarget(ie.map),i.clear());let Pe=ie.getViewport(se);a.set(r.x*Pe.x,r.y*Pe.y,r.x*Pe.z,r.y*Pe.w),V.viewport(a)}n=ie.getFrustum(se),v(I,x,Ge,ee,this.type)}ie.isPointLightShadow!==!0&&this.type===Ps&&T(ie,x),ie.needsUpdate=!1}p=this.type,m.needsUpdate=!1,i.setRenderTarget(A,N,k)};function T(S,I){let x=e.update(M);u.defines.VSM_SAMPLES!==S.blurSamples&&(u.defines.VSM_SAMPLES=S.blurSamples,d.defines.VSM_SAMPLES=S.blurSamples,u.needsUpdate=!0,d.needsUpdate=!0),S.mapPass===null?S.mapPass=new Vt(s.x,s.y,{format:Ci,type:tn}):(S.mapPass.width!==S.map.width||S.mapPass.height!==S.map.height)&&S.mapPass.setSize(S.map.width,S.map.height),u.uniforms.shadow_pass.value=S.map.depthTexture,u.uniforms.resolution.value.set(S.map.width,S.map.height),u.uniforms.radius.value=S.radius,i.setRenderTarget(S.mapPass),i.clear(),i.renderBufferDirect(I,null,x,u,M,null),d.uniforms.shadow_pass.value=S.mapPass.texture,d.uniforms.resolution.value.set(S.map.width,S.map.height),d.uniforms.radius.value=S.radius,i.setRenderTarget(S.map),i.clear(),i.renderBufferDirect(I,null,x,d,M,null)}function C(S,I,x,A){let N=null,k=x.isPointLight===!0?S.customDistanceMaterial:S.customDepthMaterial;if(k!==void 0)N=k;else if(N=x.isPointLight===!0?l:o,i.localClippingEnabled&&I.clipShadows===!0&&Array.isArray(I.clippingPlanes)&&I.clippingPlanes.length!==0||I.displacementMap&&I.displacementScale!==0||I.alphaMap&&I.alphaTest>0||I.map&&I.alphaTest>0||I.alphaToCoverage===!0){let V=N.uuid,$=I.uuid,U=c[V];U===void 0&&(U={},c[V]=U);let W=U[$];W===void 0&&(W=N.clone(),U[$]=W,I.addEventListener("dispose",w)),N=W}if(N.visible=I.visible,N.wireframe=I.wireframe,A===Ps?N.side=I.shadowSide!==null?I.shadowSide:I.side:N.side=I.shadowSide!==null?I.shadowSide:f[I.side],N.alphaMap=I.alphaMap,N.alphaTest=I.alphaToCoverage===!0?.5:I.alphaTest,N.map=I.map,N.clipShadows=I.clipShadows,N.clippingPlanes=I.clippingPlanes,N.clipIntersection=I.clipIntersection,N.displacementMap=I.displacementMap,N.displacementScale=I.displacementScale,N.displacementBias=I.displacementBias,N.wireframeLinewidth=I.wireframeLinewidth,N.linewidth=I.linewidth,x.isPointLight===!0&&N.isMeshDistanceMaterial===!0){let V=i.properties.get(N);V.light=x}return N}function v(S,I,x,A,N){if(S.visible===!1)return;if(S.layers.test(I.layers)&&(S.isMesh||S.isLine||S.isPoints)&&(S.castShadow||S.receiveShadow&&N===Ps)&&(!S.frustumCulled||S.intersectsFrustum(n))){S.modelViewMatrix.multiplyMatrices(x.matrixWorldInverse,S.matrixWorld);let $=e.update(S),U=S.material;if(Array.isArray(U)){let W=$.groups;for(let ee=0,ie=W.length;ee<ie;ee++){let Z=W[ee],Q=U[Z.materialIndex];if(Q&&Q.visible){let ue=C(S,Q,A,N);S.onBeforeShadow(i,S,I,x,$,ue,Z),i.renderBufferDirect(x,null,$,ue,S,Z),S.onAfterShadow(i,S,I,x,$,ue,Z)}}}else if(U.visible){let W=C(S,U,A,N);S.onBeforeShadow(i,S,I,x,$,W,null),i.renderBufferDirect(x,null,$,W,S,null),S.onAfterShadow(i,S,I,x,$,W,null)}}let V=S.children;for(let $=0,U=V.length;$<U;$++)v(V[$],I,x,A,N)}function w(S){S.target.removeEventListener("dispose",w);for(let x in c){let A=c[x],N=S.target.uuid;N in A&&(A[N].dispose(),delete A[N])}}}function U0(i,e){function t(){let O=!1,Te=new Dt,Y=null,be=new Dt(0,0,0,0);return{setMask:function(Ae){Y!==Ae&&!O&&(i.colorMask(Ae,Ae,Ae,Ae),Y=Ae)},setLocked:function(Ae){O=Ae},setClear:function(Ae,de,Ve,ze,St){St===!0&&(Ae*=ze,de*=ze,Ve*=ze),Te.set(Ae,de,Ve,ze),be.equals(Te)===!1&&(i.clearColor(Ae,de,Ve,ze),be.copy(Te))},reset:function(){O=!1,Y=null,be.set(-1,0,0,0)}}}function n(){let O=!1,Te=!1,Y=null,be=null,Ae=null;return{setReversed:function(de){if(Te!==de){let Ve=e.get("EXT_clip_control");de?Ve.clipControlEXT(Ve.LOWER_LEFT_EXT,Ve.ZERO_TO_ONE_EXT):Ve.clipControlEXT(Ve.LOWER_LEFT_EXT,Ve.NEGATIVE_ONE_TO_ONE_EXT),Te=de;let ze=Ae;Ae=null,this.setClear(ze)}},getReversed:function(){return Te},setTest:function(de){de?re(i.DEPTH_TEST):Se(i.DEPTH_TEST)},setMask:function(de){Y!==de&&!O&&(i.depthMask(de),Y=de)},setFunc:function(de){if(Te&&(de=Qu[de]),be!==de){switch(de){case wa:i.depthFunc(i.NEVER);break;case Aa:i.depthFunc(i.ALWAYS);break;case Ca:i.depthFunc(i.LESS);break;case gs:i.depthFunc(i.LEQUAL);break;case Ra:i.depthFunc(i.EQUAL);break;case Pa:i.depthFunc(i.GEQUAL);break;case Ia:i.depthFunc(i.GREATER);break;case La:i.depthFunc(i.NOTEQUAL);break;default:i.depthFunc(i.LEQUAL)}be=de}},setLocked:function(de){O=de},setClear:function(de){Ae!==de&&(Ae=de,Te&&(de=1-de),i.clearDepth(de))},reset:function(){O=!1,Y=null,be=null,Ae=null,Te=!1}}}function s(){let O=!1,Te=null,Y=null,be=null,Ae=null,de=null,Ve=null,ze=null,St=null;return{setTest:function(mt){O||(mt?re(i.STENCIL_TEST):Se(i.STENCIL_TEST))},setMask:function(mt){Te!==mt&&!O&&(i.stencilMask(mt),Te=mt)},setFunc:function(mt,ln,pn){(Y!==mt||be!==ln||Ae!==pn)&&(i.stencilFunc(mt,ln,pn),Y=mt,be=ln,Ae=pn)},setOp:function(mt,ln,pn){(de!==mt||Ve!==ln||ze!==pn)&&(i.stencilOp(mt,ln,pn),de=mt,Ve=ln,ze=pn)},setLocked:function(mt){O=mt},setClear:function(mt){St!==mt&&(i.clearStencil(mt),St=mt)},reset:function(){O=!1,Te=null,Y=null,be=null,Ae=null,de=null,Ve=null,ze=null,St=null}}}let r=new t,a=new n,o=new s,l=new WeakMap,c=new WeakMap,h={},f={},u={},d=new WeakMap,g=[],M=null,m=!1,p=null,T=null,C=null,v=null,w=null,S=null,I=null,x=new Ke(0,0,0),A=0,N=!1,k=null,V=null,$=null,U=null,W=null,ee=i.getParameter(i.MAX_COMBINED_TEXTURE_IMAGE_UNITS),ie=!1,Z=0,Q=i.getParameter(i.VERSION);Q.indexOf("WebGL")!==-1?(Z=parseFloat(/^WebGL (\d)/.exec(Q)[1]),ie=Z>=1):Q.indexOf("OpenGL ES")!==-1&&(Z=parseFloat(/^OpenGL ES (\d)/.exec(Q)[1]),ie=Z>=2);let ue=null,se={},Ge=i.getParameter(i.SCISSOR_BOX),Pe=i.getParameter(i.VIEWPORT),ot=new Dt().fromArray(Ge),$e=new Dt().fromArray(Pe);function Xe(O,Te,Y,be){let Ae=new Uint8Array(4),de=i.createTexture();i.bindTexture(O,de),i.texParameteri(O,i.TEXTURE_MIN_FILTER,i.NEAREST),i.texParameteri(O,i.TEXTURE_MAG_FILTER,i.NEAREST);for(let Ve=0;Ve<Y;Ve++)O===i.TEXTURE_3D||O===i.TEXTURE_2D_ARRAY?i.texImage3D(Te,0,i.RGBA,1,1,be,0,i.RGBA,i.UNSIGNED_BYTE,Ae):i.texImage2D(Te+Ve,0,i.RGBA,1,1,0,i.RGBA,i.UNSIGNED_BYTE,Ae);return de}let K={};K[i.TEXTURE_2D]=Xe(i.TEXTURE_2D,i.TEXTURE_2D,1),K[i.TEXTURE_CUBE_MAP]=Xe(i.TEXTURE_CUBE_MAP,i.TEXTURE_CUBE_MAP_POSITIVE_X,6),K[i.TEXTURE_2D_ARRAY]=Xe(i.TEXTURE_2D_ARRAY,i.TEXTURE_2D_ARRAY,1,1),K[i.TEXTURE_3D]=Xe(i.TEXTURE_3D,i.TEXTURE_3D,1,1),r.setClear(0,0,0,1),a.setClear(1),o.setClear(0),re(i.DEPTH_TEST),a.setFunc(gs),rt(!1),gt(jl),re(i.CULL_FACE),it(Cn);function re(O){h[O]!==!0&&(i.enable(O),h[O]=!0)}function Se(O){h[O]!==!1&&(i.disable(O),h[O]=!1)}function Le(O,Te){return u[O]!==Te?(i.bindFramebuffer(O,Te),u[O]=Te,O===i.DRAW_FRAMEBUFFER&&(u[i.FRAMEBUFFER]=Te),O===i.FRAMEBUFFER&&(u[i.DRAW_FRAMEBUFFER]=Te),!0):!1}function Ie(O,Te){let Y=g,be=!1;if(O){Y=d.get(Te),Y===void 0&&(Y=[],d.set(Te,Y));let Ae=O.textures;if(Y.length!==Ae.length||Y[0]!==i.COLOR_ATTACHMENT0){for(let de=0,Ve=Ae.length;de<Ve;de++)Y[de]=i.COLOR_ATTACHMENT0+de;Y.length=Ae.length,be=!0}}else Y[0]!==i.BACK&&(Y[0]=i.BACK,be=!0);be&&i.drawBuffers(Y)}function Ze(O){return M!==O?(i.useProgram(O),M=O,!0):!1}let ht={[qi]:i.FUNC_ADD,[yu]:i.FUNC_SUBTRACT,[Mu]:i.FUNC_REVERSE_SUBTRACT};ht[bu]=i.MIN,ht[Su]=i.MAX;let st={[Tu]:i.ZERO,[Eu]:i.ONE,[wu]:i.SRC_COLOR,[Ql]:i.SRC_ALPHA,[Lu]:i.SRC_ALPHA_SATURATE,[Pu]:i.DST_COLOR,[Cu]:i.DST_ALPHA,[Au]:i.ONE_MINUS_SRC_COLOR,[ec]:i.ONE_MINUS_SRC_ALPHA,[Iu]:i.ONE_MINUS_DST_COLOR,[Ru]:i.ONE_MINUS_DST_ALPHA,[Nu]:i.CONSTANT_COLOR,[Du]:i.ONE_MINUS_CONSTANT_COLOR,[Uu]:i.CONSTANT_ALPHA,[Fu]:i.ONE_MINUS_CONSTANT_ALPHA};function it(O,Te,Y,be,Ae,de,Ve,ze,St,mt){if(O===Cn){m===!0&&(Se(i.BLEND),m=!1);return}if(m===!1&&(re(i.BLEND),m=!0),O!==vu){if(O!==p||mt!==N){if((T!==qi||w!==qi)&&(i.blendEquation(i.FUNC_ADD),T=qi,w=qi),mt)switch(O){case Is:i.blendFuncSeparate(i.ONE,i.ONE_MINUS_SRC_ALPHA,i.ONE,i.ONE_MINUS_SRC_ALPHA);break;case Wi:i.blendFunc(i.ONE,i.ONE);break;case Jl:i.blendFuncSeparate(i.ZERO,i.ONE_MINUS_SRC_COLOR,i.ZERO,i.ONE);break;case Kl:i.blendFuncSeparate(i.DST_COLOR,i.ONE_MINUS_SRC_ALPHA,i.ZERO,i.ONE);break;default:et("WebGLState: Invalid blending: ",O);break}else switch(O){case Is:i.blendFuncSeparate(i.SRC_ALPHA,i.ONE_MINUS_SRC_ALPHA,i.ONE,i.ONE_MINUS_SRC_ALPHA);break;case Wi:i.blendFuncSeparate(i.SRC_ALPHA,i.ONE,i.ONE,i.ONE);break;case Jl:et("WebGLState: SubtractiveBlending requires material.premultipliedAlpha = true");break;case Kl:et("WebGLState: MultiplyBlending requires material.premultipliedAlpha = true");break;default:et("WebGLState: Invalid blending: ",O);break}C=null,v=null,S=null,I=null,x.set(0,0,0),A=0,p=O,N=mt}return}Ae=Ae||Te,de=de||Y,Ve=Ve||be,(Te!==T||Ae!==w)&&(i.blendEquationSeparate(ht[Te],ht[Ae]),T=Te,w=Ae),(Y!==C||be!==v||de!==S||Ve!==I)&&(i.blendFuncSeparate(st[Y],st[be],st[de],st[Ve]),C=Y,v=be,S=de,I=Ve),(ze.equals(x)===!1||St!==A)&&(i.blendColor(ze.r,ze.g,ze.b,St),x.copy(ze),A=St),p=O,N=!1}function Qe(O,Te){O.side===Yn?Se(i.CULL_FACE):re(i.CULL_FACE);let Y=O.side===en;Te&&(Y=!Y),rt(Y),O.blending===Is&&O.transparent===!1?it(Cn):it(O.blending,O.blendEquation,O.blendSrc,O.blendDst,O.blendEquationAlpha,O.blendSrcAlpha,O.blendDstAlpha,O.blendColor,O.blendAlpha,O.premultipliedAlpha),a.setFunc(O.depthFunc),a.setTest(O.depthTest),a.setMask(O.depthWrite),r.setMask(O.colorWrite);let be=O.stencilWrite;o.setTest(be),be&&(o.setMask(O.stencilWriteMask),o.setFunc(O.stencilFunc,O.stencilRef,O.stencilFuncMask),o.setOp(O.stencilFail,O.stencilZFail,O.stencilZPass)),Ut(O.polygonOffset,O.polygonOffsetFactor,O.polygonOffsetUnits),O.alphaToCoverage===!0?re(i.SAMPLE_ALPHA_TO_COVERAGE):Se(i.SAMPLE_ALPHA_TO_COVERAGE)}function rt(O){k!==O&&(O?i.frontFace(i.CW):i.frontFace(i.CCW),k=O)}function gt(O){O!==gu?(re(i.CULL_FACE),O!==V&&(O===jl?i.cullFace(i.BACK):O===_u?i.cullFace(i.FRONT):i.cullFace(i.FRONT_AND_BACK))):Se(i.CULL_FACE),V=O}function Ct(O){O!==$&&(ie&&i.lineWidth(O),$=O)}function Ut(O,Te,Y){O?(re(i.POLYGON_OFFSET_FILL),(U!==Te||W!==Y)&&(U=Te,W=Y,a.getReversed()&&(Te=-Te),i.polygonOffset(Te,Y))):Se(i.POLYGON_OFFSET_FILL)}function _t(O){O?re(i.SCISSOR_TEST):Se(i.SCISSOR_TEST)}function Et(O){O===void 0&&(O=i.TEXTURE0+ee-1),ue!==O&&(i.activeTexture(O),ue=O)}function B(O,Te,Y){Y===void 0&&(ue===null?Y=i.TEXTURE0+ee-1:Y=ue);let be=se[Y];be===void 0&&(be={type:void 0,texture:void 0},se[Y]=be),(be.type!==O||be.texture!==Te)&&(ue!==Y&&(i.activeTexture(Y),ue=Y),i.bindTexture(O,Te||K[O]),be.type=O,be.texture=Te)}function wt(){let O=se[ue];O!==void 0&&O.type!==void 0&&(i.bindTexture(O.type,null),O.type=void 0,O.texture=void 0)}function ct(){try{i.compressedTexImage2D(...arguments)}catch(O){et("WebGLState:",O)}}function P(){try{i.compressedTexImage3D(...arguments)}catch(O){et("WebGLState:",O)}}function _(){try{i.texSubImage2D(...arguments)}catch(O){et("WebGLState:",O)}}function G(){try{i.texSubImage3D(...arguments)}catch(O){et("WebGLState:",O)}}function j(){try{i.compressedTexSubImage2D(...arguments)}catch(O){et("WebGLState:",O)}}function oe(){try{i.compressedTexSubImage3D(...arguments)}catch(O){et("WebGLState:",O)}}function Me(){try{i.texStorage2D(...arguments)}catch(O){et("WebGLState:",O)}}function Ee(){try{i.texStorage3D(...arguments)}catch(O){et("WebGLState:",O)}}function L(){try{i.texImage2D(...arguments)}catch(O){et("WebGLState:",O)}}function z(){try{i.texImage3D(...arguments)}catch(O){et("WebGLState:",O)}}function ne(O){return f[O]!==void 0?f[O]:i.getParameter(O)}function _e(O,Te){f[O]!==Te&&(i.pixelStorei(O,Te),f[O]=Te)}function ce(O){ot.equals(O)===!1&&(i.scissor(O.x,O.y,O.z,O.w),ot.copy(O))}function pe(O){$e.equals(O)===!1&&(i.viewport(O.x,O.y,O.z,O.w),$e.copy(O))}function ye(O,Te){let Y=c.get(Te);Y===void 0&&(Y=new WeakMap,c.set(Te,Y));let be=Y.get(O);be===void 0&&(be=i.getUniformBlockIndex(Te,O.name),Y.set(O,be))}function we(O,Te){let be=c.get(Te).get(O);l.get(Te)!==be&&(i.uniformBlockBinding(Te,be,O.__bindingPointIndex),l.set(Te,be))}function ke(){i.disable(i.BLEND),i.disable(i.CULL_FACE),i.disable(i.DEPTH_TEST),i.disable(i.POLYGON_OFFSET_FILL),i.disable(i.SCISSOR_TEST),i.disable(i.STENCIL_TEST),i.disable(i.SAMPLE_ALPHA_TO_COVERAGE),i.blendEquation(i.FUNC_ADD),i.blendFunc(i.ONE,i.ZERO),i.blendFuncSeparate(i.ONE,i.ZERO,i.ONE,i.ZERO),i.blendColor(0,0,0,0),i.colorMask(!0,!0,!0,!0),i.clearColor(0,0,0,0),i.depthMask(!0),i.depthFunc(i.LESS),a.setReversed(!1),i.clearDepth(1),i.stencilMask(4294967295),i.stencilFunc(i.ALWAYS,0,4294967295),i.stencilOp(i.KEEP,i.KEEP,i.KEEP),i.clearStencil(0),i.cullFace(i.BACK),i.frontFace(i.CCW),i.polygonOffset(0,0),i.activeTexture(i.TEXTURE0),i.bindFramebuffer(i.FRAMEBUFFER,null),i.bindFramebuffer(i.DRAW_FRAMEBUFFER,null),i.bindFramebuffer(i.READ_FRAMEBUFFER,null),i.useProgram(null),i.lineWidth(1),i.scissor(0,0,i.canvas.width,i.canvas.height),i.viewport(0,0,i.canvas.width,i.canvas.height),i.pixelStorei(i.PACK_ALIGNMENT,4),i.pixelStorei(i.UNPACK_ALIGNMENT,4),i.pixelStorei(i.UNPACK_FLIP_Y_WEBGL,!1),i.pixelStorei(i.UNPACK_PREMULTIPLY_ALPHA_WEBGL,!1),i.pixelStorei(i.UNPACK_COLORSPACE_CONVERSION_WEBGL,i.BROWSER_DEFAULT_WEBGL),i.pixelStorei(i.PACK_ROW_LENGTH,0),i.pixelStorei(i.PACK_SKIP_PIXELS,0),i.pixelStorei(i.PACK_SKIP_ROWS,0),i.pixelStorei(i.UNPACK_ROW_LENGTH,0),i.pixelStorei(i.UNPACK_IMAGE_HEIGHT,0),i.pixelStorei(i.UNPACK_SKIP_PIXELS,0),i.pixelStorei(i.UNPACK_SKIP_ROWS,0),i.pixelStorei(i.UNPACK_SKIP_IMAGES,0),h={},f={},ue=null,se={},u={},d=new WeakMap,g=[],M=null,m=!1,p=null,T=null,C=null,v=null,w=null,S=null,I=null,x=new Ke(0,0,0),A=0,N=!1,k=null,V=null,$=null,U=null,W=null,ot.set(0,0,i.canvas.width,i.canvas.height),$e.set(0,0,i.canvas.width,i.canvas.height),r.reset(),a.reset(),o.reset()}return{buffers:{color:r,depth:a,stencil:o},enable:re,disable:Se,bindFramebuffer:Le,drawBuffers:Ie,useProgram:Ze,setBlending:it,setMaterial:Qe,setFlipSided:rt,setCullFace:gt,setLineWidth:Ct,setPolygonOffset:Ut,setScissorTest:_t,activeTexture:Et,bindTexture:B,unbindTexture:wt,compressedTexImage2D:ct,compressedTexImage3D:P,texImage2D:L,texImage3D:z,pixelStorei:_e,getParameter:ne,updateUBOMapping:ye,uniformBlockBinding:we,texStorage2D:Me,texStorage3D:Ee,texSubImage2D:_,texSubImage3D:G,compressedTexSubImage2D:j,compressedTexSubImage3D:oe,scissor:ce,viewport:pe,reset:ke}}function F0(i,e,t,n,s,r,a){let o=e.has("WEBGL_multisampled_render_to_texture")?e.get("WEBGL_multisampled_render_to_texture"):null,l=typeof navigator>"u"?!1:/OculusBrowser/g.test(navigator.userAgent),c=new Ue,h=new WeakMap,f=new Set,u,d=new WeakMap,g=!1;try{g=typeof OffscreenCanvas<"u"&&new OffscreenCanvas(1,1).getContext("2d")!==null}catch{}function M(P,_){return g?new OffscreenCanvas(P,_):rr("canvas")}function m(P,_,G){let j=1,oe=ct(P);if((oe.width>G||oe.height>G)&&(j=G/Math.max(oe.width,oe.height)),j<1)if(typeof HTMLImageElement<"u"&&P instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&P instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&P instanceof ImageBitmap||typeof VideoFrame<"u"&&P instanceof VideoFrame){let Me=Math.floor(j*oe.width),Ee=Math.floor(j*oe.height);u===void 0&&(u=M(Me,Ee));let L=_?M(Me,Ee):u;return L.width=Me,L.height=Ee,L.getContext("2d").drawImage(P,0,0,Me,Ee),Je("WebGLRenderer: Texture has been resized from ("+oe.width+"x"+oe.height+") to ("+Me+"x"+Ee+")."),L}else return"data"in P&&Je("WebGLRenderer: Image in DataTexture is too big ("+oe.width+"x"+oe.height+")."),P;return P}function p(P){return P.generateMipmaps}function T(P){i.generateMipmap(P)}function C(P){return P.isWebGLCubeRenderTarget?i.TEXTURE_CUBE_MAP:P.isWebGL3DRenderTarget?i.TEXTURE_3D:P.isWebGLArrayRenderTarget||P.isCompressedArrayTexture?i.TEXTURE_2D_ARRAY:i.TEXTURE_2D}function v(P,_,G,j,oe,Me=!1){if(P!==null){if(i[P]!==void 0)return i[P];Je("WebGLRenderer: Attempt to use non-existing WebGL internal format '"+P+"'")}let Ee;j&&(Ee=e.get("EXT_texture_norm16"),Ee||Je("WebGLRenderer: Unable to use normalized textures without EXT_texture_norm16 extension"));let L=_;if(_===i.RED&&(G===i.FLOAT&&(L=i.R32F),G===i.HALF_FLOAT&&(L=i.R16F),G===i.UNSIGNED_BYTE&&(L=i.R8),G===i.UNSIGNED_SHORT&&Ee&&(L=Ee.R16_EXT),G===i.SHORT&&Ee&&(L=Ee.R16_SNORM_EXT)),_===i.RED_INTEGER&&(G===i.UNSIGNED_BYTE&&(L=i.R8UI),G===i.UNSIGNED_SHORT&&(L=i.R16UI),G===i.UNSIGNED_INT&&(L=i.R32UI),G===i.BYTE&&(L=i.R8I),G===i.SHORT&&(L=i.R16I),G===i.INT&&(L=i.R32I)),_===i.RG&&(G===i.FLOAT&&(L=i.RG32F),G===i.HALF_FLOAT&&(L=i.RG16F),G===i.UNSIGNED_BYTE&&(L=i.RG8),G===i.UNSIGNED_SHORT&&Ee&&(L=Ee.RG16_EXT),G===i.SHORT&&Ee&&(L=Ee.RG16_SNORM_EXT)),_===i.RG_INTEGER&&(G===i.UNSIGNED_BYTE&&(L=i.RG8UI),G===i.UNSIGNED_SHORT&&(L=i.RG16UI),G===i.UNSIGNED_INT&&(L=i.RG32UI),G===i.BYTE&&(L=i.RG8I),G===i.SHORT&&(L=i.RG16I),G===i.INT&&(L=i.RG32I)),_===i.RGB_INTEGER&&(G===i.UNSIGNED_BYTE&&(L=i.RGB8UI),G===i.UNSIGNED_SHORT&&(L=i.RGB16UI),G===i.UNSIGNED_INT&&(L=i.RGB32UI),G===i.BYTE&&(L=i.RGB8I),G===i.SHORT&&(L=i.RGB16I),G===i.INT&&(L=i.RGB32I)),_===i.RGBA_INTEGER&&(G===i.UNSIGNED_BYTE&&(L=i.RGBA8UI),G===i.UNSIGNED_SHORT&&(L=i.RGBA16UI),G===i.UNSIGNED_INT&&(L=i.RGBA32UI),G===i.BYTE&&(L=i.RGBA8I),G===i.SHORT&&(L=i.RGBA16I),G===i.INT&&(L=i.RGBA32I)),_===i.RGB&&(G===i.UNSIGNED_SHORT&&Ee&&(L=Ee.RGB16_EXT),G===i.SHORT&&Ee&&(L=Ee.RGB16_SNORM_EXT),G===i.UNSIGNED_INT_5_9_9_9_REV&&(L=i.RGB9_E5),G===i.UNSIGNED_INT_10F_11F_11F_REV&&(L=i.R11F_G11F_B10F)),_===i.RGBA){let z=Me?sr:dt.getTransfer(oe);G===i.FLOAT&&(L=i.RGBA32F),G===i.HALF_FLOAT&&(L=i.RGBA16F),G===i.UNSIGNED_BYTE&&(L=z===bt?i.SRGB8_ALPHA8:i.RGBA8),G===i.UNSIGNED_SHORT&&Ee&&(L=Ee.RGBA16_EXT),G===i.SHORT&&Ee&&(L=Ee.RGBA16_SNORM_EXT),G===i.UNSIGNED_SHORT_4_4_4_4&&(L=i.RGBA4),G===i.UNSIGNED_SHORT_5_5_5_1&&(L=i.RGB5_A1)}return(L===i.R16F||L===i.R32F||L===i.RG16F||L===i.RG32F||L===i.RGBA16F||L===i.RGBA32F)&&e.get("EXT_color_buffer_float"),L}function w(P,_){let G;return P?_===null||_===Bn||_===Ns?G=i.DEPTH24_STENCIL8:_===Rn?G=i.DEPTH32F_STENCIL8:_===Ls&&(G=i.DEPTH24_STENCIL8,Je("DepthTexture: 16 bit depth attachment is not supported with stencil. Using 24-bit attachment.")):_===null||_===Bn||_===Ns?G=i.DEPTH_COMPONENT24:_===Rn?G=i.DEPTH_COMPONENT32F:_===Ls&&(G=i.DEPTH_COMPONENT16),G}function S(P,_){return p(P)===!0||P.isFramebufferTexture&&P.minFilter!==Zt&&P.minFilter!==Qt?Math.log2(Math.max(_.width,_.height))+1:P.mipmaps!==void 0&&P.mipmaps.length>0?P.mipmaps.length:P.isCompressedTexture&&Array.isArray(P.image)?_.mipmaps.length:1}function I(P){let _=P.target;_.removeEventListener("dispose",I),A(_),_.isVideoTexture&&h.delete(_),_.isHTMLTexture&&f.delete(_)}function x(P){let _=P.target;_.removeEventListener("dispose",x),k(_)}function A(P){let _=n.get(P);if(_.__webglInit===void 0)return;let G=P.source,j=d.get(G);if(j){let oe=j[_.__cacheKey];oe.usedTimes--,oe.usedTimes===0&&N(P),Object.keys(j).length===0&&d.delete(G)}n.remove(P)}function N(P){let _=n.get(P);i.deleteTexture(_.__webglTexture);let G=P.source,j=d.get(G);delete j[_.__cacheKey],a.memory.textures--}function k(P){let _=n.get(P);if(P.depthTexture&&(P.depthTexture.dispose(),n.remove(P.depthTexture)),P.isWebGLCubeRenderTarget)for(let j=0;j<6;j++){if(Array.isArray(_.__webglFramebuffer[j]))for(let oe=0;oe<_.__webglFramebuffer[j].length;oe++)i.deleteFramebuffer(_.__webglFramebuffer[j][oe]);else i.deleteFramebuffer(_.__webglFramebuffer[j]);_.__webglDepthbuffer&&i.deleteRenderbuffer(_.__webglDepthbuffer[j])}else{if(Array.isArray(_.__webglFramebuffer))for(let j=0;j<_.__webglFramebuffer.length;j++)i.deleteFramebuffer(_.__webglFramebuffer[j]);else i.deleteFramebuffer(_.__webglFramebuffer);if(_.__webglDepthbuffer&&i.deleteRenderbuffer(_.__webglDepthbuffer),_.__webglMultisampledFramebuffer&&i.deleteFramebuffer(_.__webglMultisampledFramebuffer),_.__webglColorRenderbuffer)for(let j=0;j<_.__webglColorRenderbuffer.length;j++)_.__webglColorRenderbuffer[j]&&i.deleteRenderbuffer(_.__webglColorRenderbuffer[j]);_.__webglDepthRenderbuffer&&i.deleteRenderbuffer(_.__webglDepthRenderbuffer)}let G=P.textures;for(let j=0,oe=G.length;j<oe;j++){let Me=n.get(G[j]);Me.__webglTexture&&(i.deleteTexture(Me.__webglTexture),a.memory.textures--),n.remove(G[j])}n.remove(P)}let V=0;function $(){V=0}function U(){return V}function W(P){V=P}function ee(){let P=V;return P>=s.maxTextures&&Je("WebGLTextures: Trying to use "+(P+1)+" texture units while this GPU supports only "+s.maxTextures),V+=1,P}function ie(P){let _=[];return _.push(P.wrapS),_.push(P.wrapT),_.push(P.wrapR||0),_.push(P.magFilter),_.push(P.minFilter),_.push(P.anisotropy),_.push(P.internalFormat),_.push(P.format),_.push(P.type),_.push(P.generateMipmaps),_.push(P.premultiplyAlpha),_.push(P.flipY),_.push(P.unpackAlignment),_.push(P.colorSpace),_.join()}function Z(P,_){let G=n.get(P);if(P.isVideoTexture&&B(P),P.isRenderTargetTexture===!1&&P.isExternalTexture!==!0&&P.version>0&&G.__version!==P.version){let j=P.image;if(j===null)Je("WebGLRenderer: Texture marked for update but no image data found.");else if(j.complete===!1)Je("WebGLRenderer: Texture marked for update but image is incomplete");else{Se(G,P,_);return}}else P.isExternalTexture&&(G.__webglTexture=P.sourceTexture?P.sourceTexture:null);t.bindTexture(i.TEXTURE_2D,G.__webglTexture,i.TEXTURE0+_)}function Q(P,_){let G=n.get(P);if(P.isRenderTargetTexture===!1&&P.version>0&&G.__version!==P.version){Se(G,P,_);return}else P.isExternalTexture&&(G.__webglTexture=P.sourceTexture?P.sourceTexture:null);t.bindTexture(i.TEXTURE_2D_ARRAY,G.__webglTexture,i.TEXTURE0+_)}function ue(P,_){let G=n.get(P);if(P.isRenderTargetTexture===!1&&P.version>0&&G.__version!==P.version){Se(G,P,_);return}t.bindTexture(i.TEXTURE_3D,G.__webglTexture,i.TEXTURE0+_)}function se(P,_){let G=n.get(P);if(P.isCubeDepthTexture!==!0&&P.version>0&&G.__version!==P.version){Le(G,P,_);return}t.bindTexture(i.TEXTURE_CUBE_MAP,G.__webglTexture,i.TEXTURE0+_)}let Ge={[Na]:i.REPEAT,[Hn]:i.CLAMP_TO_EDGE,[Da]:i.MIRRORED_REPEAT},Pe={[Zt]:i.NEAREST,[Bu]:i.NEAREST_MIPMAP_NEAREST,[kr]:i.NEAREST_MIPMAP_LINEAR,[Qt]:i.LINEAR,[fo]:i.LINEAR_MIPMAP_NEAREST,[wi]:i.LINEAR_MIPMAP_LINEAR},ot={[Gu]:i.NEVER,[Yu]:i.ALWAYS,[Wu]:i.LESS,[Jo]:i.LEQUAL,[qu]:i.EQUAL,[Ko]:i.GEQUAL,[Xu]:i.GREATER,[$u]:i.NOTEQUAL};function $e(P,_){if(_.type===Rn&&e.has("OES_texture_float_linear")===!1&&(_.magFilter===Qt||_.magFilter===fo||_.magFilter===kr||_.magFilter===wi||_.minFilter===Qt||_.minFilter===fo||_.minFilter===kr||_.minFilter===wi)&&Je("WebGLRenderer: Unable to use linear filtering with floating point textures. OES_texture_float_linear not supported on this device."),i.texParameteri(P,i.TEXTURE_WRAP_S,Ge[_.wrapS]),i.texParameteri(P,i.TEXTURE_WRAP_T,Ge[_.wrapT]),(P===i.TEXTURE_3D||P===i.TEXTURE_2D_ARRAY)&&i.texParameteri(P,i.TEXTURE_WRAP_R,Ge[_.wrapR]),i.texParameteri(P,i.TEXTURE_MAG_FILTER,Pe[_.magFilter]),i.texParameteri(P,i.TEXTURE_MIN_FILTER,Pe[_.minFilter]),_.compareFunction&&(i.texParameteri(P,i.TEXTURE_COMPARE_MODE,i.COMPARE_REF_TO_TEXTURE),i.texParameteri(P,i.TEXTURE_COMPARE_FUNC,ot[_.compareFunction])),e.has("EXT_texture_filter_anisotropic")===!0){if(_.magFilter===Zt||_.minFilter!==kr&&_.minFilter!==wi||_.type===Rn&&e.has("OES_texture_float_linear")===!1)return;if(_.anisotropy>1||n.get(_).__currentAnisotropy){let G=e.get("EXT_texture_filter_anisotropic");i.texParameterf(P,G.TEXTURE_MAX_ANISOTROPY_EXT,Math.min(_.anisotropy,s.getMaxAnisotropy())),n.get(_).__currentAnisotropy=_.anisotropy}}}function Xe(P,_){let G=!1;P.__webglInit===void 0&&(P.__webglInit=!0,_.addEventListener("dispose",I));let j=_.source,oe=d.get(j);oe===void 0&&(oe={},d.set(j,oe));let Me=ie(_);if(Me!==P.__cacheKey){oe[Me]===void 0&&(oe[Me]={texture:i.createTexture(),usedTimes:0},a.memory.textures++,G=!0),oe[Me].usedTimes++;let Ee=oe[P.__cacheKey];Ee!==void 0&&(oe[P.__cacheKey].usedTimes--,Ee.usedTimes===0&&N(_)),P.__cacheKey=Me,P.__webglTexture=oe[Me].texture}return G}function K(P,_,G){return Math.floor(Math.floor(P/G)/_)}function re(P,_,G,j){let Me=P.updateRanges;if(Me.length===0)t.texSubImage2D(i.TEXTURE_2D,0,0,0,_.width,_.height,G,j,_.data);else{Me.sort((_e,ce)=>_e.start-ce.start);let Ee=0;for(let _e=1;_e<Me.length;_e++){let ce=Me[Ee],pe=Me[_e],ye=ce.start+ce.count,we=K(pe.start,_.width,4),ke=K(ce.start,_.width,4);pe.start<=ye+1&&we===ke&&K(pe.start+pe.count-1,_.width,4)===we?ce.count=Math.max(ce.count,pe.start+pe.count-ce.start):(++Ee,Me[Ee]=pe)}Me.length=Ee+1;let L=t.getParameter(i.UNPACK_ROW_LENGTH),z=t.getParameter(i.UNPACK_SKIP_PIXELS),ne=t.getParameter(i.UNPACK_SKIP_ROWS);t.pixelStorei(i.UNPACK_ROW_LENGTH,_.width);for(let _e=0,ce=Me.length;_e<ce;_e++){let pe=Me[_e],ye=Math.floor(pe.start/4),we=Math.ceil(pe.count/4),ke=ye%_.width,O=Math.floor(ye/_.width),Te=we,Y=1;t.pixelStorei(i.UNPACK_SKIP_PIXELS,ke),t.pixelStorei(i.UNPACK_SKIP_ROWS,O),t.texSubImage2D(i.TEXTURE_2D,0,ke,O,Te,Y,G,j,_.data)}P.clearUpdateRanges(),t.pixelStorei(i.UNPACK_ROW_LENGTH,L),t.pixelStorei(i.UNPACK_SKIP_PIXELS,z),t.pixelStorei(i.UNPACK_SKIP_ROWS,ne)}}function Se(P,_,G){let j=i.TEXTURE_2D;(_.isDataArrayTexture||_.isCompressedArrayTexture)&&(j=i.TEXTURE_2D_ARRAY),_.isData3DTexture&&(j=i.TEXTURE_3D);let oe=Xe(P,_),Me=_.source;t.bindTexture(j,P.__webglTexture,i.TEXTURE0+G);let Ee=n.get(Me);if(Me.version!==Ee.__version||oe===!0){if(t.activeTexture(i.TEXTURE0+G),(typeof ImageBitmap<"u"&&_.image instanceof ImageBitmap)===!1){let Y=dt.getPrimaries(dt.workingColorSpace),be=_.colorSpace===oi?null:dt.getPrimaries(_.colorSpace),Ae=_.colorSpace===oi||Y===be?i.NONE:i.BROWSER_DEFAULT_WEBGL;t.pixelStorei(i.UNPACK_FLIP_Y_WEBGL,_.flipY),t.pixelStorei(i.UNPACK_PREMULTIPLY_ALPHA_WEBGL,_.premultiplyAlpha),t.pixelStorei(i.UNPACK_COLORSPACE_CONVERSION_WEBGL,Ae)}t.pixelStorei(i.UNPACK_ALIGNMENT,_.unpackAlignment);let z=m(_.image,!1,s.maxTextureSize);z=wt(_,z);let ne=r.convert(_.format,_.colorSpace),_e=r.convert(_.type),ce=v(_.internalFormat,ne,_e,_.normalized,_.colorSpace,_.isVideoTexture);$e(j,_);let pe,ye=_.mipmaps,we=_.isVideoTexture!==!0,ke=Ee.__version===void 0||oe===!0,O=Me.dataReady,Te=S(_,z);if(_.isDepthTexture)ce=w(_.format===Ai,_.type),ke&&(we?t.texStorage2D(i.TEXTURE_2D,1,ce,z.width,z.height):t.texImage2D(i.TEXTURE_2D,0,ce,z.width,z.height,0,ne,_e,null));else if(_.isDataTexture)if(ye.length>0){we&&ke&&t.texStorage2D(i.TEXTURE_2D,Te,ce,ye[0].width,ye[0].height);for(let Y=0,be=ye.length;Y<be;Y++)pe=ye[Y],we?O&&t.texSubImage2D(i.TEXTURE_2D,Y,0,0,pe.width,pe.height,ne,_e,pe.data):t.texImage2D(i.TEXTURE_2D,Y,ce,pe.width,pe.height,0,ne,_e,pe.data);_.generateMipmaps=!1}else we?(ke&&t.texStorage2D(i.TEXTURE_2D,Te,ce,z.width,z.height),O&&re(_,z,ne,_e)):t.texImage2D(i.TEXTURE_2D,0,ce,z.width,z.height,0,ne,_e,z.data);else if(_.isCompressedTexture)if(_.isCompressedArrayTexture){we&&ke&&t.texStorage3D(i.TEXTURE_2D_ARRAY,Te,ce,ye[0].width,ye[0].height,z.depth);for(let Y=0,be=ye.length;Y<be;Y++)if(pe=ye[Y],_.format!==Pn)if(ne!==null)if(we){if(O)if(_.layerUpdates.size>0){let Ae=gc(pe.width,pe.height,_.format,_.type);for(let de of _.layerUpdates){let Ve=pe.data.subarray(de*Ae/pe.data.BYTES_PER_ELEMENT,(de+1)*Ae/pe.data.BYTES_PER_ELEMENT);t.compressedTexSubImage3D(i.TEXTURE_2D_ARRAY,Y,0,0,de,pe.width,pe.height,1,ne,Ve)}}else t.compressedTexSubImage3D(i.TEXTURE_2D_ARRAY,Y,0,0,0,pe.width,pe.height,z.depth,ne,pe.data)}else t.compressedTexImage3D(i.TEXTURE_2D_ARRAY,Y,ce,pe.width,pe.height,z.depth,0,pe.data,0,0);else Je("WebGLRenderer: Attempt to load unsupported compressed texture format in .uploadTexture()");else we?O&&t.texSubImage3D(i.TEXTURE_2D_ARRAY,Y,0,0,0,pe.width,pe.height,z.depth,ne,_e,pe.data):t.texImage3D(i.TEXTURE_2D_ARRAY,Y,ce,pe.width,pe.height,z.depth,0,ne,_e,pe.data);_.layerUpdates.size>0&&_.clearLayerUpdates()}else{we&&ke&&t.texStorage2D(i.TEXTURE_2D,Te,ce,ye[0].width,ye[0].height);for(let Y=0,be=ye.length;Y<be;Y++)pe=ye[Y],_.format!==Pn?ne!==null?we?O&&t.compressedTexSubImage2D(i.TEXTURE_2D,Y,0,0,pe.width,pe.height,ne,pe.data):t.compressedTexImage2D(i.TEXTURE_2D,Y,ce,pe.width,pe.height,0,pe.data):Je("WebGLRenderer: Attempt to load unsupported compressed texture format in .uploadTexture()"):we?O&&t.texSubImage2D(i.TEXTURE_2D,Y,0,0,pe.width,pe.height,ne,_e,pe.data):t.texImage2D(i.TEXTURE_2D,Y,ce,pe.width,pe.height,0,ne,_e,pe.data)}else if(_.isDataArrayTexture)if(we){if(ke&&t.texStorage3D(i.TEXTURE_2D_ARRAY,Te,ce,z.width,z.height,z.depth),O)if(_.layerUpdates.size>0){let Y=gc(z.width,z.height,_.format,_.type);for(let be of _.layerUpdates){let Ae=z.data.subarray(be*Y/z.data.BYTES_PER_ELEMENT,(be+1)*Y/z.data.BYTES_PER_ELEMENT);t.texSubImage3D(i.TEXTURE_2D_ARRAY,0,0,0,be,z.width,z.height,1,ne,_e,Ae)}_.clearLayerUpdates()}else t.texSubImage3D(i.TEXTURE_2D_ARRAY,0,0,0,0,z.width,z.height,z.depth,ne,_e,z.data)}else t.texImage3D(i.TEXTURE_2D_ARRAY,0,ce,z.width,z.height,z.depth,0,ne,_e,z.data);else if(_.isData3DTexture)we?(ke&&t.texStorage3D(i.TEXTURE_3D,Te,ce,z.width,z.height,z.depth),O&&t.texSubImage3D(i.TEXTURE_3D,0,0,0,0,z.width,z.height,z.depth,ne,_e,z.data)):t.texImage3D(i.TEXTURE_3D,0,ce,z.width,z.height,z.depth,0,ne,_e,z.data);else if(_.isFramebufferTexture){if(ke)if(we)t.texStorage2D(i.TEXTURE_2D,Te,ce,z.width,z.height);else{let Y=z.width,be=z.height;for(let Ae=0;Ae<Te;Ae++)t.texImage2D(i.TEXTURE_2D,Ae,ce,Y,be,0,ne,_e,null),Y>>=1,be>>=1}}else if(_.isHTMLTexture){if("texElementImage2D"in i){let Y=i.canvas;if(Y.hasAttribute("layoutsubtree")||Y.setAttribute("layoutsubtree","true"),z.parentNode!==Y){Y.appendChild(z),f.add(_),Y.onpaint=be=>{let Ae=be.changedElements;for(let de of f)Ae.includes(de.image)&&(de.needsUpdate=!0)},Y.requestPaint();return}if(i.texElementImage2D.length===3)i.texElementImage2D(i.TEXTURE_2D,i.RGBA8,z);else{let Ae=i.RGBA,de=i.RGBA,Ve=i.UNSIGNED_BYTE;i.texElementImage2D(i.TEXTURE_2D,0,Ae,de,Ve,z)}i.texParameteri(i.TEXTURE_2D,i.TEXTURE_MIN_FILTER,i.LINEAR),i.texParameteri(i.TEXTURE_2D,i.TEXTURE_WRAP_S,i.CLAMP_TO_EDGE),i.texParameteri(i.TEXTURE_2D,i.TEXTURE_WRAP_T,i.CLAMP_TO_EDGE)}}else if(ye.length>0){if(we&&ke){let Y=ct(ye[0]);t.texStorage2D(i.TEXTURE_2D,Te,ce,Y.width,Y.height)}for(let Y=0,be=ye.length;Y<be;Y++)pe=ye[Y],we?O&&t.texSubImage2D(i.TEXTURE_2D,Y,0,0,ne,_e,pe):t.texImage2D(i.TEXTURE_2D,Y,ce,ne,_e,pe);_.generateMipmaps=!1}else if(we){if(ke){let Y=ct(z);t.texStorage2D(i.TEXTURE_2D,Te,ce,Y.width,Y.height)}O&&t.texSubImage2D(i.TEXTURE_2D,0,0,0,ne,_e,z)}else t.texImage2D(i.TEXTURE_2D,0,ce,ne,_e,z);p(_)&&T(j),Ee.__version=Me.version,_.onUpdate&&_.onUpdate(_)}P.__version=_.version}function Le(P,_,G){if(_.image.length!==6)return;let j=Xe(P,_),oe=_.source;t.bindTexture(i.TEXTURE_CUBE_MAP,P.__webglTexture,i.TEXTURE0+G);let Me=n.get(oe);if(oe.version!==Me.__version||j===!0){t.activeTexture(i.TEXTURE0+G);let Ee=dt.getPrimaries(dt.workingColorSpace),L=_.colorSpace===oi?null:dt.getPrimaries(_.colorSpace),z=_.colorSpace===oi||Ee===L?i.NONE:i.BROWSER_DEFAULT_WEBGL;t.pixelStorei(i.UNPACK_FLIP_Y_WEBGL,_.flipY),t.pixelStorei(i.UNPACK_PREMULTIPLY_ALPHA_WEBGL,_.premultiplyAlpha),t.pixelStorei(i.UNPACK_ALIGNMENT,_.unpackAlignment),t.pixelStorei(i.UNPACK_COLORSPACE_CONVERSION_WEBGL,z);let ne=_.isCompressedTexture||_.image[0].isCompressedTexture,_e=_.image[0]&&_.image[0].isDataTexture,ce=[];for(let de=0;de<6;de++)!ne&&!_e?ce[de]=m(_.image[de],!0,s.maxCubemapSize):ce[de]=_e?_.image[de].image:_.image[de],ce[de]=wt(_,ce[de]);let pe=ce[0],ye=r.convert(_.format,_.colorSpace),we=r.convert(_.type),ke=v(_.internalFormat,ye,we,_.normalized,_.colorSpace),O=_.isVideoTexture!==!0,Te=Me.__version===void 0||j===!0,Y=oe.dataReady,be=S(_,pe);$e(i.TEXTURE_CUBE_MAP,_);let Ae;if(ne){O&&Te&&t.texStorage2D(i.TEXTURE_CUBE_MAP,be,ke,pe.width,pe.height);for(let de=0;de<6;de++){Ae=ce[de].mipmaps;for(let Ve=0;Ve<Ae.length;Ve++){let ze=Ae[Ve];_.format!==Pn?ye!==null?O?Y&&t.compressedTexSubImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+de,Ve,0,0,ze.width,ze.height,ye,ze.data):t.compressedTexImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+de,Ve,ke,ze.width,ze.height,0,ze.data):Je("WebGLRenderer: Attempt to load unsupported compressed texture format in .setTextureCube()"):O?Y&&t.texSubImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+de,Ve,0,0,ze.width,ze.height,ye,we,ze.data):t.texImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+de,Ve,ke,ze.width,ze.height,0,ye,we,ze.data)}}}else{if(Ae=_.mipmaps,O&&Te){Ae.length>0&&be++;let de=ct(ce[0]);t.texStorage2D(i.TEXTURE_CUBE_MAP,be,ke,de.width,de.height)}for(let de=0;de<6;de++)if(_e){O?Y&&t.texSubImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+de,0,0,0,ce[de].width,ce[de].height,ye,we,ce[de].data):t.texImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+de,0,ke,ce[de].width,ce[de].height,0,ye,we,ce[de].data);for(let Ve=0;Ve<Ae.length;Ve++){let St=Ae[Ve].image[de].image;O?Y&&t.texSubImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+de,Ve+1,0,0,St.width,St.height,ye,we,St.data):t.texImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+de,Ve+1,ke,St.width,St.height,0,ye,we,St.data)}}else{O?Y&&t.texSubImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+de,0,0,0,ye,we,ce[de]):t.texImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+de,0,ke,ye,we,ce[de]);for(let Ve=0;Ve<Ae.length;Ve++){let ze=Ae[Ve];O?Y&&t.texSubImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+de,Ve+1,0,0,ye,we,ze.image[de]):t.texImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+de,Ve+1,ke,ye,we,ze.image[de])}}}p(_)&&T(i.TEXTURE_CUBE_MAP),Me.__version=oe.version,_.onUpdate&&_.onUpdate(_)}P.__version=_.version}function Ie(P,_,G,j,oe,Me){let Ee=r.convert(G.format,G.colorSpace),L=r.convert(G.type),z=v(G.internalFormat,Ee,L,G.normalized,G.colorSpace),ne=n.get(_),_e=n.get(G);if(_e.__renderTarget=_,!ne.__hasExternalTextures){let ce=Math.max(1,_.width>>Me),pe=Math.max(1,_.height>>Me);oe===i.TEXTURE_3D||oe===i.TEXTURE_2D_ARRAY?t.texImage3D(oe,Me,z,ce,pe,_.depth,0,Ee,L,null):t.texImage2D(oe,Me,z,ce,pe,0,Ee,L,null)}t.bindFramebuffer(i.FRAMEBUFFER,P),Et(_)?o.framebufferTexture2DMultisampleEXT(i.FRAMEBUFFER,j,oe,_e.__webglTexture,0,_t(_)):(oe===i.TEXTURE_2D||oe>=i.TEXTURE_CUBE_MAP_POSITIVE_X&&oe<=i.TEXTURE_CUBE_MAP_NEGATIVE_Z)&&i.framebufferTexture2D(i.FRAMEBUFFER,j,oe,_e.__webglTexture,Me),t.bindFramebuffer(i.FRAMEBUFFER,null)}function Ze(P,_,G){if(i.bindRenderbuffer(i.RENDERBUFFER,P),_.depthBuffer){let j=_.depthTexture,oe=j&&j.isDepthTexture?j.type:null,Me=w(_.stencilBuffer,oe),Ee=_.stencilBuffer?i.DEPTH_STENCIL_ATTACHMENT:i.DEPTH_ATTACHMENT;Et(_)?o.renderbufferStorageMultisampleEXT(i.RENDERBUFFER,_t(_),Me,_.width,_.height):G?i.renderbufferStorageMultisample(i.RENDERBUFFER,_t(_),Me,_.width,_.height):i.renderbufferStorage(i.RENDERBUFFER,Me,_.width,_.height),i.framebufferRenderbuffer(i.FRAMEBUFFER,Ee,i.RENDERBUFFER,P)}else{let j=_.textures;for(let oe=0;oe<j.length;oe++){let Me=j[oe],Ee=r.convert(Me.format,Me.colorSpace),L=r.convert(Me.type),z=v(Me.internalFormat,Ee,L,Me.normalized,Me.colorSpace);Et(_)?o.renderbufferStorageMultisampleEXT(i.RENDERBUFFER,_t(_),z,_.width,_.height):G?i.renderbufferStorageMultisample(i.RENDERBUFFER,_t(_),z,_.width,_.height):i.renderbufferStorage(i.RENDERBUFFER,z,_.width,_.height)}}i.bindRenderbuffer(i.RENDERBUFFER,null)}function ht(P,_,G){let j=_.isWebGLCubeRenderTarget===!0;if(t.bindFramebuffer(i.FRAMEBUFFER,P),!(_.depthTexture&&_.depthTexture.isDepthTexture))throw new Error("THREE.WebGLTextures: renderTarget.depthTexture must be an instance of THREE.DepthTexture.");let oe=n.get(_.depthTexture);if(oe.__renderTarget=_,(!oe.__webglTexture||_.depthTexture.image.width!==_.width||_.depthTexture.image.height!==_.height)&&(_.depthTexture.image.width=_.width,_.depthTexture.image.height=_.height,_.depthTexture.needsUpdate=!0),j){if(oe.__webglInit===void 0&&(oe.__webglInit=!0,_.depthTexture.addEventListener("dispose",I)),oe.__webglTexture===void 0){oe.__webglTexture=i.createTexture(),t.bindTexture(i.TEXTURE_CUBE_MAP,oe.__webglTexture),$e(i.TEXTURE_CUBE_MAP,_.depthTexture);let ne=r.convert(_.depthTexture.format),_e=r.convert(_.depthTexture.type),ce;_.depthTexture.format===Gn?ce=i.DEPTH_COMPONENT24:_.depthTexture.format===Ai&&(ce=i.DEPTH24_STENCIL8);for(let pe=0;pe<6;pe++)i.texImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+pe,0,ce,_.width,_.height,0,ne,_e,null)}}else Z(_.depthTexture,0);let Me=oe.__webglTexture,Ee=_t(_),L=j?i.TEXTURE_CUBE_MAP_POSITIVE_X+G:i.TEXTURE_2D,z=_.depthTexture.format===Ai?i.DEPTH_STENCIL_ATTACHMENT:i.DEPTH_ATTACHMENT;if(_.depthTexture.format===Gn)Et(_)?o.framebufferTexture2DMultisampleEXT(i.FRAMEBUFFER,z,L,Me,0,Ee):i.framebufferTexture2D(i.FRAMEBUFFER,z,L,Me,0);else if(_.depthTexture.format===Ai)Et(_)?o.framebufferTexture2DMultisampleEXT(i.FRAMEBUFFER,z,L,Me,0,Ee):i.framebufferTexture2D(i.FRAMEBUFFER,z,L,Me,0);else throw new Error("THREE.WebGLTextures: Unknown depthTexture format.")}function st(P){let _=n.get(P),G=P.isWebGLCubeRenderTarget===!0;if(_.__boundDepthTexture!==P.depthTexture){let j=P.depthTexture;if(_.__depthDisposeCallback&&_.__depthDisposeCallback(),j){let oe=()=>{delete _.__boundDepthTexture,delete _.__depthDisposeCallback,j.removeEventListener("dispose",oe)};j.addEventListener("dispose",oe),_.__depthDisposeCallback=oe}_.__boundDepthTexture=j}if(P.depthTexture&&!_.__autoAllocateDepthBuffer)if(G)for(let j=0;j<6;j++)ht(_.__webglFramebuffer[j],P,j);else{let j=P.texture.mipmaps;j&&j.length>0?ht(_.__webglFramebuffer[0],P,0):ht(_.__webglFramebuffer,P,0)}else if(G){_.__webglDepthbuffer=[];for(let j=0;j<6;j++)if(t.bindFramebuffer(i.FRAMEBUFFER,_.__webglFramebuffer[j]),_.__webglDepthbuffer[j]===void 0)_.__webglDepthbuffer[j]=i.createRenderbuffer(),Ze(_.__webglDepthbuffer[j],P,!1);else{let oe=P.stencilBuffer?i.DEPTH_STENCIL_ATTACHMENT:i.DEPTH_ATTACHMENT,Me=_.__webglDepthbuffer[j];i.bindRenderbuffer(i.RENDERBUFFER,Me),i.framebufferRenderbuffer(i.FRAMEBUFFER,oe,i.RENDERBUFFER,Me)}}else{let j=P.texture.mipmaps;if(j&&j.length>0?t.bindFramebuffer(i.FRAMEBUFFER,_.__webglFramebuffer[0]):t.bindFramebuffer(i.FRAMEBUFFER,_.__webglFramebuffer),_.__webglDepthbuffer===void 0)_.__webglDepthbuffer=i.createRenderbuffer(),Ze(_.__webglDepthbuffer,P,!1);else{let oe=P.stencilBuffer?i.DEPTH_STENCIL_ATTACHMENT:i.DEPTH_ATTACHMENT,Me=_.__webglDepthbuffer;i.bindRenderbuffer(i.RENDERBUFFER,Me),i.framebufferRenderbuffer(i.FRAMEBUFFER,oe,i.RENDERBUFFER,Me)}}t.bindFramebuffer(i.FRAMEBUFFER,null)}function it(P,_,G){let j=n.get(P);_!==void 0&&Ie(j.__webglFramebuffer,P,P.texture,i.COLOR_ATTACHMENT0,i.TEXTURE_2D,0),G!==void 0&&st(P)}function Qe(P){let _=P.texture,G=n.get(P),j=n.get(_);P.addEventListener("dispose",x);let oe=P.textures,Me=P.isWebGLCubeRenderTarget===!0,Ee=oe.length>1;if(Ee||(j.__webglTexture===void 0&&(j.__webglTexture=i.createTexture()),j.__version=_.version,a.memory.textures++),Me){G.__webglFramebuffer=[];for(let L=0;L<6;L++)if(_.mipmaps&&_.mipmaps.length>0){G.__webglFramebuffer[L]=[];for(let z=0;z<_.mipmaps.length;z++)G.__webglFramebuffer[L][z]=i.createFramebuffer()}else G.__webglFramebuffer[L]=i.createFramebuffer()}else{if(_.mipmaps&&_.mipmaps.length>0){G.__webglFramebuffer=[];for(let L=0;L<_.mipmaps.length;L++)G.__webglFramebuffer[L]=i.createFramebuffer()}else G.__webglFramebuffer=i.createFramebuffer();if(Ee)for(let L=0,z=oe.length;L<z;L++){let ne=n.get(oe[L]);ne.__webglTexture===void 0&&(ne.__webglTexture=i.createTexture(),a.memory.textures++)}if(P.samples>0&&Et(P)===!1){G.__webglMultisampledFramebuffer=i.createFramebuffer(),G.__webglColorRenderbuffer=[],t.bindFramebuffer(i.FRAMEBUFFER,G.__webglMultisampledFramebuffer);for(let L=0;L<oe.length;L++){let z=oe[L];G.__webglColorRenderbuffer[L]=i.createRenderbuffer(),i.bindRenderbuffer(i.RENDERBUFFER,G.__webglColorRenderbuffer[L]);let ne=r.convert(z.format,z.colorSpace),_e=r.convert(z.type),ce=v(z.internalFormat,ne,_e,z.normalized,z.colorSpace,P.isXRRenderTarget===!0),pe=_t(P);i.renderbufferStorageMultisample(i.RENDERBUFFER,pe,ce,P.width,P.height),i.framebufferRenderbuffer(i.FRAMEBUFFER,i.COLOR_ATTACHMENT0+L,i.RENDERBUFFER,G.__webglColorRenderbuffer[L])}i.bindRenderbuffer(i.RENDERBUFFER,null),P.depthBuffer&&(G.__webglDepthRenderbuffer=i.createRenderbuffer(),Ze(G.__webglDepthRenderbuffer,P,!0)),t.bindFramebuffer(i.FRAMEBUFFER,null)}}if(Me){t.bindTexture(i.TEXTURE_CUBE_MAP,j.__webglTexture),$e(i.TEXTURE_CUBE_MAP,_);for(let L=0;L<6;L++)if(_.mipmaps&&_.mipmaps.length>0)for(let z=0;z<_.mipmaps.length;z++)Ie(G.__webglFramebuffer[L][z],P,_,i.COLOR_ATTACHMENT0,i.TEXTURE_CUBE_MAP_POSITIVE_X+L,z);else Ie(G.__webglFramebuffer[L],P,_,i.COLOR_ATTACHMENT0,i.TEXTURE_CUBE_MAP_POSITIVE_X+L,0);p(_)&&T(i.TEXTURE_CUBE_MAP),t.unbindTexture()}else if(Ee){for(let L=0,z=oe.length;L<z;L++){let ne=oe[L],_e=n.get(ne),ce=i.TEXTURE_2D;(P.isWebGL3DRenderTarget||P.isWebGLArrayRenderTarget)&&(ce=P.isWebGL3DRenderTarget?i.TEXTURE_3D:i.TEXTURE_2D_ARRAY),t.bindTexture(ce,_e.__webglTexture),$e(ce,ne),Ie(G.__webglFramebuffer,P,ne,i.COLOR_ATTACHMENT0+L,ce,0),p(ne)&&T(ce)}t.unbindTexture()}else{let L=i.TEXTURE_2D;if((P.isWebGL3DRenderTarget||P.isWebGLArrayRenderTarget)&&(L=P.isWebGL3DRenderTarget?i.TEXTURE_3D:i.TEXTURE_2D_ARRAY),t.bindTexture(L,j.__webglTexture),$e(L,_),_.mipmaps&&_.mipmaps.length>0)for(let z=0;z<_.mipmaps.length;z++)Ie(G.__webglFramebuffer[z],P,_,i.COLOR_ATTACHMENT0,L,z);else Ie(G.__webglFramebuffer,P,_,i.COLOR_ATTACHMENT0,L,0);p(_)&&T(L),t.unbindTexture()}P.depthBuffer&&st(P)}function rt(P){let _=P.textures;for(let G=0,j=_.length;G<j;G++){let oe=_[G];if(p(oe)){let Me=C(P),Ee=n.get(oe).__webglTexture;t.bindTexture(Me,Ee),T(Me),t.unbindTexture()}}}let gt=[],Ct=[];function Ut(P){if(P.samples>0){if(Et(P)===!1){let _=P.textures,G=P.width,j=P.height,oe=i.COLOR_BUFFER_BIT,Me=P.stencilBuffer?i.DEPTH_STENCIL_ATTACHMENT:i.DEPTH_ATTACHMENT,Ee=n.get(P),L=_.length>1;if(L)for(let ne=0;ne<_.length;ne++)t.bindFramebuffer(i.FRAMEBUFFER,Ee.__webglMultisampledFramebuffer),i.framebufferRenderbuffer(i.FRAMEBUFFER,i.COLOR_ATTACHMENT0+ne,i.RENDERBUFFER,null),t.bindFramebuffer(i.FRAMEBUFFER,Ee.__webglFramebuffer),i.framebufferTexture2D(i.DRAW_FRAMEBUFFER,i.COLOR_ATTACHMENT0+ne,i.TEXTURE_2D,null,0);t.bindFramebuffer(i.READ_FRAMEBUFFER,Ee.__webglMultisampledFramebuffer);let z=P.texture.mipmaps;z&&z.length>0?t.bindFramebuffer(i.DRAW_FRAMEBUFFER,Ee.__webglFramebuffer[0]):t.bindFramebuffer(i.DRAW_FRAMEBUFFER,Ee.__webglFramebuffer);for(let ne=0;ne<_.length;ne++){if(P.resolveDepthBuffer&&(P.depthBuffer&&(oe|=i.DEPTH_BUFFER_BIT),P.stencilBuffer&&P.resolveStencilBuffer&&(oe|=i.STENCIL_BUFFER_BIT)),L){i.framebufferRenderbuffer(i.READ_FRAMEBUFFER,i.COLOR_ATTACHMENT0,i.RENDERBUFFER,Ee.__webglColorRenderbuffer[ne]);let _e=n.get(_[ne]).__webglTexture;i.framebufferTexture2D(i.DRAW_FRAMEBUFFER,i.COLOR_ATTACHMENT0,i.TEXTURE_2D,_e,0)}i.blitFramebuffer(0,0,G,j,0,0,G,j,oe,i.NEAREST),l===!0&&(gt.length=0,Ct.length=0,gt.push(i.COLOR_ATTACHMENT0+ne),P.depthBuffer&&P.storeMultisampledDepthBuffer===!1&&(gt.push(Me),Ct.push(Me),i.invalidateFramebuffer(i.DRAW_FRAMEBUFFER,Ct)),i.invalidateFramebuffer(i.READ_FRAMEBUFFER,gt))}if(t.bindFramebuffer(i.READ_FRAMEBUFFER,null),t.bindFramebuffer(i.DRAW_FRAMEBUFFER,null),L)for(let ne=0;ne<_.length;ne++){t.bindFramebuffer(i.FRAMEBUFFER,Ee.__webglMultisampledFramebuffer),i.framebufferRenderbuffer(i.FRAMEBUFFER,i.COLOR_ATTACHMENT0+ne,i.RENDERBUFFER,Ee.__webglColorRenderbuffer[ne]);let _e=n.get(_[ne]).__webglTexture;t.bindFramebuffer(i.FRAMEBUFFER,Ee.__webglFramebuffer),i.framebufferTexture2D(i.DRAW_FRAMEBUFFER,i.COLOR_ATTACHMENT0+ne,i.TEXTURE_2D,_e,0)}t.bindFramebuffer(i.DRAW_FRAMEBUFFER,Ee.__webglMultisampledFramebuffer)}else if(P.depthBuffer&&P.storeMultisampledDepthBuffer===!1&&l){let _=P.stencilBuffer?i.DEPTH_STENCIL_ATTACHMENT:i.DEPTH_ATTACHMENT;i.invalidateFramebuffer(i.DRAW_FRAMEBUFFER,[_])}}}function _t(P){return Math.min(s.maxSamples,P.samples)}function Et(P){let _=n.get(P);return P.samples>0&&e.has("WEBGL_multisampled_render_to_texture")===!0&&_.__useRenderToTexture!==!1}function B(P){let _=a.render.frame;h.get(P)!==_&&(h.set(P,_),P.update())}function wt(P,_){let G=P.colorSpace,j=P.format,oe=P.type;return P.isCompressedTexture===!0||P.isVideoTexture===!0||G!==ir&&G!==oi&&(dt.getTransfer(G)===bt?(j!==Pn||oe!==xn)&&Je("WebGLTextures: sRGB encoded textures have to use RGBAFormat and UnsignedByteType."):et("WebGLTextures: Unsupported texture color space:",G)),_}function ct(P){return typeof HTMLImageElement<"u"&&P instanceof HTMLImageElement?(c.width=P.naturalWidth||P.width,c.height=P.naturalHeight||P.height):typeof VideoFrame<"u"&&P instanceof VideoFrame?(c.width=P.displayWidth,c.height=P.displayHeight):(c.width=P.width,c.height=P.height),c}this.allocateTextureUnit=ee,this.resetTextureUnits=$,this.getTextureUnits=U,this.setTextureUnits=W,this.setTexture2D=Z,this.setTexture2DArray=Q,this.setTexture3D=ue,this.setTextureCube=se,this.rebindTextures=it,this.setupRenderTarget=Qe,this.updateRenderTargetMipmap=rt,this.updateMultisampleRenderTarget=Ut,this.setupDepthRenderbuffer=st,this.setupFrameBufferTexture=Ie,this.useMultisampledRTT=Et,this.isReversedDepthBuffer=function(){return t.buffers.depth.getReversed()}}function k0(i,e){function t(n,s=oi){let r,a=dt.getTransfer(s);if(n===xn)return i.UNSIGNED_BYTE;if(n===mo)return i.UNSIGNED_SHORT_4_4_4_4;if(n===go)return i.UNSIGNED_SHORT_5_5_5_1;if(n===sc)return i.UNSIGNED_INT_5_9_9_9_REV;if(n===rc)return i.UNSIGNED_INT_10F_11F_11F_REV;if(n===nc)return i.BYTE;if(n===ic)return i.SHORT;if(n===Ls)return i.UNSIGNED_SHORT;if(n===po)return i.INT;if(n===Bn)return i.UNSIGNED_INT;if(n===Rn)return i.FLOAT;if(n===tn)return i.HALF_FLOAT;if(n===ac)return i.ALPHA;if(n===oc)return i.RGB;if(n===Pn)return i.RGBA;if(n===Gn)return i.DEPTH_COMPONENT;if(n===Ai)return i.DEPTH_STENCIL;if(n===_o)return i.RED;if(n===xo)return i.RED_INTEGER;if(n===Ci)return i.RG;if(n===vo)return i.RG_INTEGER;if(n===yo)return i.RGBA_INTEGER;if(n===Or||n===Br||n===zr||n===Vr)if(a===bt)if(r=e.get("WEBGL_compressed_texture_s3tc_srgb"),r!==null){if(n===Or)return r.COMPRESSED_SRGB_S3TC_DXT1_EXT;if(n===Br)return r.COMPRESSED_SRGB_ALPHA_S3TC_DXT1_EXT;if(n===zr)return r.COMPRESSED_SRGB_ALPHA_S3TC_DXT3_EXT;if(n===Vr)return r.COMPRESSED_SRGB_ALPHA_S3TC_DXT5_EXT}else return null;else if(r=e.get("WEBGL_compressed_texture_s3tc"),r!==null){if(n===Or)return r.COMPRESSED_RGB_S3TC_DXT1_EXT;if(n===Br)return r.COMPRESSED_RGBA_S3TC_DXT1_EXT;if(n===zr)return r.COMPRESSED_RGBA_S3TC_DXT3_EXT;if(n===Vr)return r.COMPRESSED_RGBA_S3TC_DXT5_EXT}else return null;if(n===Mo||n===bo||n===So||n===To)if(r=e.get("WEBGL_compressed_texture_pvrtc"),r!==null){if(n===Mo)return r.COMPRESSED_RGB_PVRTC_4BPPV1_IMG;if(n===bo)return r.COMPRESSED_RGB_PVRTC_2BPPV1_IMG;if(n===So)return r.COMPRESSED_RGBA_PVRTC_4BPPV1_IMG;if(n===To)return r.COMPRESSED_RGBA_PVRTC_2BPPV1_IMG}else return null;if(n===Eo||n===wo||n===Ao||n===Co||n===Ro||n===Hr||n===Po)if(r=e.get("WEBGL_compressed_texture_etc"),r!==null){if(n===Eo||n===wo)return a===bt?r.COMPRESSED_SRGB8_ETC2:r.COMPRESSED_RGB8_ETC2;if(n===Ao)return a===bt?r.COMPRESSED_SRGB8_ALPHA8_ETC2_EAC:r.COMPRESSED_RGBA8_ETC2_EAC;if(n===Co)return r.COMPRESSED_R11_EAC;if(n===Ro)return r.COMPRESSED_SIGNED_R11_EAC;if(n===Hr)return r.COMPRESSED_RG11_EAC;if(n===Po)return r.COMPRESSED_SIGNED_RG11_EAC}else return null;if(n===Io||n===Lo||n===No||n===Do||n===Uo||n===Fo||n===ko||n===Oo||n===Bo||n===zo||n===Vo||n===Ho||n===Go||n===Wo)if(r=e.get("WEBGL_compressed_texture_astc"),r!==null){if(n===Io)return a===bt?r.COMPRESSED_SRGB8_ALPHA8_ASTC_4x4_KHR:r.COMPRESSED_RGBA_ASTC_4x4_KHR;if(n===Lo)return a===bt?r.COMPRESSED_SRGB8_ALPHA8_ASTC_5x4_KHR:r.COMPRESSED_RGBA_ASTC_5x4_KHR;if(n===No)return a===bt?r.COMPRESSED_SRGB8_ALPHA8_ASTC_5x5_KHR:r.COMPRESSED_RGBA_ASTC_5x5_KHR;if(n===Do)return a===bt?r.COMPRESSED_SRGB8_ALPHA8_ASTC_6x5_KHR:r.COMPRESSED_RGBA_ASTC_6x5_KHR;if(n===Uo)return a===bt?r.COMPRESSED_SRGB8_ALPHA8_ASTC_6x6_KHR:r.COMPRESSED_RGBA_ASTC_6x6_KHR;if(n===Fo)return a===bt?r.COMPRESSED_SRGB8_ALPHA8_ASTC_8x5_KHR:r.COMPRESSED_RGBA_ASTC_8x5_KHR;if(n===ko)return a===bt?r.COMPRESSED_SRGB8_ALPHA8_ASTC_8x6_KHR:r.COMPRESSED_RGBA_ASTC_8x6_KHR;if(n===Oo)return a===bt?r.COMPRESSED_SRGB8_ALPHA8_ASTC_8x8_KHR:r.COMPRESSED_RGBA_ASTC_8x8_KHR;if(n===Bo)return a===bt?r.COMPRESSED_SRGB8_ALPHA8_ASTC_10x5_KHR:r.COMPRESSED_RGBA_ASTC_10x5_KHR;if(n===zo)return a===bt?r.COMPRESSED_SRGB8_ALPHA8_ASTC_10x6_KHR:r.COMPRESSED_RGBA_ASTC_10x6_KHR;if(n===Vo)return a===bt?r.COMPRESSED_SRGB8_ALPHA8_ASTC_10x8_KHR:r.COMPRESSED_RGBA_ASTC_10x8_KHR;if(n===Ho)return a===bt?r.COMPRESSED_SRGB8_ALPHA8_ASTC_10x10_KHR:r.COMPRESSED_RGBA_ASTC_10x10_KHR;if(n===Go)return a===bt?r.COMPRESSED_SRGB8_ALPHA8_ASTC_12x10_KHR:r.COMPRESSED_RGBA_ASTC_12x10_KHR;if(n===Wo)return a===bt?r.COMPRESSED_SRGB8_ALPHA8_ASTC_12x12_KHR:r.COMPRESSED_RGBA_ASTC_12x12_KHR}else return null;if(n===qo||n===Xo||n===$o)if(r=e.get("EXT_texture_compression_bptc"),r!==null){if(n===qo)return a===bt?r.COMPRESSED_SRGB_ALPHA_BPTC_UNORM_EXT:r.COMPRESSED_RGBA_BPTC_UNORM_EXT;if(n===Xo)return r.COMPRESSED_RGB_BPTC_SIGNED_FLOAT_EXT;if(n===$o)return r.COMPRESSED_RGB_BPTC_UNSIGNED_FLOAT_EXT}else return null;if(n===Yo||n===Zo||n===Gr||n===jo)if(r=e.get("EXT_texture_compression_rgtc"),r!==null){if(n===Yo)return r.COMPRESSED_RED_RGTC1_EXT;if(n===Zo)return r.COMPRESSED_SIGNED_RED_RGTC1_EXT;if(n===Gr)return r.COMPRESSED_RED_GREEN_RGTC2_EXT;if(n===jo)return r.COMPRESSED_SIGNED_RED_GREEN_RGTC2_EXT}else return null;return n===Ns?i.UNSIGNED_INT_24_8:i[n]!==void 0?i[n]:null}return{convert:t}}var O0=`
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

}`,Pc=class{constructor(){this.texture=null,this.mesh=null,this.depthNear=0,this.depthFar=0}init(e,t){if(this.texture===null){let n=new mr(e.texture);(e.depthNear!==t.depthNear||e.depthFar!==t.depthFar)&&(this.depthNear=e.depthNear,this.depthFar=e.depthFar),this.texture=n}}getMesh(e){if(this.texture!==null&&this.mesh===null){let t=e.cameras[0].viewport,n=new Ot({vertexShader:O0,fragmentShader:B0,uniforms:{depthColor:{value:this.texture},depthWidth:{value:t.z},depthHeight:{value:t.w}}});this.mesh=new yt(new yr(20,20),n)}return this.mesh}reset(){this.texture=null,this.mesh=null}getDepthTexture(){return this.texture}},Ic=class extends Wn{constructor(e,t){super();let n=this,s=null,r=1,a=null,o="local-floor",l=1,c=null,h=null,f=null,u=null,d=null,g=null,M=typeof XRWebGLBinding<"u",m=new Pc,p={},T=t.getContextAttributes(),C=null,v=null,w=[],S=[],I=new Ue,x=null,A=null,N=new Jt;N.viewport=new Dt;let k=new Jt;k.viewport=new Dt;let V=[N,k],$=new lo,U=null,W=null;this.cameraAutoUpdate=!0,this.enabled=!1,this.isPresenting=!1,this.getController=function(K){let re=w[K];return re===void 0&&(re=new bs,w[K]=re),re.getTargetRaySpace()},this.getControllerGrip=function(K){let re=w[K];return re===void 0&&(re=new bs,w[K]=re),re.getGripSpace()},this.getHand=function(K){let re=w[K];return re===void 0&&(re=new bs,w[K]=re),re.getHandSpace()};function ee(K){let re=S.indexOf(K.inputSource);if(re===-1)return;let Se=w[re];Se!==void 0&&(Se.update(K.inputSource,K.frame,c||a),Se.dispatchEvent({type:K.type,data:K.inputSource}))}function ie(){s.removeEventListener("select",ee),s.removeEventListener("selectstart",ee),s.removeEventListener("selectend",ee),s.removeEventListener("squeeze",ee),s.removeEventListener("squeezestart",ee),s.removeEventListener("squeezeend",ee),s.removeEventListener("end",ie),s.removeEventListener("inputsourceschange",Z);for(let K=0;K<w.length;K++){let re=S[K];re!==null&&(S[K]=null,w[K].disconnect(re))}U=null,W=null,m.reset();for(let K in p)delete p[K];if(e.setRenderTarget(C),d=null,u=null,f=null,s=null,v=null,Xe.stop(),n.isPresenting=!1,e.setPixelRatio(x),e.setSize(I.width,I.height,!1),A!==null){let K=A.camera;K.fov=A.fov,K.zoom=A.zoom,K.updateProjectionMatrix(),A=null}n.dispatchEvent({type:"sessionend"})}this.setFramebufferScaleFactor=function(K){r=K,n.isPresenting===!0&&Je("WebXRManager: Cannot change framebuffer scale while presenting.")},this.setReferenceSpaceType=function(K){o=K,n.isPresenting===!0&&Je("WebXRManager: Cannot change reference space type while presenting.")},this.getReferenceSpace=function(){return c||a},this.setReferenceSpace=function(K){c=K},this.getBaseLayer=function(){return u!==null?u:d},this.getBinding=function(){return f===null&&M&&(f=new XRWebGLBinding(s,t)),f},this.getFrame=function(){return g},this.getSession=function(){return s},this.setSession=async function(K){if(s=K,s!==null){if(C=e.getRenderTarget(),s.addEventListener("select",ee),s.addEventListener("selectstart",ee),s.addEventListener("selectend",ee),s.addEventListener("squeeze",ee),s.addEventListener("squeezestart",ee),s.addEventListener("squeezeend",ee),s.addEventListener("end",ie),s.addEventListener("inputsourceschange",Z),T.xrCompatible!==!0&&await t.makeXRCompatible(),x=e.getPixelRatio(),e.getSize(I),M&&"createProjectionLayer"in XRWebGLBinding.prototype){let Se=null,Le=null,Ie=null;T.depth&&(Ie=T.stencil?t.DEPTH24_STENCIL8:t.DEPTH_COMPONENT24,Se=T.stencil?Ai:Gn,Le=T.stencil?Ns:Bn);let Ze={colorFormat:t.RGBA8,depthFormat:Ie,scaleFactor:r};f=this.getBinding(),u=f.createProjectionLayer(Ze),s.updateRenderState({layers:[u]}),e.setPixelRatio(1),e.setSize(u.textureWidth,u.textureHeight,!1),v=new Vt(u.textureWidth,u.textureHeight,{format:Pn,type:xn,depthTexture:new vi(u.textureWidth,u.textureHeight,Le,void 0,void 0,void 0,void 0,void 0,void 0,Se),stencilBuffer:T.stencil,colorSpace:e.outputColorSpace,samples:T.antialias?4:0,resolveDepthBuffer:u.ignoreDepthValues===!1,resolveStencilBuffer:u.ignoreDepthValues===!1,storeMultisampledDepthBuffer:u.ignoreDepthValues===!1,storeMultisampledStencilBuffer:u.ignoreDepthValues===!1})}else{let Se={antialias:T.antialias,alpha:!0,depth:T.depth,stencil:T.stencil,framebufferScaleFactor:r};d=new XRWebGLLayer(s,t,Se),s.updateRenderState({baseLayer:d}),e.setPixelRatio(1),e.setSize(d.framebufferWidth,d.framebufferHeight,!1),v=new Vt(d.framebufferWidth,d.framebufferHeight,{format:Pn,type:xn,colorSpace:e.outputColorSpace,stencilBuffer:T.stencil,resolveDepthBuffer:d.ignoreDepthValues===!1,resolveStencilBuffer:d.ignoreDepthValues===!1,storeMultisampledDepthBuffer:d.ignoreDepthValues===!1,storeMultisampledStencilBuffer:d.ignoreDepthValues===!1})}v.isXRRenderTarget=!0,this.setFoveation(l),c=null,a=await s.requestReferenceSpace(o),Xe.setContext(s),Xe.start(),n.isPresenting=!0,n.dispatchEvent({type:"sessionstart"})}},this.getEnvironmentBlendMode=function(){if(s!==null)return s.environmentBlendMode},this.getDepthTexture=function(){return m.getDepthTexture()};function Z(K){for(let re=0;re<K.removed.length;re++){let Se=K.removed[re],Le=S.indexOf(Se);Le>=0&&(S[Le]=null,w[Le].disconnect(Se))}for(let re=0;re<K.added.length;re++){let Se=K.added[re],Le=S.indexOf(Se);if(Le===-1){for(let Ze=0;Ze<w.length;Ze++)if(Ze>=S.length){S.push(Se),Le=Ze;break}else if(S[Ze]===null){S[Ze]=Se,Le=Ze;break}if(Le===-1)break}let Ie=w[Le];Ie&&Ie.connect(Se)}}let Q=new D,ue=new D;function se(K,re,Se){Q.setFromMatrixPosition(re.matrixWorld),ue.setFromMatrixPosition(Se.matrixWorld);let Le=Q.distanceTo(ue),Ie=re.projectionMatrix.elements,Ze=Se.projectionMatrix.elements,ht=Ie[14]/(Ie[10]-1),st=Ie[14]/(Ie[10]+1),it=(Ie[9]+1)/Ie[5],Qe=(Ie[9]-1)/Ie[5],rt=(Ie[8]-1)/Ie[0],gt=(Ze[8]+1)/Ze[0],Ct=ht*rt,Ut=ht*gt,_t=Le/(-rt+gt),Et=_t*-rt;if(re.matrixWorld.decompose(K.position,K.quaternion,K.scale),K.translateX(Et),K.translateZ(_t),K.matrixWorld.compose(K.position,K.quaternion,K.scale),K.matrixWorldInverse.copy(K.matrixWorld).invert(),Ie[10]===-1)K.projectionMatrix.copy(re.projectionMatrix),K.projectionMatrixInverse.copy(re.projectionMatrixInverse);else{let B=ht+_t,wt=st+_t,ct=Ct-Et,P=Ut+(Le-Et),_=it*st/wt*B,G=Qe*st/wt*B;K.projectionMatrix.makePerspective(ct,P,_,G,B,wt),K.projectionMatrixInverse.copy(K.projectionMatrix).invert()}}function Ge(K,re){re===null?K.matrixWorld.copy(K.matrix):K.matrixWorld.multiplyMatrices(re.matrixWorld,K.matrix),K.matrixWorldInverse.copy(K.matrixWorld).invert()}this.updateCamera=function(K){if(s===null)return;let re=K.near,Se=K.far;m.texture!==null&&(m.depthNear>0&&(re=m.depthNear),m.depthFar>0&&(Se=m.depthFar)),$.near=k.near=N.near=re,$.far=k.far=N.far=Se,(U!==$.near||W!==$.far)&&(s.updateRenderState({depthNear:$.near,depthFar:$.far}),U=$.near,W=$.far),$.layers.mask=K.layers.mask|6,N.layers.mask=$.layers.mask&-5,k.layers.mask=$.layers.mask&-3;let Le=K.parent,Ie=$.cameras;Ge($,Le);for(let Ze=0;Ze<Ie.length;Ze++)Ge(Ie[Ze],Le);Ie.length===2?se($,N,k):$.projectionMatrix.copy(N.projectionMatrix),A===null&&K.isPerspectiveCamera&&(A={camera:K,fov:K.fov,zoom:K.zoom}),Pe(K,$,Le)};function Pe(K,re,Se){Se===null?K.matrix.copy(re.matrixWorld):(K.matrix.copy(Se.matrixWorld),K.matrix.invert(),K.matrix.multiply(re.matrixWorld)),K.matrix.decompose(K.position,K.quaternion,K.scale),K.updateMatrixWorld(!0),K.projectionMatrix.copy(re.projectionMatrix),K.projectionMatrixInverse.copy(re.projectionMatrixInverse),K.isPerspectiveCamera&&(K.fov=vs*2*Math.atan(1/K.projectionMatrix.elements[5]),K.zoom=1)}this.getCamera=function(){return $},this.getFoveation=function(){if(!(u===null&&d===null))return l},this.setFoveation=function(K){l=K,u!==null&&(u.fixedFoveation=K),d!==null&&d.fixedFoveation!==void 0&&(d.fixedFoveation=K)},this.hasDepthSensing=function(){return m.texture!==null},this.getDepthSensingMesh=function(){return m.getMesh($)},this.getCameraTexture=function(K){return p[K]};let ot=null;function $e(K,re){if(h=re.getViewerPose(c||a),g=re,h!==null){let Se=h.views;d!==null&&(e.setRenderTargetFramebuffer(v,d.framebuffer),e.setRenderTarget(v));let Le=!1;Se.length!==$.cameras.length&&($.cameras.length=0,Le=!0);for(let st=0;st<Se.length;st++){let it=Se[st],Qe=null;if(d!==null)Qe=d.getViewport(it);else{let gt=f.getViewSubImage(u,it);Qe=gt.viewport,st===0&&(e.setRenderTargetTextures(v,gt.colorTexture,gt.depthStencilTexture),e.setRenderTarget(v))}let rt=V[st];rt===void 0&&(rt=new Jt,rt.layers.enable(st),rt.viewport=new Dt,V[st]=rt),rt.matrix.fromArray(it.transform.matrix),rt.matrix.decompose(rt.position,rt.quaternion,rt.scale),rt.projectionMatrix.fromArray(it.projectionMatrix),rt.projectionMatrixInverse.copy(rt.projectionMatrix).invert(),rt.viewport.set(Qe.x,Qe.y,Qe.width,Qe.height),st===0&&($.matrix.copy(rt.matrix),$.matrix.decompose($.position,$.quaternion,$.scale)),Le===!0&&$.cameras.push(rt)}let Ie=s.enabledFeatures;if(Ie&&Ie.includes("depth-sensing")&&s.depthUsage=="gpu-optimized"&&M){f=n.getBinding();let st=f.getDepthInformation(Se[0]);st&&st.isValid&&st.texture&&m.init(st,s.renderState)}if(Ie&&Ie.includes("camera-access")&&M){e.state.unbindTexture(),f=n.getBinding();for(let st=0;st<Se.length;st++){let it=Se[st].camera;if(it){let Qe=p[it];Qe||(Qe=new mr,p[it]=Qe);let rt=f.getCameraImage(it);Qe.sourceTexture=rt}}}}for(let Se=0;Se<w.length;Se++){let Le=S[Se],Ie=w[Se];Le!==null&&Ie!==void 0&&Ie.update(Le,re,c||a)}ot&&ot(K,re),re.detectedPlanes&&n.dispatchEvent({type:"planesdetected",data:re}),g=null}let Xe=new Th;Xe.setAnimationLoop($e),this.setAnimationLoop=function(K){ot=K},this.dispose=function(){}}},z0=new pt,Ph=new nt;Ph.set(-1,0,0,0,1,0,0,0,1);function V0(i,e){function t(m,p){m.matrixAutoUpdate===!0&&m.updateMatrix(),p.value.copy(m.matrix)}function n(m,p){p.color.getRGB(m.fogColor.value,fc(i)),p.isFog?(m.fogNear.value=p.near,m.fogFar.value=p.far):p.isFogExp2&&(m.fogDensity.value=p.density)}function s(m,p,T,C,v){p.isNodeMaterial?p.uniformsNeedUpdate=!1:p.isMeshBasicMaterial?r(m,p):p.isMeshLambertMaterial?(r(m,p),p.envMap&&(m.envMapIntensity.value=p.envMapIntensity)):p.isMeshToonMaterial?(r(m,p),f(m,p)):p.isMeshPhongMaterial?(r(m,p),h(m,p),p.envMap&&(m.envMapIntensity.value=p.envMapIntensity)):p.isMeshStandardMaterial?(r(m,p),u(m,p),p.isMeshPhysicalMaterial&&d(m,p,v)):p.isMeshMatcapMaterial?(r(m,p),g(m,p)):p.isMeshDepthMaterial?r(m,p):p.isMeshDistanceMaterial?(r(m,p),M(m,p)):p.isMeshNormalMaterial?r(m,p):p.isLineBasicMaterial?(a(m,p),p.isLineDashedMaterial&&o(m,p)):p.isPointsMaterial?l(m,p,T,C):p.isSpriteMaterial?c(m,p):p.isShadowMaterial?(m.color.value.copy(p.color),m.opacity.value=p.opacity):p.isShaderMaterial&&(p.uniformsNeedUpdate=!1)}function r(m,p){m.opacity.value=p.opacity,p.color&&m.diffuse.value.copy(p.color),p.emissive&&m.emissive.value.copy(p.emissive).multiplyScalar(p.emissiveIntensity),p.map&&(m.map.value=p.map,t(p.map,m.mapTransform)),p.alphaMap&&(m.alphaMap.value=p.alphaMap,t(p.alphaMap,m.alphaMapTransform)),p.bumpMap&&(m.bumpMap.value=p.bumpMap,t(p.bumpMap,m.bumpMapTransform),m.bumpScale.value=p.bumpScale,p.side===en&&(m.bumpScale.value*=-1)),p.normalMap&&(m.normalMap.value=p.normalMap,t(p.normalMap,m.normalMapTransform),m.normalScale.value.copy(p.normalScale),p.side===en&&m.normalScale.value.negate()),p.displacementMap&&(m.displacementMap.value=p.displacementMap,t(p.displacementMap,m.displacementMapTransform),m.displacementScale.value=p.displacementScale,m.displacementBias.value=p.displacementBias),p.emissiveMap&&(m.emissiveMap.value=p.emissiveMap,t(p.emissiveMap,m.emissiveMapTransform)),p.specularMap&&(m.specularMap.value=p.specularMap,t(p.specularMap,m.specularMapTransform)),p.alphaTest>0&&(m.alphaTest.value=p.alphaTest);let T=e.get(p),C=T.envMap,v=T.envMapRotation;C&&(m.envMap.value=C,m.envMapRotation.value.setFromMatrix4(z0.makeRotationFromEuler(v)).transpose(),C.isCubeTexture&&C.isRenderTargetTexture===!1&&m.envMapRotation.value.premultiply(Ph),m.reflectivity.value=p.reflectivity,m.ior.value=p.ior,m.refractionRatio.value=p.refractionRatio),p.lightMap&&(m.lightMap.value=p.lightMap,m.lightMapIntensity.value=p.lightMapIntensity,t(p.lightMap,m.lightMapTransform)),p.aoMap&&(m.aoMap.value=p.aoMap,m.aoMapIntensity.value=p.aoMapIntensity,t(p.aoMap,m.aoMapTransform))}function a(m,p){m.diffuse.value.copy(p.color),m.opacity.value=p.opacity,p.map&&(m.map.value=p.map,t(p.map,m.mapTransform))}function o(m,p){m.dashSize.value=p.dashSize,m.totalSize.value=p.dashSize+p.gapSize,m.scale.value=p.scale}function l(m,p,T,C){m.diffuse.value.copy(p.color),m.opacity.value=p.opacity,m.size.value=p.size*T,m.scale.value=C*.5,p.map&&(m.map.value=p.map,t(p.map,m.uvTransform)),p.alphaMap&&(m.alphaMap.value=p.alphaMap,t(p.alphaMap,m.alphaMapTransform)),p.alphaTest>0&&(m.alphaTest.value=p.alphaTest)}function c(m,p){m.diffuse.value.copy(p.color),m.opacity.value=p.opacity,m.rotation.value=p.rotation,p.map&&(m.map.value=p.map,t(p.map,m.mapTransform)),p.alphaMap&&(m.alphaMap.value=p.alphaMap,t(p.alphaMap,m.alphaMapTransform)),p.alphaTest>0&&(m.alphaTest.value=p.alphaTest)}function h(m,p){m.specular.value.copy(p.specular),m.shininess.value=Math.max(p.shininess,1e-4)}function f(m,p){p.gradientMap&&(m.gradientMap.value=p.gradientMap)}function u(m,p){m.metalness.value=p.metalness,p.metalnessMap&&(m.metalnessMap.value=p.metalnessMap,t(p.metalnessMap,m.metalnessMapTransform)),m.roughness.value=p.roughness,p.roughnessMap&&(m.roughnessMap.value=p.roughnessMap,t(p.roughnessMap,m.roughnessMapTransform)),p.envMap&&(m.envMapIntensity.value=p.envMapIntensity)}function d(m,p,T){m.ior.value=p.ior,p.sheen>0&&(m.sheenColor.value.copy(p.sheenColor).multiplyScalar(p.sheen),m.sheenRoughness.value=p.sheenRoughness,p.sheenColorMap&&(m.sheenColorMap.value=p.sheenColorMap,t(p.sheenColorMap,m.sheenColorMapTransform)),p.sheenRoughnessMap&&(m.sheenRoughnessMap.value=p.sheenRoughnessMap,t(p.sheenRoughnessMap,m.sheenRoughnessMapTransform))),p.clearcoat>0&&(m.clearcoat.value=p.clearcoat,m.clearcoatRoughness.value=p.clearcoatRoughness,p.clearcoatMap&&(m.clearcoatMap.value=p.clearcoatMap,t(p.clearcoatMap,m.clearcoatMapTransform)),p.clearcoatRoughnessMap&&(m.clearcoatRoughnessMap.value=p.clearcoatRoughnessMap,t(p.clearcoatRoughnessMap,m.clearcoatRoughnessMapTransform)),p.clearcoatNormalMap&&(m.clearcoatNormalMap.value=p.clearcoatNormalMap,t(p.clearcoatNormalMap,m.clearcoatNormalMapTransform),m.clearcoatNormalScale.value.copy(p.clearcoatNormalScale),p.side===en&&m.clearcoatNormalScale.value.negate())),p.dispersion>0&&(m.dispersion.value=p.dispersion),p.retroreflectivity>0&&(m.retroreflectivity.value=p.retroreflectivity),p.iridescence>0&&(m.iridescence.value=p.iridescence,m.iridescenceIOR.value=p.iridescenceIOR,m.iridescenceThicknessMinimum.value=p.iridescenceThicknessRange[0],m.iridescenceThicknessMaximum.value=p.iridescenceThicknessRange[1],p.iridescenceMap&&(m.iridescenceMap.value=p.iridescenceMap,t(p.iridescenceMap,m.iridescenceMapTransform)),p.iridescenceThicknessMap&&(m.iridescenceThicknessMap.value=p.iridescenceThicknessMap,t(p.iridescenceThicknessMap,m.iridescenceThicknessMapTransform))),p.transmission>0&&(m.transmission.value=p.transmission,m.transmissionSamplerMap.value=T.texture,m.transmissionSamplerSize.value.set(T.width,T.height),p.transmissionMap&&(m.transmissionMap.value=p.transmissionMap,t(p.transmissionMap,m.transmissionMapTransform)),m.thickness.value=p.thickness,p.thicknessMap&&(m.thicknessMap.value=p.thicknessMap,t(p.thicknessMap,m.thicknessMapTransform)),m.attenuationDistance.value=p.attenuationDistance,m.attenuationColor.value.copy(p.attenuationColor)),p.anisotropy>0&&(m.anisotropyVector.value.set(p.anisotropy*Math.cos(p.anisotropyRotation),p.anisotropy*Math.sin(p.anisotropyRotation)),p.anisotropyMap&&(m.anisotropyMap.value=p.anisotropyMap,t(p.anisotropyMap,m.anisotropyMapTransform))),m.specularIntensity.value=p.specularIntensity,m.specularColor.value.copy(p.specularColor),p.specularColorMap&&(m.specularColorMap.value=p.specularColorMap,t(p.specularColorMap,m.specularColorMapTransform)),p.specularIntensityMap&&(m.specularIntensityMap.value=p.specularIntensityMap,t(p.specularIntensityMap,m.specularIntensityMapTransform))}function g(m,p){p.matcap&&(m.matcap.value=p.matcap)}function M(m,p){let T=e.get(p).light;m.referencePosition.value.setFromMatrixPosition(T.matrixWorld),m.nearDistance.value=T.shadow.camera.near,m.farDistance.value=T.shadow.camera.far}return{refreshFogUniforms:n,refreshMaterialUniforms:s}}function H0(i,e,t,n){let s={},r={},a=[],o=i.getParameter(i.MAX_UNIFORM_BUFFER_BINDINGS);function l(v,w){let S=w.program;n.uniformBlockBinding(v,S)}function c(v,w){let S=s[v.id];S===void 0&&(m(v),S=h(v),s[v.id]=S,v.addEventListener("dispose",T));let I=w.program;n.updateUBOMapping(v,I);let x=e.render.frame;r[v.id]!==x&&(u(v),r[v.id]=x)}function h(v){let w=f();v.__bindingPointIndex=w;let S=i.createBuffer(),I=v.__size,x=v.usage;return i.bindBuffer(i.UNIFORM_BUFFER,S),i.bufferData(i.UNIFORM_BUFFER,I,x),i.bindBuffer(i.UNIFORM_BUFFER,null),i.bindBufferBase(i.UNIFORM_BUFFER,w,S),S}function f(){for(let v=0;v<o;v++)if(a.indexOf(v)===-1)return a.push(v),v;return et("WebGLRenderer: Maximum number of simultaneously usable uniforms groups reached."),0}function u(v){let w=s[v.id],S=v.uniforms,I=v.__cache;i.bindBuffer(i.UNIFORM_BUFFER,w);for(let x=0,A=S.length;x<A;x++){let N=S[x];if(Array.isArray(N))for(let k=0,V=N.length;k<V;k++)d(N[k],x,k,I);else d(N,x,0,I)}i.bindBuffer(i.UNIFORM_BUFFER,null)}function d(v,w,S,I){if(M(v,w,S,I)===!0){let x=v.__offset,A=v.value;if(Array.isArray(A)){let N=0;for(let k=0;k<A.length;k++){let V=A[k],$=p(V);g(V,v.__data,N),typeof V!="number"&&typeof V!="boolean"&&!V.isMatrix3&&!ArrayBuffer.isView(V)&&(N+=$.storage/Float32Array.BYTES_PER_ELEMENT)}}else g(A,v.__data,0);i.bufferSubData(i.UNIFORM_BUFFER,x,v.__data)}}function g(v,w,S){typeof v=="number"||typeof v=="boolean"?w[0]=v:v.isMatrix3?(w[0]=v.elements[0],w[1]=v.elements[1],w[2]=v.elements[2],w[3]=0,w[4]=v.elements[3],w[5]=v.elements[4],w[6]=v.elements[5],w[7]=0,w[8]=v.elements[6],w[9]=v.elements[7],w[10]=v.elements[8],w[11]=0):ArrayBuffer.isView(v)?w.set(new v.constructor(v.buffer,v.byteOffset,w.length)):v.toArray(w,S)}function M(v,w,S,I){let x=v.value,A=w+"_"+S;if(I[A]===void 0)return typeof x=="number"||typeof x=="boolean"?I[A]=x:ArrayBuffer.isView(x)?I[A]=x.slice():I[A]=x.clone(),!0;{let N=I[A];if(typeof x=="number"||typeof x=="boolean"){if(N!==x)return I[A]=x,!0}else{if(ArrayBuffer.isView(x))return!0;if(N.equals(x)===!1)return N.copy(x),!0}}return!1}function m(v){let w=v.uniforms,S=0,I=16;for(let A=0,N=w.length;A<N;A++){let k=Array.isArray(w[A])?w[A]:[w[A]];for(let V=0,$=k.length;V<$;V++){let U=k[V],W=Array.isArray(U.value)?U.value:[U.value];for(let ee=0,ie=W.length;ee<ie;ee++){let Z=W[ee],Q=p(Z),ue=S%I,se=ue%Q.boundary,Ge=ue+se;S+=se,Ge!==0&&I-Ge<Q.storage&&(S+=I-Ge),U.__data=new Float32Array(Q.storage/Float32Array.BYTES_PER_ELEMENT),U.__offset=S,S+=Q.storage}}}let x=S%I;return x>0&&(S+=I-x),v.__size=S,v.__cache={},this}function p(v){let w={boundary:0,storage:0};return typeof v=="number"||typeof v=="boolean"?(w.boundary=4,w.storage=4):v.isVector2?(w.boundary=8,w.storage=8):v.isVector3||v.isColor?(w.boundary=16,w.storage=12):v.isVector4?(w.boundary=16,w.storage=16):v.isMatrix3?(w.boundary=48,w.storage=48):v.isMatrix4?(w.boundary=64,w.storage=64):v.isTexture?Je("WebGLRenderer: Texture samplers can not be part of an uniforms group."):ArrayBuffer.isView(v)?(w.boundary=16,w.storage=v.byteLength):Je("WebGLRenderer: Unsupported uniform value type.",v),w}function T(v){let w=v.target;w.removeEventListener("dispose",T);let S=a.indexOf(w.__bindingPointIndex);a.splice(S,1),i.deleteBuffer(s[w.id]),delete s[w.id],delete r[w.id]}function C(){for(let v in s)i.deleteBuffer(s[v]);a=[],s={},r={}}return{bind:l,update:c,dispose:C}}var G0=new Uint16Array([12469,15057,12620,14925,13266,14620,13807,14376,14323,13990,14545,13625,14713,13328,14840,12882,14931,12528,14996,12233,15039,11829,15066,11525,15080,11295,15085,10976,15082,10705,15073,10495,13880,14564,13898,14542,13977,14430,14158,14124,14393,13732,14556,13410,14702,12996,14814,12596,14891,12291,14937,11834,14957,11489,14958,11194,14943,10803,14921,10506,14893,10278,14858,9960,14484,14039,14487,14025,14499,13941,14524,13740,14574,13468,14654,13106,14743,12678,14818,12344,14867,11893,14889,11509,14893,11180,14881,10751,14852,10428,14812,10128,14765,9754,14712,9466,14764,13480,14764,13475,14766,13440,14766,13347,14769,13070,14786,12713,14816,12387,14844,11957,14860,11549,14868,11215,14855,10751,14825,10403,14782,10044,14729,9651,14666,9352,14599,9029,14967,12835,14966,12831,14963,12804,14954,12723,14936,12564,14917,12347,14900,11958,14886,11569,14878,11247,14859,10765,14828,10401,14784,10011,14727,9600,14660,9289,14586,8893,14508,8533,15111,12234,15110,12234,15104,12216,15092,12156,15067,12010,15028,11776,14981,11500,14942,11205,14902,10752,14861,10393,14812,9991,14752,9570,14682,9252,14603,8808,14519,8445,14431,8145,15209,11449,15208,11451,15202,11451,15190,11438,15163,11384,15117,11274,15055,10979,14994,10648,14932,10343,14871,9936,14803,9532,14729,9218,14645,8742,14556,8381,14461,8020,14365,7603,15273,10603,15272,10607,15267,10619,15256,10631,15231,10614,15182,10535,15118,10389,15042,10167,14963,9787,14883,9447,14800,9115,14710,8665,14615,8318,14514,7911,14411,7507,14279,7198,15314,9675,15313,9683,15309,9712,15298,9759,15277,9797,15229,9773,15166,9668,15084,9487,14995,9274,14898,8910,14800,8539,14697,8234,14590,7790,14479,7409,14367,7067,14178,6621,15337,8619,15337,8631,15333,8677,15325,8769,15305,8871,15264,8940,15202,8909,15119,8775,15022,8565,14916,8328,14804,8009,14688,7614,14569,7287,14448,6888,14321,6483,14088,6171,15350,7402,15350,7419,15347,7480,15340,7613,15322,7804,15287,7973,15229,8057,15148,8012,15046,7846,14933,7611,14810,7357,14682,7069,14552,6656,14421,6316,14251,5948,14007,5528,15356,5942,15356,5977,15353,6119,15348,6294,15332,6551,15302,6824,15249,7044,15171,7122,15070,7050,14949,6861,14818,6611,14679,6349,14538,6067,14398,5651,14189,5311,13935,4958,15359,4123,15359,4153,15356,4296,15353,4646,15338,5160,15311,5508,15263,5829,15188,6042,15088,6094,14966,6001,14826,5796,14678,5543,14527,5287,14377,4985,14133,4586,13869,4257,15360,1563,15360,1642,15358,2076,15354,2636,15341,3350,15317,4019,15273,4429,15203,4732,15105,4911,14981,4932,14836,4818,14679,4621,14517,4386,14359,4156,14083,3795,13808,3437,15360,122,15360,137,15358,285,15355,636,15344,1274,15322,2177,15281,2765,15215,3223,15120,3451,14995,3569,14846,3567,14681,3466,14511,3305,14344,3121,14037,2800,13753,2467,15360,0,15360,1,15359,21,15355,89,15346,253,15325,479,15287,796,15225,1148,15133,1492,15008,1749,14856,1882,14685,1886,14506,1783,14324,1608,13996,1398,13702,1183]),Zn=null;function W0(){return Zn===null&&(Zn=new ur(G0,16,16,Ci,tn),Zn.name="DFG_LUT",Zn.minFilter=Qt,Zn.magFilter=Qt,Zn.wrapS=Hn,Zn.wrapT=Hn,Zn.generateMipmaps=!1,Zn.needsUpdate=!0),Zn}var il=class{constructor(e={}){let{canvas:t=ju(),context:n=null,depth:s=!0,stencil:r=!1,alpha:a=!1,antialias:o=!1,premultipliedAlpha:l=!0,preserveDrawingBuffer:c=!1,powerPreference:h="default",failIfMajorPerformanceCaveat:f=!1,reversedDepthBuffer:u=!1,outputBufferType:d=xn}=e;this.isWebGLRenderer=!0;let g;if(n!==null){if(typeof WebGLRenderingContext<"u"&&n instanceof WebGLRenderingContext)throw new Error("THREE.WebGLRenderer: WebGL 1 is not supported since r163.");g=n.getContextAttributes().alpha}else g=a;let M=d,m=new Set([yo,vo,xo]),p=new Set([xn,Bn,Ls,Ns,mo,go]),T=new Uint32Array(4),C=new Int32Array(4),v=new D,w=null,S=null,I=[],x=[],A=null;this.domElement=t,this.debug={checkShaderErrors:!0,diagnostics:{keywords:!1},onShaderError:null},this.autoClear=!0,this.autoClearColor=!0,this.autoClearDepth=!0,this.autoClearStencil=!0,this.sortObjects=!0,this.clippingPlanes=[],this.localClippingEnabled=!1,this.toneMapping=On,this.toneMappingExposure=1,this.transmissionResolutionScale=1;let N=this,k=!1,V=null,$=null,U=null,W=null;this._outputColorSpace=dn;let ee=0,ie=0,Z=null,Q=-1,ue=null,se=new Dt,Ge=new Dt,Pe=null,ot=new Ke(0),$e=0,Xe=t.width,K=t.height,re=1,Se=null,Le=null,Ie=new Dt(0,0,Xe,K),Ze=new Dt(0,0,Xe,K),ht=!1,st=new Ss,it=!1,Qe=!1,rt=new pt,gt=new D,Ct=new Dt,Ut={background:null,fog:null,environment:null,overrideMaterial:null,isScene:!0},_t=!1;function Et(){return Z===null?re:1}let B=n;function wt(y,F){return t.getContext(y,F)}let ct,P,_,G,j,oe,Me,Ee,L,z,ne,_e,ce,pe,ye,we,ke,O,Te,Y,be,Ae,de;try{let y={alpha:!0,depth:s,stencil:r,antialias:o,premultipliedAlpha:l,preserveDrawingBuffer:c,powerPreference:h,failIfMajorPerformanceCaveat:f};if("setAttribute"in t&&t.setAttribute("data-engine",`three.js r${"186"}`),t.addEventListener("webglcontextlost",St,!1),t.addEventListener("webglcontextrestored",mt,!1),t.addEventListener("webglcontextcreationerror",ln,!1),B===null){let F="webgl2";if(B=wt(F,y),B===null)throw wt(F)?new Error("THREE.WebGLRenderer: Error creating WebGL context with your selected attributes."):new Error("THREE.WebGLRenderer: Error creating WebGL context.")}Ve()}catch(y){throw t.removeEventListener("webglcontextlost",St,!1),t.removeEventListener("webglcontextrestored",mt,!1),t.removeEventListener("webglcontextcreationerror",ln,!1),et("WebGLRenderer: "+y.message),y}function Ve(){ct=new Jm(B),ct.init(),be=new k0(B,ct),P=new Vm(B,ct,e,be),_=new U0(B,ct),P.reversedDepthBuffer&&u&&_.buffers.depth.setReversed(!0),$=B.createFramebuffer(),U=B.createFramebuffer(),W=B.createFramebuffer(),G=new eg(B),j=new M0,oe=new F0(B,ct,_,j,P,be,G),Me=new jm(N),Ee=new tf(B),Ae=new Bm(B,Ee),L=new Km(B,Ee,G,Ae),z=new ng(B,L,Ee,Ae,G),O=new tg(B,P,oe),ye=new Hm(j),ne=new y0(N,Me,ct,P,Ae,ye),_e=new V0(N,j),ce=new S0,pe=new R0(ct),ke=new Om(N,Me,_,z,g,l),we=new D0(N,z,P),de=new H0(B,G,P,_),Te=new zm(B,ct,G),Y=new Qm(B,ct,G),G.programs=ne.programs,N.capabilities=P,N.extensions=ct,N.properties=j,N.renderLists=ce,N.shadowMap=we,N.state=_,N.info=G}M!==xn&&(A=new sg(M,t.width,t.height,o,s,r));let ze=new Ic(N,B);this.xr=ze,this.getContext=function(){return B},this.getContextAttributes=function(){return B.getContextAttributes()},this.forceContextLoss=function(){let y=ct.get("WEBGL_lose_context");y&&y.loseContext()},this.forceContextRestore=function(){let y=ct.get("WEBGL_lose_context");y&&y.restoreContext()},this.getPixelRatio=function(){return re},this.setPixelRatio=function(y){y!==void 0&&(re=y,this.setSize(Xe,K,!1))},this.getSize=function(y){return y.set(Xe,K)},this.setSize=function(y,F,J=!0){if(ze.isPresenting){Je("WebGLRenderer: Can't change size while VR device is presenting.");return}Xe=y,K=F,t.width=Math.floor(y*re),t.height=Math.floor(F*re),J===!0&&(t.style.width=y+"px",t.style.height=F+"px"),A!==null&&A.setSize(t.width,t.height),this.setViewport(0,0,y,F)},this.getDrawingBufferSize=function(y){return y.set(Xe*re,K*re).floor()},this.setDrawingBufferSize=function(y,F,J){Xe=y,K=F,re=J,t.width=Math.floor(y*J),t.height=Math.floor(F*J),this.setViewport(0,0,y,F)},this.setEffects=function(y){if(M===xn){et("WebGLRenderer: setEffects() requires outputBufferType set to HalfFloatType or FloatType.");return}if(y){for(let F=0;F<y.length;F++)if(y[F].isOutputPass===!0){Je("WebGLRenderer: OutputPass is not needed in setEffects(). Tone mapping and color space conversion are applied automatically.");break}}A.setEffects(y||[])},this.getCurrentViewport=function(y){return y.copy(se)},this.getViewport=function(y){return y.copy(Ie)},this.setViewport=function(y,F,J,X){y.isVector4?Ie.set(y.x,y.y,y.z,y.w):Ie.set(y,F,J,X),_.viewport(se.copy(Ie).multiplyScalar(re).round())},this.getScissor=function(y){return y.copy(Ze)},this.setScissor=function(y,F,J,X){y.isVector4?Ze.set(y.x,y.y,y.z,y.w):Ze.set(y,F,J,X),_.scissor(Ge.copy(Ze).multiplyScalar(re).round())},this.getScissorTest=function(){return ht},this.setScissorTest=function(y){_.setScissorTest(ht=y)},this.setOpaqueSort=function(y){Se=y},this.setTransparentSort=function(y){Le=y},this.getClearColor=function(y){return y.copy(ke.getClearColor())},this.setClearColor=function(){ke.setClearColor(...arguments)},this.getClearAlpha=function(){return ke.getClearAlpha()},this.setClearAlpha=function(){ke.setClearAlpha(...arguments)},this.clear=function(y=!0,F=!0,J=!0){let X=0;if(y){let q=!1;if(Z!==null){let Re=Z.texture.format;q=m.has(Re)}if(q){let Re=Z.texture.type,Ne=p.has(Re),Ce=ke.getClearColor(),Be=ke.getClearAlpha(),ge=Ce.r,Fe=Ce.g,at=Ce.b;Ne?(T[0]=ge,T[1]=Fe,T[2]=at,T[3]=Be,B.clearBufferuiv(B.COLOR,0,T)):(C[0]=ge,C[1]=Fe,C[2]=at,C[3]=Be,B.clearBufferiv(B.COLOR,0,C))}else X|=B.COLOR_BUFFER_BIT}F&&(X|=B.DEPTH_BUFFER_BIT,this.state.buffers.depth.setMask(!0)),J&&(X|=B.STENCIL_BUFFER_BIT,this.state.buffers.stencil.setMask(4294967295)),X!==0&&B.clear(X)},this.clearColor=function(){this.clear(!0,!1,!1)},this.clearDepth=function(){this.clear(!1,!0,!1)},this.clearStencil=function(){this.clear(!1,!1,!0)},this.setNodesHandler=function(y){y.setRenderer(this),V=y},this.dispose=function(){t.removeEventListener("webglcontextlost",St,!1),t.removeEventListener("webglcontextrestored",mt,!1),t.removeEventListener("webglcontextcreationerror",ln,!1),ke.dispose(),ce.dispose(),pe.dispose(),j.dispose(),Me.dispose(),z.dispose(),Ae.dispose(),de.dispose(),ne.dispose(),ze.dispose(),ze.removeEventListener("sessionstart",Jn),ze.removeEventListener("sessionend",b),R.stop()};function St(y){y.preventDefault(),uc("WebGLRenderer: Context Lost."),k=!0}function mt(){uc("WebGLRenderer: Context Restored."),k=!1;let y=G.autoReset,F=we.enabled,J=we.autoUpdate,X=we.needsUpdate,q=we.type;Ve(),G.autoReset=y,we.enabled=F,we.autoUpdate=J,we.needsUpdate=X,we.type=q}function ln(y){et("WebGLRenderer: A WebGL context could not be created. Reason: ",y.statusMessage)}function pn(y){let F=y.target;F.removeEventListener("dispose",pn),Li(F)}function Li(y){Ws(y),j.remove(y)}function Ws(y){let F=j.get(y).programs;F!==void 0&&(F.forEach(function(J){ne.releaseProgram(J)}),y.isShaderMaterial&&ne.releaseShaderCache(y))}this.renderBufferDirect=function(y,F,J,X,q,Re){F===null&&(F=Ut);let Ne=q.isMesh&&q.matrixWorld.determinantAffine()<0,Ce=xe(y,F,J,X,q);_.setMaterial(X,Ne);let Be=J.index,ge=1;if(X.wireframe===!0){if(Be=L.getWireframeAttribute(J),Be===void 0)return;ge=2}let Fe=J.drawRange,at=J.attributes.position,He=Fe.start*ge,xt=(Fe.start+Fe.count)*ge;Re!==null&&(He=Math.max(He,Re.start*ge),xt=Math.min(xt,(Re.start+Re.count)*ge)),Be!==null?(He=Math.max(He,0),xt=Math.min(xt,Be.count)):at!=null&&(He=Math.max(He,0),xt=Math.min(xt,at.count));let Ft=xt-He;if(Ft<0||Ft===1/0)return;Ae.setup(q,X,Ce,J,Be);let At,Tt=Te;if(Be!==null&&(At=Ee.get(Be),Tt=Y,Tt.setIndex(At)),q.isMesh)X.wireframe===!0?(_.setLineWidth(X.wireframeLinewidth*Et()),Tt.setMode(B.LINES)):Tt.setMode(B.TRIANGLES);else if(q.isLine){let Xt=X.linewidth;Xt===void 0&&(Xt=1),_.setLineWidth(Xt*Et()),q.isLineSegments?Tt.setMode(B.LINES):q.isLineLoop?Tt.setMode(B.LINE_LOOP):Tt.setMode(B.LINE_STRIP)}else q.isPoints?Tt.setMode(B.POINTS):q.isSprite&&Tt.setMode(B.TRIANGLES);if(q.isBatchedMesh)if(ct.get("WEBGL_multi_draw"))Tt.renderMultiDraw(q._multiDrawStarts,q._multiDrawCounts,q._multiDrawCount);else{let Xt=q._multiDrawStarts,Oe=q._multiDrawCounts,$t=q._multiDrawCount,le=Be?Ee.get(Be).bytesPerElement:1,tt=j.get(X).currentProgram.getUniforms();for(let un=0;un<$t;un++)tt.setValue(B,"_gl_DrawID",un),Tt.render(Xt[un]/le,Oe[un])}else if(q.isInstancedMesh)Tt.renderInstances(He,Ft,q.count);else if(J.isInstancedBufferGeometry){let Xt=J._maxInstanceCount!==void 0?J._maxInstanceCount:1/0,Oe=Math.min(J.instanceCount,Xt);Tt.renderInstances(He,Ft,Oe)}else Tt.render(He,Ft)};function Ki(y,F,J,X){V!==null&&y.isNodeMaterial&&V.setObject(X,y),it===!0&&ye.setState(y,J,!1),y.transparent===!0&&y.side===Yn&&y.forceSinglePass===!1?(y.side=en,y.needsUpdate=!0,fe(y,F,X),y.side=Ti,y.needsUpdate=!0,fe(y,F,X),y.side=Yn):fe(y,F,X)}this.compile=function(y,F,J=null){J===null&&(J=y),V!==null&&V.renderStart(y,F,J),S=pe.get(J),S.init(F),x.push(S),J.traverseVisible(function(q){q.isLight&&q.layers.test(F.layers)&&(S.pushLight(q),q.castShadow&&S.pushShadow(q))}),y!==J&&y.traverseVisible(function(q){q.isLight&&q.layers.test(F.layers)&&(S.pushLight(q),q.castShadow&&S.pushShadow(q))}),S.setupLights(),V!==null&&V.updateLights(S.state.lightsArray),Qe=this.localClippingEnabled,it=ye.init(this.clippingPlanes,Qe),it===!0&&ye.setGlobalState(this.clippingPlanes,F),V!==null&&we.render(S.state.shadowsArray,J,F);let X=new Set;return y.traverse(function(q){if(!(q.isMesh||q.isPoints||q.isLine||q.isSprite))return;let Re=q.material;if(Re)if(Array.isArray(Re))for(let Ne=0;Ne<Re.length;Ne++){let Ce=Re[Ne];Ki(Ce,J,F,q),X.add(Ce)}else Ki(Re,J,F,q),X.add(Re)}),S=x.pop(),V!==null&&V.renderEnd(),X},this.compileAsync=function(y,F,J=null){let X=this.compile(y,F,J);return new Promise(q=>{function Re(){if(X.forEach(function(Ne){let Be=j.get(Ne).currentProgram;(Be===void 0||Be.isReady())&&X.delete(Ne)}),X.size===0){q(y);return}setTimeout(Re,10)}ct.get("KHR_parallel_shader_compile")!==null?Re():setTimeout(Re,10)})};let Ni=null;function fl(y){Ni&&Ni(y)}function Jn(){R.stop()}function b(){R.start()}let R=new Th;R.setAnimationLoop(fl),typeof self<"u"&&R.setContext(self),this.setAnimationLoop=function(y){Ni=y,ze.setAnimationLoop(y),y===null?R.stop():R.start()},ze.addEventListener("sessionstart",Jn),ze.addEventListener("sessionend",b),this.render=function(y,F){if(F!==void 0&&F.isCamera!==!0){et("WebGLRenderer.render: camera is not an instance of THREE.Camera.");return}if(k===!0)return;V!==null&&V.renderStart(y,F);let J=ze.enabled===!0&&ze.isPresenting===!0,X=A!==null&&(Z===null||J)&&A.begin(N,Z);if(y.matrixWorldAutoUpdate===!0&&y.updateMatrixWorld(),F.parent===null&&F.matrixWorldAutoUpdate===!0&&F.updateMatrixWorld(),ze.enabled===!0&&ze.isPresenting===!0&&(A===null||A.isCompositing()===!1)&&(ze.cameraAutoUpdate===!0&&ze.updateCamera(F),F=ze.getCamera()),y.isScene===!0&&y.onBeforeRender(N,y,F,Z),S=pe.get(y,x.length),S.init(F),S.state.textureUnits=oe.getTextureUnits(),x.push(S),rt.multiplyMatrices(F.projectionMatrix,F.matrixWorldInverse),st.setFromProjectionMatrix(rt,Un,F.reversedDepth),Qe=this.localClippingEnabled,it=ye.init(this.clippingPlanes,Qe),w=ce.get(y,I.length),w.init(),I.push(w),ze.enabled===!0&&ze.isPresenting===!0){let Ne=N.xr.getDepthSensingMesh();Ne!==null&&E(Ne,F,-1/0,N.sortObjects)}E(y,F,0,N.sortObjects),w.finish(),V!==null&&V.updateLights(S.state.lightsArray),N.sortObjects===!0&&w.sort(Se,Le),_t=ze.enabled===!1||ze.isPresenting===!1||ze.hasDepthSensing()===!1,_t&&ke.addToRenderList(w,y),this.info.render.frame++,this.info.autoReset===!0&&this.info.reset(),it===!0&&ye.beginShadows();let q=S.state.shadowsArray;if(we.render(q,y,F),it===!0&&ye.endShadows(),(X&&A.hasRenderPass())===!1){let Ne=w.opaque,Ce=w.transmissive;if(S.setupLights(),F.isArrayCamera){let Be=F.cameras;if(Ce.length>0)for(let ge=0,Fe=Be.length;ge<Fe;ge++){let at=Be[ge];he(Ne,Ce,y,at)}_t&&ke.render(y);for(let ge=0,Fe=Be.length;ge<Fe;ge++){let at=Be[ge];H(w,y,at,at.viewport)}}else Ce.length>0&&he(Ne,Ce,y,F),_t&&ke.render(y),H(w,y,F)}Z!==null&&ie===0&&(oe.updateMultisampleRenderTarget(Z),oe.updateRenderTargetMipmap(Z)),X&&A.end(N),y.isScene===!0&&y.onAfterRender(N,y,F),Ae.resetDefaultState(),Q=-1,ue=null,x.pop(),x.length>0?(S=x[x.length-1],oe.setTextureUnits(S.state.textureUnits),it===!0&&ye.setGlobalState(N.clippingPlanes,S.state.camera)):S=null,I.pop(),I.length>0?w=I[I.length-1]:w=null,V!==null&&V.renderEnd()};function E(y,F,J,X){if(y.visible===!1)return;if(y.layers.test(F.layers)){if(y.isGroup)J=y.renderOrder;else if(y.isLOD)y.autoUpdate===!0&&y.update(F);else if(y.isLightProbeGrid)S.pushLightProbeGrid(y);else if(y.isLight)S.pushLight(y),y.castShadow&&S.pushShadow(y);else if(y.isSprite){if(!y.frustumCulled||y.intersectsFrustum(st)){X&&Ct.setFromMatrixPosition(y.matrixWorld).applyMatrix4(rt);let Ne=z.update(y),Ce=y.material;Ce.visible&&w.push(y,Ne,Ce,J,Ct.z,null,F)}}else if((y.isMesh||y.isLine||y.isPoints)&&(!y.frustumCulled||y.intersectsFrustum(st))){let Ne=z.update(y),Ce=y.material;if(X&&(y.boundingSphere!==void 0?(y.boundingSphere===null&&y.computeBoundingSphere(),Ct.copy(y.boundingSphere.center)):(Ne.boundingSphere===null&&Ne.computeBoundingSphere(),Ct.copy(Ne.boundingSphere.center)),Ct.applyMatrix4(y.matrixWorld).applyMatrix4(rt)),Array.isArray(Ce)){let Be=Ne.groups;for(let ge=0,Fe=Be.length;ge<Fe;ge++){let at=Be[ge],He=Ce[at.materialIndex];He&&He.visible&&w.push(y,Ne,He,J,Ct.z,at,F)}}else Ce.visible&&w.push(y,Ne,Ce,J,Ct.z,null,F)}}let Re=y.children;for(let Ne=0,Ce=Re.length;Ne<Ce;Ne++)E(Re[Ne],F,J,X)}function H(y,F,J,X){let{opaque:q,transmissive:Re,transparent:Ne}=y;S.setupLightsView(J),it===!0&&ye.setGlobalState(N.clippingPlanes,J),X&&_.viewport(se.copy(X)),q.length>0&&te(q,F,J),Re.length>0&&te(Re,F,J),Ne.length>0&&te(Ne,F,J),_.buffers.depth.setTest(!0),_.buffers.depth.setMask(!0),_.buffers.color.setMask(!0),_.setPolygonOffset(!1)}function he(y,F,J,X){if((J.isScene===!0?J.overrideMaterial:null)!==null)return;if(S.state.transmissionRenderTarget[X.id]===void 0){let He=ct.has("EXT_color_buffer_half_float")||ct.has("EXT_color_buffer_float");S.state.transmissionRenderTarget[X.id]=new Vt(1,1,{generateMipmaps:!0,type:He?tn:xn,minFilter:wi,samples:Math.max(4,P.samples),stencilBuffer:r,resolveDepthBuffer:!1,resolveStencilBuffer:!1,storeMultisampledDepthBuffer:!1,storeMultisampledStencilBuffer:!1,colorSpace:dt.workingColorSpace})}let Re=S.state.transmissionRenderTarget[X.id],Ne=X.viewport||se;Re.setSize(Ne.z*N.transmissionResolutionScale,Ne.w*N.transmissionResolutionScale);let Ce=N.getRenderTarget(),Be=N.getActiveCubeFace(),ge=N.getActiveMipmapLevel();N.setRenderTarget(Re),N.getClearColor(ot),$e=N.getClearAlpha(),$e<1&&N.setClearColor(16777215,.5),N.clear(),_t&&ke.render(J);let Fe=N.toneMapping;N.toneMapping=On;let at=X.viewport;if(X.viewport!==void 0&&(X.viewport=void 0),S.setupLightsView(X),it===!0&&ye.setGlobalState(N.clippingPlanes,X),te(y,J,X),oe.updateMultisampleRenderTarget(Re),oe.updateRenderTargetMipmap(Re),ct.has("WEBGL_multisampled_render_to_texture")===!1){let He=!1;for(let xt=0,Ft=F.length;xt<Ft;xt++){let At=F[xt],{object:Tt,geometry:Xt,material:Oe,group:$t}=At;if(Oe.side===Yn&&Tt.layers.test(X.layers)){let le=Oe.side;Oe.side=en,Oe.needsUpdate=!0,me(Tt,J,X,Xt,Oe,$t),Oe.side=le,Oe.needsUpdate=!0,He=!0}}He===!0&&(oe.updateMultisampleRenderTarget(Re),oe.updateRenderTargetMipmap(Re))}N.setRenderTarget(Ce,Be,ge),N.setClearColor(ot,$e),at!==void 0&&(X.viewport=at),N.toneMapping=Fe}function te(y,F,J){let X=F.isScene===!0?F.overrideMaterial:null;for(let q=0,Re=y.length;q<Re;q++){let Ne=y[q],{object:Ce,geometry:Be,group:ge}=Ne,Fe=Ne.material;Fe.allowOverride===!0&&X!==null&&(Fe=X),Ce.layers.test(J.layers)&&me(Ce,F,J,Be,Fe,ge)}}function me(y,F,J,X,q,Re){V!==null&&q.isNodeMaterial&&V.setObject(y,q),y.onBeforeRender(N,F,J,X,q,Re),y.modelViewMatrix.multiplyMatrices(J.matrixWorldInverse,y.matrixWorld),y.normalMatrix.getNormalMatrix(y.modelViewMatrix),q.onBeforeRender(N,F,J,X,y,Re),q.transparent===!0&&q.side===Yn&&q.forceSinglePass===!1?(q.side=en,q.needsUpdate=!0,N.renderBufferDirect(J,F,X,q,y,Re),q.side=Ti,q.needsUpdate=!0,N.renderBufferDirect(J,F,X,q,y,Re),q.side=Yn):N.renderBufferDirect(J,F,X,q,y,Re),y.onAfterRender(N,F,J,X,q,Re)}function fe(y,F,J){F.isScene!==!0&&(F=Ut);let X=j.get(y),q=S.state.lights,Re=S.state.shadowsArray,Ne=q.state.version,Ce=ne.getParameters(y,q.state,Re,F,J,S.state.lightProbeGridArray),Be=ne.getProgramCacheKey(Ce),ge=X.programs;X.environment=y.isMeshStandardMaterial||y.isMeshLambertMaterial||y.isMeshPhongMaterial?F.environment:null,X.fog=F.fog;let Fe=y.isMeshStandardMaterial||y.isMeshLambertMaterial&&!y.envMap||y.isMeshPhongMaterial&&!y.envMap;X.envMap=Me.get(y.envMap||X.environment,Fe),X.envMapRotation=X.environment!==null&&y.envMap===null?F.environmentRotation:y.envMapRotation,ge===void 0&&(y.addEventListener("dispose",pn),ge=new Map,X.programs=ge);let at=ge.get(Be);if(at!==void 0){if(X.currentProgram===at&&X.lightsStateVersion===Ne)return Ye(y,Ce),at}else Ce.uniforms=ne.getUniforms(y),V!==null&&y.isNodeMaterial&&V.build(y,J,Ce),y.onBeforeCompile(Ce,N),at=ne.acquireProgram(Ce,Be),ge.set(Be,at),X.uniforms=Ce.uniforms;let He=X.uniforms;return(!y.isShaderMaterial&&!y.isRawShaderMaterial||y.clipping===!0)&&(He.clippingPlanes=ye.uniform),Ye(y,Ce),X.needsLights=We(y),X.lightsStateVersion=Ne,X.needsLights&&(He.ambientLightColor.value=q.state.ambient,He.lightProbe.value=q.state.probe,He.sunLights.value=q.state.sun,He.sunLightShadows.value=q.state.sunShadow,He.directionalLights.value=q.state.directional,He.directionalLightShadows.value=q.state.directionalShadow,He.spotLights.value=q.state.spot,He.spotLightShadows.value=q.state.spotShadow,He.rectAreaLights.value=q.state.rectArea,He.ltc_1.value=q.state.rectAreaLTC1,He.ltc_2.value=q.state.rectAreaLTC2,He.pointLights.value=q.state.point,He.pointLightShadows.value=q.state.pointShadow,He.hemisphereLights.value=q.state.hemi,He.sunShadowMatrix.value=q.state.sunShadowMatrix,He.sunShadowCascade.value=q.state.sunShadowCascade,He.directionalShadowMatrix.value=q.state.directionalShadowMatrix,He.spotLightMatrix.value=q.state.spotLightMatrix,He.spotLightMap.value=q.state.spotLightMap,He.pointShadowMatrix.value=q.state.pointShadowMatrix),X.lightProbeGrid=S.state.lightProbeGridArray.length>0,X.currentProgram=at,X.uniformsList=null,at}function ae(y){if(y.uniformsList===null){let F=y.currentProgram.getUniforms();y.uniformsList=ks.seqWithValue(F.seq,y.uniforms)}return y.uniformsList}function Ye(y,F){let J=j.get(y);J.outputColorSpace=F.outputColorSpace,J.batching=F.batching,J.batchingColor=F.batchingColor,J.instancing=F.instancing,J.instancingColor=F.instancingColor,J.instancingMorph=F.instancingMorph,J.skinning=F.skinning,J.morphTargets=F.morphTargets,J.morphNormals=F.morphNormals,J.morphColors=F.morphColors,J.morphTargetsCount=F.morphTargetsCount,J.numClippingPlanes=F.numClippingPlanes,J.numIntersection=F.numClipIntersection,J.vertexAlphas=F.vertexAlphas,J.vertexTangents=F.vertexTangents,J.toneMapping=F.toneMapping}function je(y,F){if(y.length===0)return null;if(y.length===1)return y[0].texture!==null?y[0]:null;v.setFromMatrixPosition(F.matrixWorld);for(let J=0,X=y.length;J<X;J++){let q=y[J];if(q.texture!==null&&q.boundingBox.containsPoint(v))return q}return null}function xe(y,F,J,X,q){F.isScene!==!0&&(F=Ut),oe.resetTextureUnits();let Re=F.fog,Ne=X.isMeshStandardMaterial||X.isMeshLambertMaterial||X.isMeshPhongMaterial?F.environment:null,Ce=Z===null?N.outputColorSpace:Z.isXRRenderTarget===!0?Z.texture.colorSpace:dt.workingColorSpace,Be=X.isMeshStandardMaterial||X.isMeshLambertMaterial&&!X.envMap||X.isMeshPhongMaterial&&!X.envMap,ge=Me.get(X.envMap||Ne,Be),Fe=X.vertexColors===!0&&!!J.attributes.color&&J.attributes.color.itemSize===4,at=!!J.attributes.tangent&&(!!X.normalMap||X.anisotropy>0),He=!!J.morphAttributes.position,xt=!!J.morphAttributes.normal,Ft=!!J.morphAttributes.color,At=On;X.toneMapped&&(Z===null||Z.isXRRenderTarget===!0)&&(At=N.toneMapping);let Tt=J.morphAttributes.position||J.morphAttributes.normal||J.morphAttributes.color,Xt=Tt!==void 0?Tt.length:0,Oe=j.get(X),$t=S.state.lights;if(it===!0&&(Qe===!0||y!==ue)){let It=y===ue&&X.id===Q;ye.setState(X,y,It)}let le=!1;X.version===Oe.__version?(Oe.needsLights&&Oe.lightsStateVersion!==$t.state.version||Oe.outputColorSpace!==Ce||q.isBatchedMesh&&Oe.batching===!1||!q.isBatchedMesh&&Oe.batching===!0||q.isBatchedMesh&&Oe.batchingColor===!0&&q._colorsTexture===null||q.isBatchedMesh&&Oe.batchingColor===!1&&q._colorsTexture!==null||q.isInstancedMesh&&Oe.instancing===!1||!q.isInstancedMesh&&Oe.instancing===!0||q.isSkinnedMesh&&Oe.skinning===!1||!q.isSkinnedMesh&&Oe.skinning===!0||q.isInstancedMesh&&Oe.instancingColor===!0&&q.instanceColor===null||q.isInstancedMesh&&Oe.instancingColor===!1&&q.instanceColor!==null||q.isInstancedMesh&&Oe.instancingMorph===!0&&q.morphTexture===null||q.isInstancedMesh&&Oe.instancingMorph===!1&&q.morphTexture!==null||Oe.envMap!==ge||X.fog===!0&&Oe.fog!==Re||Oe.numClippingPlanes!==void 0&&(Oe.numClippingPlanes!==ye.numPlanes||Oe.numIntersection!==ye.numIntersection)||Oe.vertexAlphas!==Fe||Oe.vertexTangents!==at||Oe.morphTargets!==He||Oe.morphNormals!==xt||Oe.morphColors!==Ft||Oe.toneMapping!==At||Oe.morphTargetsCount!==Xt||!!Oe.lightProbeGrid!=S.state.lightProbeGridArray.length>0)&&(le=!0):(le=!0,Oe.__version=X.version);let tt=Oe.currentProgram;le===!0&&(tt=fe(X,F,q),V&&X.isNodeMaterial&&V.onUpdateProgram(X,tt,Oe));let un=!1,zn=!1,Kn=!1,Mt=tt.getUniforms(),Lt=Oe.uniforms;if(_.useProgram(tt.program)&&(un=!0,zn=!0,Kn=!0),X.id!==Q&&(Q=X.id,zn=!0),Oe.needsLights){let It=je(S.state.lightProbeGridArray,q);Oe.lightProbeGrid!==It&&(Oe.lightProbeGrid=It,zn=!0)}if(un||ue!==y){_.buffers.depth.getReversed()&&y.reversedDepth!==!0&&(y._reversedDepth=!0,y.updateProjectionMatrix()),Mt.setValue(B,"projectionMatrix",y.projectionMatrix),Mt.setValue(B,"viewMatrix",y.matrixWorldInverse);let di=Mt.map.cameraPosition;di!==void 0&&di.setValue(B,gt.setFromMatrixPosition(y.matrixWorld)),P.logarithmicDepthBuffer&&Mt.setValue(B,"logDepthBufFC",2/(Math.log(y.far+1)/Math.LN2)),(X.isMeshPhongMaterial||X.isMeshToonMaterial||X.isMeshLambertMaterial||X.isMeshBasicMaterial||X.isMeshStandardMaterial||X.isShaderMaterial)&&Mt.setValue(B,"isOrthographic",y.isOrthographicCamera===!0),ue!==y&&(ue=y,zn=!0,Kn=!0)}if(Oe.needsLights&&($t.state.sunShadowMap.length>0&&Mt.setValue(B,"sunShadowMap",$t.state.sunShadowMap,oe),$t.state.directionalShadowMap.length>0&&Mt.setValue(B,"directionalShadowMap",$t.state.directionalShadowMap,oe),$t.state.spotShadowMap.length>0&&Mt.setValue(B,"spotShadowMap",$t.state.spotShadowMap,oe),$t.state.pointShadowMap.length>0&&Mt.setValue(B,"pointShadowMap",$t.state.pointShadowMap,oe)),q.isSkinnedMesh){Mt.setOptional(B,q,"bindMatrix"),Mt.setOptional(B,q,"bindMatrixInverse");let It=q.skeleton;It&&(It.boneTexture===null&&It.computeBoneTexture(),Mt.setValue(B,"boneTexture",It.boneTexture,oe))}q.isBatchedMesh&&(Mt.setOptional(B,q,"batchingTexture"),Mt.setValue(B,"batchingTexture",q._matricesTexture,oe),Mt.setOptional(B,q,"batchingIdTexture"),Mt.setValue(B,"batchingIdTexture",q._indirectTexture,oe),Mt.setOptional(B,q,"batchingColorTexture"),q._colorsTexture!==null&&Mt.setValue(B,"batchingColorTexture",q._colorsTexture,oe));let hi=J.morphAttributes;if((hi.position!==void 0||hi.normal!==void 0||hi.color!==void 0)&&O.update(q,J,tt),(zn||Oe.receiveShadow!==q.receiveShadow)&&(Oe.receiveShadow=q.receiveShadow,Mt.setValue(B,"receiveShadow",q.receiveShadow)),(X.isMeshStandardMaterial||X.isMeshLambertMaterial||X.isMeshPhongMaterial)&&X.envMap===null&&F.environment!==null&&(Lt.envMapIntensity.value=F.environmentIntensity),Lt.dfgLUT!==void 0&&(Lt.dfgLUT.value=W0()),zn){if(Mt.setValue(B,"toneMappingExposure",N.toneMappingExposure),Oe.needsLights&&qe(Lt,Kn),Re&&X.fog===!0&&_e.refreshFogUniforms(Lt,Re),_e.refreshMaterialUniforms(Lt,X,re,K,S.state.transmissionRenderTarget[y.id]),Oe.needsLights&&Oe.lightProbeGrid){let It=Oe.lightProbeGrid;Lt.probesSH.value=It.texture,Lt.probesMin.value.copy(It.boundingBox.min),Lt.probesMax.value.copy(It.boundingBox.max),Lt.probesResolution.value.copy(It.resolution)}ks.upload(B,ae(Oe),Lt,oe)}if(X.isShaderMaterial&&X.uniformsNeedUpdate===!0&&(ks.upload(B,ae(Oe),Lt,oe),X.uniformsNeedUpdate=!1),X.isSpriteMaterial&&Mt.setValue(B,"center",q.center),Mt.setValue(B,"modelViewMatrix",q.modelViewMatrix),Mt.setValue(B,"normalMatrix",q.normalMatrix),Mt.setValue(B,"modelMatrix",q.matrixWorld),X.uniformsGroups!==void 0){let It=X.uniformsGroups;for(let di=0,Qi=It.length;di<Qi;di++){let Fc=It[di];de.update(Fc,tt),de.bind(Fc,tt)}}return tt}function qe(y,F){y.ambientLightColor.needsUpdate=F,y.lightProbe.needsUpdate=F,y.sunLights.needsUpdate=F,y.sunLightShadows.needsUpdate=F,y.directionalLights.needsUpdate=F,y.directionalLightShadows.needsUpdate=F,y.pointLights.needsUpdate=F,y.pointLightShadows.needsUpdate=F,y.spotLights.needsUpdate=F,y.spotLightShadows.needsUpdate=F,y.rectAreaLights.needsUpdate=F,y.hemisphereLights.needsUpdate=F}function We(y){return y.isMeshLambertMaterial||y.isMeshToonMaterial||y.isMeshPhongMaterial||y.isMeshStandardMaterial||y.isShadowMaterial||y.isShaderMaterial&&y.lights===!0}this.getActiveCubeFace=function(){return ee},this.getActiveMipmapLevel=function(){return ie},this.getRenderTarget=function(){return Z},this.setRenderTargetTextures=function(y,F,J){let X=j.get(y);X.__autoAllocateDepthBuffer=y.resolveDepthBuffer===!1,X.__autoAllocateDepthBuffer===!1&&(X.__useRenderToTexture=!1),j.get(y.texture).__webglTexture=F,j.get(y.depthTexture).__webglTexture=X.__autoAllocateDepthBuffer?void 0:J,X.__hasExternalTextures=!0},this.setRenderTargetFramebuffer=function(y,F){let J=j.get(y);J.__webglFramebuffer=F,J.__useDefaultFramebuffer=F===void 0},this.setRenderTarget=function(y,F=0,J=0){Z=y,ee=F,ie=J;let X=null,q=!1,Re=!1;if(y){let Ce=j.get(y);if(Ce.__useDefaultFramebuffer!==void 0){_.bindFramebuffer(B.FRAMEBUFFER,Ce.__webglFramebuffer),se.copy(y.viewport),Ge.copy(y.scissor),Pe=y.scissorTest,_.viewport(se),_.scissor(Ge),_.setScissorTest(Pe),Q=-1;return}else if(Ce.__webglFramebuffer===void 0)oe.setupRenderTarget(y);else if(Ce.__hasExternalTextures)oe.rebindTextures(y,j.get(y.texture).__webglTexture,j.get(y.depthTexture).__webglTexture);else if(y.depthBuffer){let Fe=y.depthTexture;if(Ce.__boundDepthTexture!==Fe){if(Fe!==null&&j.has(Fe)&&(y.width!==Fe.image.width||y.height!==Fe.image.height))throw new Error("THREE.WebGLRenderer: Attached DepthTexture is initialized to the incorrect size.");oe.setupDepthRenderbuffer(y)}}let Be=y.texture;(Be.isData3DTexture||Be.isDataArrayTexture||Be.isCompressedArrayTexture)&&(Re=!0);let ge=j.get(y).__webglFramebuffer;y.isWebGLCubeRenderTarget?(Array.isArray(ge[F])?X=ge[F][J]:X=ge[F],q=!0):y.samples>0&&oe.useMultisampledRTT(y)===!1?X=j.get(y).__webglMultisampledFramebuffer:Array.isArray(ge)?X=ge[J]:X=ge,se.copy(y.viewport),Ge.copy(y.scissor),Pe=y.scissorTest}else se.copy(Ie).multiplyScalar(re).floor(),Ge.copy(Ze).multiplyScalar(re).floor(),Pe=ht;if(J!==0&&(X=$),_.bindFramebuffer(B.FRAMEBUFFER,X)&&_.drawBuffers(y,X),_.viewport(se),_.scissor(Ge),_.setScissorTest(Pe),q){let Ce=j.get(y.texture);B.framebufferTexture2D(B.FRAMEBUFFER,B.COLOR_ATTACHMENT0,B.TEXTURE_CUBE_MAP_POSITIVE_X+F,Ce.__webglTexture,J)}else if(Re){let Ce=F;for(let Be=0;Be<y.textures.length;Be++){let ge=j.get(y.textures[Be]);B.framebufferTextureLayer(B.FRAMEBUFFER,B.COLOR_ATTACHMENT0+Be,ge.__webglTexture,J,Ce)}}else if(y!==null&&J!==0){let Ce=j.get(y.texture);B.framebufferTexture2D(B.FRAMEBUFFER,B.COLOR_ATTACHMENT0,B.TEXTURE_2D,Ce.__webglTexture,J)}Q=-1};function cn(y){let F=j.get(y);return(F.__readFormat!==y.format||F.__readType!==y.type)&&(F.__readFormat=y.format,F.__readType=y.type,F.__formatReadable=P.textureFormatReadable(y.format),F.__typeReadable=P.textureTypeReadable(y.type)),F}this.readRenderTargetPixels=function(y,F,J,X,q,Re,Ne,Ce=0){if(!(y&&y.isWebGLRenderTarget)){et("WebGLRenderer.readRenderTargetPixels: renderTarget is not THREE.WebGLRenderTarget.");return}let Be=j.get(y).__webglFramebuffer;if(y.isWebGLCubeRenderTarget&&Ne!==void 0&&(Be=Be[Ne]),Be){_.bindFramebuffer(B.FRAMEBUFFER,Be);try{let ge=y.textures[Ce],Fe=ge.format,at=ge.type;y.textures.length>1&&B.readBuffer(B.COLOR_ATTACHMENT0+Ce);let He=cn(ge);if(He.__formatReadable===!1){et("WebGLRenderer.readRenderTargetPixels: renderTarget is not in RGBA or implementation defined format.");return}if(He.__typeReadable===!1){et("WebGLRenderer.readRenderTargetPixels: renderTarget is not in UnsignedByteType or implementation defined type.");return}F>=0&&F<=y.width-X&&J>=0&&J<=y.height-q&&B.readPixels(F,J,X,q,be.convert(Fe),be.convert(at),Re)}finally{let ge=Z!==null?j.get(Z).__webglFramebuffer:null;_.bindFramebuffer(B.FRAMEBUFFER,ge)}}},this.readRenderTargetPixelsAsync=async function(y,F,J,X,q,Re,Ne,Ce=0){if(!(y&&y.isWebGLRenderTarget))throw new Error("THREE.WebGLRenderer.readRenderTargetPixels: renderTarget is not THREE.WebGLRenderTarget.");let Be=j.get(y).__webglFramebuffer;if(y.isWebGLCubeRenderTarget&&Ne!==void 0&&(Be=Be[Ne]),Be)if(F>=0&&F<=y.width-X&&J>=0&&J<=y.height-q){_.bindFramebuffer(B.FRAMEBUFFER,Be);let ge=y.textures[Ce],Fe=ge.format,at=ge.type;y.textures.length>1&&B.readBuffer(B.COLOR_ATTACHMENT0+Ce);let He=cn(ge);if(He.__formatReadable===!1)throw new Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: renderTarget is not in RGBA or implementation defined format.");if(He.__typeReadable===!1)throw new Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: renderTarget is not in UnsignedByteType or implementation defined type.");let xt=B.createBuffer();B.bindBuffer(B.PIXEL_PACK_BUFFER,xt),B.bufferData(B.PIXEL_PACK_BUFFER,Re.byteLength,B.STREAM_READ),B.readPixels(F,J,X,q,be.convert(Fe),be.convert(at),0),B.bindBuffer(B.PIXEL_PACK_BUFFER,null);let Ft=Z!==null?j.get(Z).__webglFramebuffer:null;_.bindFramebuffer(B.FRAMEBUFFER,Ft);let At=B.fenceSync(B.SYNC_GPU_COMMANDS_COMPLETE,0);return B.flush(),await Ku(B,At,4),B.bindBuffer(B.PIXEL_PACK_BUFFER,xt),B.getBufferSubData(B.PIXEL_PACK_BUFFER,0,Re),B.bindBuffer(B.PIXEL_PACK_BUFFER,null),B.deleteBuffer(xt),B.deleteSync(At),Re}else throw new Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: requested read bounds are out of range.")},this.copyFramebufferToTexture=function(y,F=null,J=0){let X=Math.pow(2,-J),q=Math.floor(y.image.width*X),Re=Math.floor(y.image.height*X),Ne=F!==null?F.x:0,Ce=F!==null?F.y:0;oe.setTexture2D(y,0),B.copyTexSubImage2D(B.TEXTURE_2D,J,0,0,Ne,Ce,q,Re),_.unbindTexture()},this.copyTextureToTexture=function(y,F,J=null,X=null,q=0,Re=0){let Ne,Ce,Be,ge,Fe,at,He,xt,Ft,At=y.isCompressedTexture?y.mipmaps[Re]:y.image;if(J!==null)Ne=J.max.x-J.min.x,Ce=J.max.y-J.min.y,Be=J.isBox3?J.max.z-J.min.z:1,ge=J.min.x,Fe=J.min.y,at=J.isBox3?J.min.z:0;else{let Lt=Math.pow(2,-q);Ne=Math.floor(At.width*Lt),Ce=Math.floor(At.height*Lt),y.isDataArrayTexture?Be=At.depth:y.isData3DTexture?Be=Math.floor(At.depth*Lt):Be=1,ge=0,Fe=0,at=0}X!==null?(He=X.x,xt=X.y,Ft=X.z):(He=0,xt=0,Ft=0);let Tt=be.convert(F.format),Xt=be.convert(F.type),Oe;F.isData3DTexture?(oe.setTexture3D(F,0),Oe=B.TEXTURE_3D):F.isDataArrayTexture||F.isCompressedArrayTexture?(oe.setTexture2DArray(F,0),Oe=B.TEXTURE_2D_ARRAY):(oe.setTexture2D(F,0),Oe=B.TEXTURE_2D),_.activeTexture(B.TEXTURE0),_.pixelStorei(B.UNPACK_FLIP_Y_WEBGL,F.flipY),_.pixelStorei(B.UNPACK_PREMULTIPLY_ALPHA_WEBGL,F.premultiplyAlpha),_.pixelStorei(B.UNPACK_ALIGNMENT,F.unpackAlignment);let $t=_.getParameter(B.UNPACK_ROW_LENGTH),le=_.getParameter(B.UNPACK_IMAGE_HEIGHT),tt=_.getParameter(B.UNPACK_SKIP_PIXELS),un=_.getParameter(B.UNPACK_SKIP_ROWS),zn=_.getParameter(B.UNPACK_SKIP_IMAGES);_.pixelStorei(B.UNPACK_ROW_LENGTH,At.width),_.pixelStorei(B.UNPACK_IMAGE_HEIGHT,At.height),_.pixelStorei(B.UNPACK_SKIP_PIXELS,ge),_.pixelStorei(B.UNPACK_SKIP_ROWS,Fe),_.pixelStorei(B.UNPACK_SKIP_IMAGES,at);let Kn=y.isDataArrayTexture||y.isData3DTexture,Mt=F.isDataArrayTexture||F.isData3DTexture;if(y.isDepthTexture){let Lt=j.get(y),hi=j.get(F),It=j.get(Lt.__renderTarget),di=j.get(hi.__renderTarget);_.bindFramebuffer(B.READ_FRAMEBUFFER,It.__webglFramebuffer),_.bindFramebuffer(B.DRAW_FRAMEBUFFER,di.__webglFramebuffer);for(let Qi=0;Qi<Be;Qi++)Kn&&(B.framebufferTextureLayer(B.READ_FRAMEBUFFER,B.COLOR_ATTACHMENT0,j.get(y).__webglTexture,q,at+Qi),B.framebufferTextureLayer(B.DRAW_FRAMEBUFFER,B.COLOR_ATTACHMENT0,j.get(F).__webglTexture,Re,Ft+Qi)),B.blitFramebuffer(ge,Fe,Ne,Ce,He,xt,Ne,Ce,B.DEPTH_BUFFER_BIT,B.NEAREST);_.bindFramebuffer(B.READ_FRAMEBUFFER,null),_.bindFramebuffer(B.DRAW_FRAMEBUFFER,null)}else if(q!==0||y.isRenderTargetTexture||j.has(y)){let Lt=j.get(y),hi=j.get(F);_.bindFramebuffer(B.READ_FRAMEBUFFER,U),_.bindFramebuffer(B.DRAW_FRAMEBUFFER,W);for(let It=0;It<Be;It++)Kn?B.framebufferTextureLayer(B.READ_FRAMEBUFFER,B.COLOR_ATTACHMENT0,Lt.__webglTexture,q,at+It):B.framebufferTexture2D(B.READ_FRAMEBUFFER,B.COLOR_ATTACHMENT0,B.TEXTURE_2D,Lt.__webglTexture,q),Mt?B.framebufferTextureLayer(B.DRAW_FRAMEBUFFER,B.COLOR_ATTACHMENT0,hi.__webglTexture,Re,Ft+It):B.framebufferTexture2D(B.DRAW_FRAMEBUFFER,B.COLOR_ATTACHMENT0,B.TEXTURE_2D,hi.__webglTexture,Re),q!==0?B.blitFramebuffer(ge,Fe,Ne,Ce,He,xt,Ne,Ce,B.COLOR_BUFFER_BIT,B.NEAREST):Mt?B.copyTexSubImage3D(Oe,Re,He,xt,Ft+It,ge,Fe,Ne,Ce):B.copyTexSubImage2D(Oe,Re,He,xt,ge,Fe,Ne,Ce);_.bindFramebuffer(B.READ_FRAMEBUFFER,null),_.bindFramebuffer(B.DRAW_FRAMEBUFFER,null)}else Mt?y.isDataTexture||y.isData3DTexture?B.texSubImage3D(Oe,Re,He,xt,Ft,Ne,Ce,Be,Tt,Xt,At.data):F.isCompressedArrayTexture?B.compressedTexSubImage3D(Oe,Re,He,xt,Ft,Ne,Ce,Be,Tt,At.data):B.texSubImage3D(Oe,Re,He,xt,Ft,Ne,Ce,Be,Tt,Xt,At):y.isDataTexture?B.texSubImage2D(B.TEXTURE_2D,Re,He,xt,Ne,Ce,Tt,Xt,At.data):y.isCompressedTexture?B.compressedTexSubImage2D(B.TEXTURE_2D,Re,He,xt,At.width,At.height,Tt,At.data):B.texSubImage2D(B.TEXTURE_2D,Re,He,xt,Ne,Ce,Tt,Xt,At);_.pixelStorei(B.UNPACK_ROW_LENGTH,$t),_.pixelStorei(B.UNPACK_IMAGE_HEIGHT,le),_.pixelStorei(B.UNPACK_SKIP_PIXELS,tt),_.pixelStorei(B.UNPACK_SKIP_ROWS,un),_.pixelStorei(B.UNPACK_SKIP_IMAGES,zn),Re===0&&F.generateMipmaps&&B.generateMipmap(Oe),_.unbindTexture()},this.initRenderTarget=function(y){j.get(y).__webglFramebuffer===void 0&&oe.setupRenderTarget(y)},this.initTexture=function(y){y.isCubeTexture?oe.setTextureCube(y,0):y.isData3DTexture?oe.setTexture3D(y,0):y.isDataArrayTexture||y.isCompressedArrayTexture?oe.setTexture2DArray(y,0):oe.setTexture2D(y,0),_.unbindTexture()},this.resetState=function(){ee=0,ie=0,Z=null,_.reset(),Ae.reset()},typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("observe",{detail:this}))}get coordinateSystem(){return Un}get outputColorSpace(){return this._outputColorSpace}set outputColorSpace(e){this._outputColorSpace=e;let t=this.getContext();t.drawingBufferColorSpace=dt._getDrawingBufferColorSpace(e),t.unpackColorSpace=dt._getUnpackColorSpace()}};var zs={name:"CopyShader",uniforms:{tDiffuse:{value:null},opacity:{value:1}},vertexShader:`

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


		}`};var Sn=class{constructor(){this.isPass=!0,this.enabled=!0,this.needsSwap=!0,this.clear=!1,this.renderToScreen=!1}setSize(){}render(){console.error("THREE.Pass: .render() must be implemented in derived pass.")}dispose(){}},q0=new Si(-1,1,1,-1,0,1),Nc=class extends Rt{constructor(){super(),this.setAttribute("position",new vt([-1,3,0,-1,-1,0,3,-1,0],3)),this.setAttribute("uv",new vt([0,2,0,0,2,0],2))}},X0=new Nc,Ri=class{constructor(e){this._mesh=new yt(X0,e)}dispose(){this._mesh.geometry.dispose()}render(e){e.render(this._mesh,q0)}get material(){return this._mesh.material}set material(e){this._mesh.material=e}};var al=class extends Sn{constructor(e,t="tDiffuse"){super(),this.textureID=t,this.uniforms=null,this.material=null,e instanceof Ot?(this.uniforms=e.uniforms,this.material=e):e&&(this.uniforms=li.clone(e.uniforms),this.material=new Ot({name:e.name!==void 0?e.name:"unspecified",defines:Object.assign({},e.defines),uniforms:this.uniforms,vertexShader:e.vertexShader,fragmentShader:e.fragmentShader})),this._fsQuad=new Ri(this.material)}render(e,t,n){this.uniforms[this.textureID]&&(this.uniforms[this.textureID].value=n.texture),this._fsQuad.material=this.material,this.renderToScreen?(e.setRenderTarget(null),this._fsQuad.render(e)):(e.setRenderTarget(t),this.clear&&e.clear(e.autoClearColor,e.autoClearDepth,e.autoClearStencil),this._fsQuad.render(e))}dispose(){this.material.dispose(),this._fsQuad.dispose()}};var Yr=class extends Sn{constructor(e,t){super(),this.scene=e,this.camera=t,this.clear=!0,this.needsSwap=!1,this.inverse=!1}render(e,t,n){let s=e.getContext(),r=e.state;r.buffers.color.setMask(!1),r.buffers.depth.setMask(!1),r.buffers.color.setLocked(!0),r.buffers.depth.setLocked(!0);let a,o;this.inverse?(a=0,o=1):(a=1,o=0),r.buffers.stencil.setTest(!0),r.buffers.stencil.setOp(s.REPLACE,s.REPLACE,s.REPLACE),r.buffers.stencil.setFunc(s.ALWAYS,a,4294967295),r.buffers.stencil.setClear(o),r.buffers.stencil.setLocked(!0),e.setRenderTarget(n),this.clear&&e.clear(),e.render(this.scene,this.camera),e.setRenderTarget(t),this.clear&&e.clear(),e.render(this.scene,this.camera),r.buffers.color.setLocked(!1),r.buffers.depth.setLocked(!1),r.buffers.color.setMask(!0),r.buffers.depth.setMask(!0),r.buffers.stencil.setLocked(!1),r.buffers.stencil.setFunc(s.EQUAL,1,4294967295),r.buffers.stencil.setOp(s.KEEP,s.KEEP,s.KEEP),r.buffers.stencil.setLocked(!0)}},ol=class extends Sn{constructor(){super(),this.needsSwap=!1}render(e){e.state.buffers.stencil.setLocked(!1),e.state.buffers.stencil.setTest(!1)}};var ll=class{constructor(e,t){if(this.renderer=e,this._pixelRatio=e.getPixelRatio(),t===void 0){let n=e.getSize(new Ue);this._width=n.width,this._height=n.height,t=new Vt(this._width*this._pixelRatio,this._height*this._pixelRatio,{type:tn}),t.texture.name="EffectComposer.rt1"}else this._width=t.width,this._height=t.height;this.renderTarget1=t,this.renderTarget2=t.clone(),this.renderTarget2.texture.name="EffectComposer.rt2",this.writeBuffer=this.renderTarget1,this.readBuffer=this.renderTarget2,this.renderToScreen=!0,this.passes=[],this.copyPass=new al(zs),this.copyPass.material.blending=Cn,this.timer=new Ar}swapBuffers(){let e=this.readBuffer;this.readBuffer=this.writeBuffer,this.writeBuffer=e}addPass(e){this.passes.push(e),e.setSize(this._width*this._pixelRatio,this._height*this._pixelRatio)}insertPass(e,t){this.passes.splice(t,0,e),e.setSize(this._width*this._pixelRatio,this._height*this._pixelRatio)}removePass(e){let t=this.passes.indexOf(e);t!==-1&&this.passes.splice(t,1)}isLastEnabledPass(e){for(let t=e+1;t<this.passes.length;t++)if(this.passes[t].enabled)return!1;return!0}render(e){this.timer.update(),e===void 0&&(e=this.timer.getDelta());let t=this.renderer.getRenderTarget(),n=!1;for(let s=0,r=this.passes.length;s<r;s++){let a=this.passes[s];if(a.enabled!==!1){if(a.renderToScreen=this.renderToScreen&&this.isLastEnabledPass(s),a.render(this.renderer,this.writeBuffer,this.readBuffer,e,n),a.needsSwap){if(n){let o=this.renderer.getContext(),l=this.renderer.state.buffers.stencil;l.setFunc(o.NOTEQUAL,1,4294967295),this.copyPass.render(this.renderer,this.writeBuffer,this.readBuffer,e),l.setFunc(o.EQUAL,1,4294967295)}this.swapBuffers()}Yr!==void 0&&(a instanceof Yr?n=!0:a instanceof ol&&(n=!1))}}this.renderer.setRenderTarget(t)}reset(e){if(e===void 0){let t=this.renderer.getSize(new Ue);this._pixelRatio=this.renderer.getPixelRatio(),this._width=t.width,this._height=t.height,e=this.renderTarget1.clone(),e.setSize(this._width*this._pixelRatio,this._height*this._pixelRatio)}this.renderTarget1.dispose(),this.renderTarget2.dispose(),this.renderTarget1=e,this.renderTarget2=e.clone(),this.writeBuffer=this.renderTarget1,this.readBuffer=this.renderTarget2}setSize(e,t){this._width=e,this._height=t;let n=this._width*this._pixelRatio,s=this._height*this._pixelRatio;this.renderTarget1.setSize(n,s),this.renderTarget2.setSize(n,s);for(let r=0;r<this.passes.length;r++)this.passes[r].setSize(n,s)}setPixelRatio(e){this._pixelRatio=e,this.setSize(this._width,this._height)}dispose(){this.renderTarget1.dispose(),this.renderTarget2.dispose(),this.copyPass.dispose()}};var cl=class extends Sn{constructor(e,t,n=null,s=null,r=null){super(),this.scene=e,this.camera=t,this.overrideMaterial=n,this.clearColor=s,this.clearAlpha=r,this.clear=!0,this.clearDepth=!1,this.needsSwap=!1,this.isRenderPass=!0,this._oldClearColor=new Ke}render(e,t,n){let s=e.autoClear;e.autoClear=!1;let r,a;this.overrideMaterial!==null&&(a=this.scene.overrideMaterial,this.scene.overrideMaterial=this.overrideMaterial),this.clearColor!==null&&(e.getClearColor(this._oldClearColor),e.setClearColor(this.clearColor,e.getClearAlpha())),this.clearAlpha!==null&&(r=e.getClearAlpha(),e.setClearAlpha(this.clearAlpha)),this.clearDepth==!0&&e.clearDepth(),e.setRenderTarget(this.renderToScreen?null:n),this.clear===!0&&e.clear(e.autoClearColor,e.autoClearDepth,e.autoClearStencil),e.render(this.scene,this.camera),this.clearColor!==null&&e.setClearColor(this._oldClearColor),this.clearAlpha!==null&&e.setClearAlpha(r),this.overrideMaterial!==null&&(this.scene.overrideMaterial=a),e.autoClear=s}};var Ih={name:"LuminosityHighPassShader",uniforms:{tDiffuse:{value:null},luminosityThreshold:{value:1},smoothWidth:{value:1},defaultColor:{value:new Ke(0)},defaultOpacity:{value:0}},vertexShader:`

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

		}`};var Vs=class i extends Sn{constructor(e,t=1,n,s){super(),this.strength=t,this.radius=n,this.threshold=s,this.resolution=e!==void 0?new Ue(e.x,e.y):new Ue(256,256),this.clearColor=new Ke(0,0,0),this.needsSwap=!1,this.renderTargetsHorizontal=[],this.renderTargetsVertical=[],this.nMips=5;let r=Math.round(this.resolution.x/2),a=Math.round(this.resolution.y/2);this.renderTargetBright=new Vt(r,a,{type:tn,depthBuffer:!1}),this.renderTargetBright.texture.name="UnrealBloomPass.bright",this.renderTargetBright.texture.generateMipmaps=!1;for(let h=0;h<this.nMips;h++){let f=new Vt(r,a,{type:tn,depthBuffer:!1});f.texture.name="UnrealBloomPass.h"+h,f.texture.generateMipmaps=!1,this.renderTargetsHorizontal.push(f);let u=new Vt(r,a,{type:tn,depthBuffer:!1});u.texture.name="UnrealBloomPass.v"+h,u.texture.generateMipmaps=!1,this.renderTargetsVertical.push(u),r=Math.round(r/2),a=Math.round(a/2)}let o=Ih;this.highPassUniforms=li.clone(o.uniforms),this.highPassUniforms.luminosityThreshold.value=s,this.highPassUniforms.smoothWidth.value=.01,this.materialHighPassFilter=new Ot({uniforms:this.highPassUniforms,vertexShader:o.vertexShader,fragmentShader:o.fragmentShader}),this.separableBlurMaterials=[];let l=[6,10,14,18,22];r=Math.round(this.resolution.x/2),a=Math.round(this.resolution.y/2);for(let h=0;h<this.nMips;h++)this.separableBlurMaterials.push(this._getSeparableBlurMaterial(l[h])),this.separableBlurMaterials[h].uniforms.invSize.value=new Ue(1/r,1/a),r=Math.round(r/2),a=Math.round(a/2);this.compositeMaterial=this._getCompositeMaterial(this.nMips),this.compositeMaterial.uniforms.blurTexture1.value=this.renderTargetsVertical[0].texture,this.compositeMaterial.uniforms.blurTexture2.value=this.renderTargetsVertical[1].texture,this.compositeMaterial.uniforms.blurTexture3.value=this.renderTargetsVertical[2].texture,this.compositeMaterial.uniforms.blurTexture4.value=this.renderTargetsVertical[3].texture,this.compositeMaterial.uniforms.blurTexture5.value=this.renderTargetsVertical[4].texture,this.compositeMaterial.uniforms.bloomStrength.value=t,this.compositeMaterial.uniforms.bloomRadius.value=.1;let c=[1,.8,.6,.4,.2];this.compositeMaterial.uniforms.bloomFactors.value=c,this.bloomTintColors=[new D(1,1,1),new D(1,1,1),new D(1,1,1),new D(1,1,1),new D(1,1,1)],this.compositeMaterial.uniforms.bloomTintColors.value=this.bloomTintColors,this.copyUniforms=li.clone(zs.uniforms),this.blendMaterial=new Ot({uniforms:this.copyUniforms,vertexShader:zs.vertexShader,fragmentShader:zs.fragmentShader,premultipliedAlpha:!0,blending:Wi,depthTest:!1,depthWrite:!1,transparent:!0}),this._oldClearColor=new Ke,this._oldClearAlpha=1,this._basic=new fn,this._fsQuad=new Ri(null)}dispose(){for(let e=0;e<this.renderTargetsHorizontal.length;e++)this.renderTargetsHorizontal[e].dispose();for(let e=0;e<this.renderTargetsVertical.length;e++)this.renderTargetsVertical[e].dispose();this.renderTargetBright.dispose();for(let e=0;e<this.separableBlurMaterials.length;e++)this.separableBlurMaterials[e].dispose();this.compositeMaterial.dispose(),this.blendMaterial.dispose(),this._basic.dispose(),this._fsQuad.dispose()}setSize(e,t){let n=Math.round(e/2),s=Math.round(t/2);this.renderTargetBright.setSize(n,s);for(let r=0;r<this.nMips;r++)this.renderTargetsHorizontal[r].setSize(n,s),this.renderTargetsVertical[r].setSize(n,s),this.separableBlurMaterials[r].uniforms.invSize.value=new Ue(1/n,1/s),n=Math.round(n/2),s=Math.round(s/2)}render(e,t,n,s,r){e.getClearColor(this._oldClearColor),this._oldClearAlpha=e.getClearAlpha();let a=e.autoClear;e.autoClear=!1,e.setClearColor(this.clearColor,0),r&&e.state.buffers.stencil.setTest(!1),this.renderToScreen&&(this._fsQuad.material=this._basic,this._basic.map=n.texture,e.setRenderTarget(null),e.clear(),this._fsQuad.render(e)),this.highPassUniforms.tDiffuse.value=n.texture,this.highPassUniforms.luminosityThreshold.value=this.threshold,this._fsQuad.material=this.materialHighPassFilter,e.setRenderTarget(this.renderTargetBright),e.clear(),this._fsQuad.render(e);let o=this.renderTargetBright;for(let l=0;l<this.nMips;l++)this._fsQuad.material=this.separableBlurMaterials[l],this.separableBlurMaterials[l].uniforms.colorTexture.value=o.texture,this.separableBlurMaterials[l].uniforms.direction.value=i.BlurDirectionX,e.setRenderTarget(this.renderTargetsHorizontal[l]),e.clear(),this._fsQuad.render(e),this.separableBlurMaterials[l].uniforms.colorTexture.value=this.renderTargetsHorizontal[l].texture,this.separableBlurMaterials[l].uniforms.direction.value=i.BlurDirectionY,e.setRenderTarget(this.renderTargetsVertical[l]),e.clear(),this._fsQuad.render(e),o=this.renderTargetsVertical[l];this._fsQuad.material=this.compositeMaterial,this.compositeMaterial.uniforms.bloomStrength.value=this.strength,this.compositeMaterial.uniforms.bloomRadius.value=this.radius,this.compositeMaterial.uniforms.bloomTintColors.value=this.bloomTintColors,e.setRenderTarget(this.renderTargetsHorizontal[0]),e.clear(),this._fsQuad.render(e),this._fsQuad.material=this.blendMaterial,this.copyUniforms.tDiffuse.value=this.renderTargetsHorizontal[0].texture,r&&e.state.buffers.stencil.setTest(!0),this.renderToScreen?(e.setRenderTarget(null),this._fsQuad.render(e)):(e.setRenderTarget(n),this._fsQuad.render(e)),e.setClearColor(this._oldClearColor,this._oldClearAlpha),e.autoClear=a}_getSeparableBlurMaterial(e){let t=[],n=e/3;for(let a=0;a<e;a++)t.push(.39894*Math.exp(-.5*a*a/(n*n))/n);let s=[],r=[];for(let a=1;a<e;a+=2){let o=t[a],l=a+1<e?t[a+1]:0,c=o+l;s.push((a*o+(a+1)*l)/c),r.push(c)}return new Ot({defines:{KERNEL_PAIRS:s.length},uniforms:{colorTexture:{value:null},invSize:{value:new Ue(.5,.5)},direction:{value:new Ue(.5,.5)},centerWeight:{value:t[0]},gaussianOffsets:{value:s},gaussianWeights:{value:r}},vertexShader:`

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

				}`})}_getCompositeMaterial(e){return new Ot({defines:{NUM_MIPS:e},uniforms:{blurTexture1:{value:null},blurTexture2:{value:null},blurTexture3:{value:null},blurTexture4:{value:null},blurTexture5:{value:null},bloomStrength:{value:1},bloomFactors:{value:null},bloomTintColors:{value:null},bloomRadius:{value:0}},vertexShader:`

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

				}`})}};Vs.BlurDirectionX=new Ue(1,0);Vs.BlurDirectionY=new Ue(0,1);var Zr={name:"OutputShader",uniforms:{tDiffuse:{value:null},toneMappingExposure:{value:1}},vertexShader:`
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

		}`};var ul=class extends Sn{constructor(){super(),this.isOutputPass=!0,this.uniforms=li.clone(Zr.uniforms),this.material=new Cs({name:Zr.name,uniforms:this.uniforms,vertexShader:Zr.vertexShader,fragmentShader:Zr.fragmentShader}),this._fsQuad=new Ri(this.material),this._outputColorSpace=null,this._toneMapping=null}render(e,t,n){this.uniforms.tDiffuse.value=n.texture,this.uniforms.toneMappingExposure.value=e.toneMappingExposure,(this._outputColorSpace!==e.outputColorSpace||this._toneMapping!==e.toneMapping)&&(this._outputColorSpace=e.outputColorSpace,this._toneMapping=e.toneMapping,this.material.defines={},dt.getTransfer(this._outputColorSpace)===bt&&(this.material.defines.SRGB_TRANSFER=""),this._toneMapping===Pr?this.material.defines.LINEAR_TONE_MAPPING="":this._toneMapping===Ir?this.material.defines.REINHARD_TONE_MAPPING="":this._toneMapping===Lr?this.material.defines.CINEON_TONE_MAPPING="":this._toneMapping===Xi?this.material.defines.ACES_FILMIC_TONE_MAPPING="":this._toneMapping===Dr?this.material.defines.AGX_TONE_MAPPING="":this._toneMapping===Ur?this.material.defines.NEUTRAL_TONE_MAPPING="":this._toneMapping===Nr&&(this.material.defines.CUSTOM_TONE_MAPPING=""),this.material.needsUpdate=!0),this.renderToScreen===!0?(e.setRenderTarget(null),this._fsQuad.render(e)):(e.setRenderTarget(t),this.clear&&e.clear(e.autoClearColor,e.autoClearDepth,e.autoClearStencil),this._fsQuad.render(e))}dispose(){this.material.dispose(),this._fsQuad.dispose()}};var hl=class extends Bi{constructor(){super(),this.name="RoomEnvironment",this.position.y=-3.5;let e=new kn;e.deleteAttribute("uv");let t=new jt({side:en}),n=new jt,s=new ai(16777215,900,28,2);s.position.set(.418,16.199,.3),this.add(s);let r=new yt(e,t);r.position.set(-.757,13.219,.717),r.scale.set(31.713,28.305,28.591),this.add(r);let a=new gn(e,n,6),o=new Ht;o.position.set(-10.906,2.009,1.846),o.rotation.set(0,-.195,0),o.scale.set(2.328,7.905,4.651),o.updateMatrix(),a.setMatrixAt(0,o.matrix),o.position.set(-5.607,-.754,-.758),o.rotation.set(0,.994,0),o.scale.set(1.97,1.534,3.955),o.updateMatrix(),a.setMatrixAt(1,o.matrix),o.position.set(6.167,.857,7.803),o.rotation.set(0,.561,0),o.scale.set(3.927,6.285,3.687),o.updateMatrix(),a.setMatrixAt(2,o.matrix),o.position.set(-2.017,.018,6.124),o.rotation.set(0,.333,0),o.scale.set(2.002,4.566,2.064),o.updateMatrix(),a.setMatrixAt(3,o.matrix),o.position.set(2.291,-.756,-2.621),o.rotation.set(0,-.286,0),o.scale.set(1.546,1.552,1.496),o.updateMatrix(),a.setMatrixAt(4,o.matrix),o.position.set(-2.193,-.369,-5.547),o.rotation.set(0,.516,0),o.scale.set(3.875,3.487,2.986),o.updateMatrix(),a.setMatrixAt(5,o.matrix),this.add(a);let l=new yt(e,Hs(50));l.position.set(-16.116,14.37,8.208),l.scale.set(.1,2.428,2.739),this.add(l);let c=new yt(e,Hs(50));c.position.set(-16.109,18.021,-8.207),c.scale.set(.1,2.425,2.751),this.add(c);let h=new yt(e,Hs(17));h.position.set(14.904,12.198,-1.832),h.scale.set(.15,4.265,6.331),this.add(h);let f=new yt(e,Hs(43));f.position.set(-.462,8.89,14.52),f.scale.set(4.38,5.441,.088),this.add(f);let u=new yt(e,Hs(20));u.position.set(3.235,11.486,-12.541),u.scale.set(2.5,2,.1),this.add(u);let d=new yt(e,Hs(100));d.position.set(0,20,0),d.scale.set(1,.1,1),this.add(d)}dispose(){let e=new Set;this.traverse(t=>{t.isMesh&&(e.add(t.geometry),e.add(t.material))});for(let t of e)t.dispose()}};function Hs(i){return new br({color:0,emissive:16777215,emissiveIntensity:i})}var Lh={idle:{energy:.34,speed:.16,cyan:8314111,amber:15180363},receiving:{energy:.72,speed:.55,cyan:9169407,amber:16757851},working:{energy:1,speed:.92,cyan:10154751,amber:16760162},tool:{energy:.92,speed:1.12,cyan:8388572,amber:16761183},delegating:{energy:.88,speed:.82,cyan:7536592,amber:16756815},waiting_result:{energy:.48,speed:.28,cyan:7985407,amber:14064458},waiting_user:{energy:.76,speed:.34,cyan:16748405,amber:16738383},speaking:{energy:.7,speed:.74,cyan:9238751,amber:16762218},complete:{energy:.56,speed:.32,cyan:9041343,amber:16762733},error:{energy:.74,speed:.2,cyan:16744556,amber:16736072},offline:{energy:.12,speed:.04,cyan:5858923,amber:6706244}},Nh=Qo.clamp;function Dh({low:i=!1}={}){let e=new zt;e.name="Reactive orchestration quantum core";let t=new Set,n=Z=>(t.add(Z),Z),s={transparent:!0,depthWrite:!1,blending:Wi},r=n(new jt({color:16765065,emissive:16754237,emissiveIntensity:3.2,roughness:.28,metalness:.15,transparent:!0,opacity:.9})),a=new yt(n(new As(.48,i?2:4)),r);a.name="Energy nucleus",e.add(a);let o=n(new fn({color:10218239,wireframe:!0,opacity:.35,...s})),l=new yt(n(new As(.76,i?2:3)),o);l.name="Nucleus field cage",e.add(l);let c=new zt;c.name="Concentric computation rings",e.add(c);let h=[],f=[],u=i?7:11;for(let Z=0;Z<u;Z++){let Q=1.05+Z*.19,ue=n(new fn({color:Z%2?8710399:15773013,opacity:.16+Z%3*.035,...s}));h.push(ue);let se=new yt(n(new An(Q,.009+Z%3*.004,i?5:7,i?72:128)),ue);se.rotation.set(Z%3*Math.PI/3+.16,Z*2%5*Math.PI/5,Z%4*.19),se.userData.phase=Z*.71,c.add(se),f.push(se)}let d=new zt;d.name="Data orbit filaments",e.add(d);let g=[];for(let Z=0;Z<(i?7:12);Z++){let Q=[],ue=i?90:150,se=1.32+Z%5*.29,Ge=.56+Z%4*.11;for(let Xe=0;Xe<=ue;Xe++){let K=Xe/ue*Math.PI*2;Q.push(new D(Math.cos(K)*se,Math.sin(K)*se*Ge,Math.sin(K*2+Z)*.16))}let Pe=n(new Rt().setFromPoints(Q)),ot=n(new ri({color:Z%3?9169663:16758621,opacity:Z%3?.2:.28,...s}));g.push(ot);let $e=new dr(Pe,ot);$e.rotation.set(Z*.39,Z*.51,Z*.23),$e.userData.phase=Z*.64,d.add($e)}let M=1369948382,m=()=>(M=1664525*M+1013904223>>>0,M/4294967296),p=(Z,Q,ue,se,Ge)=>{let Pe=new Float32Array(Z*3);for(let K=0;K<Z;K++){let re=m()*2-1,Se=m()*Math.PI*2,Le=Q+(ue-Q)*Math.pow(m(),.62),Ie=Math.sqrt(Math.max(0,1-re*re));Pe[K*3]=Math.cos(Se)*Ie*Le,Pe[K*3+1]=re*Le,Pe[K*3+2]=Math.sin(Se)*Ie*Le}let ot=n(new Rt);ot.setAttribute("position",new Kt(Pe,3));let $e=n(new Ts({color:se,size:Ge,sizeAttenuation:!0,opacity:.72,...s})),Xe=new fr(ot,$e);return e.add(Xe),{points:Xe,material:$e}},T=p(i?430:1050,.86,2.86,10219263,i?.025:.021),C=p(i?180:430,.72,2.5,16757842,i?.031:.027),v=n(new fn({color:10940415,opacity:.12,...s})),w=new yt(n(new $n(.018,.055,7.5,10,1,!0)),v),S=w.clone();S.geometry=n(w.geometry.clone()),S.rotation.z=Math.PI/2,e.add(w,S);let I=n(new _n(.035,i?5:7,i?4:6)),x=n(new fn({color:15268607,...s})),A=new gn(I,x,i?24:48),N=new pt,k=new D(1,1,1),V=new Gt;for(let Z=0;Z<A.count;Z++){let Q=Z/A.count*Math.PI*2,ue=1.52+Z%6*.23,se=Math.sin(Q*3)*.9;N.compose(new D(Math.cos(Q)*ue,se,Math.sin(Q)*ue),V,k),A.setMatrixAt(Z,N)}A.instanceMatrix.needsUpdate=!0,e.add(A);let $=new ai(10153983,11,11,1.5);e.add($);let U=.28,W="offline",ee={running:0,pending:0,blocked:0,userBlocked:0,workingAgents:0};function ie({time:Z=0,delta:Q=1/60,state:ue=W,reduced:se=!1,activity:Ge=ee}={}){W=Lh[ue]?ue:"offline",ee={...ee,...Ge};let Pe=Lh[W],ot=Nh((ee.running||0)*.26+(ee.workingAgents||0)*.16+Math.min(ee.pending||0,6)*.035,0,.58),$e=Nh(Pe.energy+ot,.08,1.28),Xe=se?1:1-Math.exp(-Math.max(Q,0)*4.2);U=Qo.lerp(U,$e,Xe);let K=W==="waiting_user"||W==="error"||(ee.userBlocked||0)>0,re=K?16742500:Pe.cyan,Se=K?16735816:Pe.amber,Le=se?0:Pe.speed*(.72+U*.72),Ie=se?1:1+Math.sin(Z*(1.8+Le*3.2))*.055*U;a.scale.setScalar(Ie*(.92+U*.11)),l.scale.setScalar(1+(se?0:Math.sin(Z*1.13)*.025*U)),r.emissive.setHex(Se),r.emissiveIntensity=.2+U*3.7,r.opacity=.32+U*.55,o.color.setHex(re),o.opacity=.08+U*.34,c.rotation.y=se?0:Z*Le*.19,c.rotation.x=se?.11:.11+Math.sin(Z*.17)*.08,f.forEach((Ze,ht)=>{se||(Ze.rotation.z+=Q*Le*(.12+ht%5*.035)*(ht%2?1:-1)),Ze.material.color.setHex(ht%2?re:Se),Ze.material.opacity=.05+U*(.11+ht%3*.025)}),d.rotation.z=se?0:-Z*Le*.08,d.rotation.y=se?0:Z*Le*.06,g.forEach((Ze,ht)=>{Ze.color.setHex(ht%3?re:Se),Ze.opacity=.045+U*(ht%3?.18:.25)}),T.points.rotation.y=se?0:Z*Le*.09,T.points.rotation.z=se?0:Z*Le*.035,C.points.rotation.y=se?0:-Z*Le*.14,C.points.rotation.x=se?0:Z*Le*.028,T.material.color.setHex(re),T.material.opacity=.16+U*.68,C.material.color.setHex(Se),C.material.opacity=.1+U*.64,v.color.setHex(re),v.opacity=W==="offline"?.02:.035+U*.14,w.scale.set(1,.75+U*.32,1),S.scale.set(.72+U*.34,1,1),x.color.setHex(K?16752767:15137791),A.rotation.y=se?0:Z*Le*.12,A.rotation.x=se?0:Math.sin(Z*.11)*.14,$.color.setHex(re),$.intensity=.45+U*12.5}return{group:e,update:ie,setActivity(Z){ee={...ee,...Z}},diagnostics(){return{type:"reactive-quantum-core",state:W,energy:U,rings:f.length,particles:T.points.geometry.attributes.position.count+C.points.geometry.attributes.position.count,nodes:A.count,activity:{...ee}}},dispose(){for(let Z of t)Z.dispose?.()}}}var Dc=new D(0,1,0),jr=Math.PI*2;function Uh(i){let e=i|0||1;return()=>(e^=e<<13,e^=e>>>17,e^=e<<5,(e>>>0)/4294967296)}function Fh(){return{armor:new jt({color:2698543,metalness:.88,roughness:.39}),edge:new jt({color:7828841,metalness:.92,roughness:.3}),black:new jt({color:527374,metalness:.6,roughness:.48}),bronze:new jt({color:6048048,metalness:.91,roughness:.39}),cable:new jt({color:1711906,metalness:.7,roughness:.44}),light:new jt({color:16756811,emissive:16751153,emissiveIntensity:1.2,metalness:.35,roughness:.27}),lens:new jt({color:16768921,emissive:16752947,emissiveIntensity:2.5,metalness:.3,roughness:.16})}}var dl=class{constructor(e){this.materials=e,this.buckets={},this.count=0,this.matrix=new pt,this.normalMatrix=new nt,this.position=new D,this.normal=new D,this.rotation=new Gt}add(e,t,n=[0,0,0],s=[1,1,1],r=null){let a=t.index?t.toNonIndexed():t,o=this.buckets[e]||(this.buckets[e]={position:[],normal:[]});this.rotation.identity(),r instanceof Gt?this.rotation.copy(r):r&&this.rotation.setFromEuler(new En(...r)),this.matrix.compose(new D(...n),this.rotation,new D(...s)),this.normalMatrix.getNormalMatrix(this.matrix);let l=a.getAttribute("position"),c=a.getAttribute("normal");for(let h=0;h<l.count;h++)this.position.fromBufferAttribute(l,h).applyMatrix4(this.matrix),this.normal.fromBufferAttribute(c,h).applyNormalMatrix(this.normalMatrix),o.position.push(this.position.x,this.position.y,this.position.z),o.normal.push(this.normal.x,this.normal.y,this.normal.z);this.count++,a!==t&&a.dispose(),t.dispose()}box(e,t,n,s=null){this.add(e,new kn(1,1,1),t,n,s)}strut(e,t,n,s=.015,r=6,a=s){let o=new D(...t),l=new D(...n),c=l.clone().sub(o),h=c.length();h<1e-4||this.add(e,new $n(a,s,h,r),o.add(l).multiplyScalar(.5).toArray(),[1,1,1],new Gt().setFromUnitVectors(Dc,c.normalize()))}cable(e,t,n=.015,s=18){let r=new ws(t.map(a=>new D(...a)));this.add(e,new Mr(r,s,n,5,!1))}finish(e){for(let[t,n]of Object.entries(this.buckets)){let s=new Rt;s.setAttribute("position",new vt(n.position,3)),s.setAttribute("normal",new vt(n.normal,3)),s.computeBoundingSphere();let r=new yt(s,this.materials[t]);r.name=`machine-batch-${t}`,e.add(r)}return Object.keys(this.buckets).length}};function Pi(i,e,t,n,s=.075){i.add("black",new $n(s*1.4,s*1.3,.105,12),[e,t,n-.025],[1,1,1],[Math.PI/2,0,0]),i.add("edge",new An(s*1.15,.015,5,16),[e,t,n+.028]),i.add("bronze",new An(s*.82,.007,4,14),[e,t,n+.039]),i.add("lens",new _n(s*.69,12,8),[e,t,n+.025],[1,1,.35]),i.add("black",new _n(s*.19,8,6),[e,t,n+.053],[1,1,.2])}function $0(i,e,t){i.add("black",new _n(.48,20,12),[0,0,0],[1,.9,.91]);let n=t?12:18;for(let s=0;s<n;s++){let r=s/n*jr,a=[];for(let c=0;c<7;c++){let h=-1.23+c*2.46/6;a.push([Math.cos(r)*Math.cos(h)*.53,Math.sin(h)*.5,Math.sin(r)*Math.cos(h)*.46])}for(let c=0;c<a.length-1;c++)i.strut(s%4===0?"bronze":"armor",a[c],a[c+1],.034,6),i.add("edge",new _n(.028,6,4),a[c]);let o=r+.1,l=[Math.cos(o)*.48,.15*Math.sin(r*2),Math.sin(o)*.43];i.box("armor",l,[.12,.19+e()*.13,.06],[0,-o+Math.PI/2,.12]),i.strut("edge",[Math.cos(r)*.32,.43,Math.sin(r)*.3],[Math.cos(r)*.18,.62+e()*.12,Math.sin(r)*.17],.012)}for(let s of[-.27,.02,.29]){let r=Math.sqrt(1-(s/.52)**2)*.51;i.add("edge",new An(r,.014,5,40),[0,s,0],[1,.85,1],[Math.PI/2,0,0])}i.box("armor",[0,.045,.43],[.37,.28,.14],[.05,0,0]),Pi(i,0,.07,.53,.092),Pi(i,-.16,-.025,.486,.048),Pi(i,.16,-.025,.486,.048),Pi(i,-.095,.205,.46,.035),Pi(i,.095,.205,.46,.035);for(let s=0;s<4;s++){let r=(s-1.5)*.095;i.box("black",[r,-.35,.26],[.068,.16,.11]),i.box("bronze",[r,-.44,.26],[.075,.025,.12]),i.box("light",[r,-.41,.321],[.031,.018,.008])}for(let s=0;s<95;s++){let r=e()*jr,a=(e()-.5)*.8,o=Math.sqrt(1-a*a/.25)*.51;i.box(s%8===0?"bronze":"edge",[Math.cos(r)*o,a,Math.sin(r)*o*.9],[.015,.027,.013],[e(),r,e()])}for(let s=0;s<5;s++){let r=(s-2)*.12,a=.68+e()*.35;i.strut("armor",[r,.38,-.05],[r*1.12,a,-.08],.022,6,.007),i.box("edge",[r,.54,-.05],[.035,.07,.04]),s%2===0&&i.add("light",new _n(.012,6,4),[r*1.12,a,-.08])}}function Y0(i,e,t){i.box("black",[0,0,0],[.63,.72,.56]);let n=t?34:56;for(let s=0;s<n;s++){let a=s%4*Math.PI/2,o=.065+e()*.12,l=.19+e()*.48,c=(e()-.5)*.63,h=.29+e()*.11,f=Math.sin(a)*h+Math.cos(a)*c,u=Math.cos(a)*h-Math.sin(a)*c,d=(e()-.5)*.36;i.box(s%5===0?"bronze":"armor",[f,d,u],[o,l,.11],[0,a,0]),i.box("edge",[f,d+l*.45,u],[o*1.09,.018,.13],[0,a,0]),i.box("black",[f,d-l*.25,u],[o*1.1,.03,.13],[0,a,0]);let g=new D(Math.sin(a),0,Math.cos(a));for(let M=0;M<3;M++)i.box(M%3===0?"light":"edge",[f+g.x*.061,d+M*.042,u+g.z*.061],[.012,.023,.008],[0,a,0])}for(let s=-1;s<=1;s+=2)for(let r=0;r<4;r++){let a=(r-1.5)*.16;i.box("armor",[s*.44,a,-.07],[.34,.038,.55],[0,0,s*.07]),i.strut("edge",[s*.29,a-.09,.15],[s*.6,a,.15],.009),i.box("bronze",[s*.59,a,-.08],[.015,.045,.56])}Pi(i,0,.04,.435,.063),Pi(i,-.14,.09,.41,.028),Pi(i,.14,.09,.41,.028);for(let s=0;s<9;s++){let r=(e()-.5)*.54,a=(e()-.5)*.45,o=.22+e()*.45;i.box("armor",[r,.35+o/2,a],[.043,o,.05]),i.strut("edge",[r,.35+o,a],[r,.54+o,a],.007,5,.002),i.box("bronze",[r,.46,a],[.067,.016,.075])}for(let s=0;s<12;s++){let r=(s%4-1.5)*.145,a=(Math.floor(s/4)-1)*.14,o=.14+e()*.22;i.strut("armor",[r,-.33,a],[r,-.33-o,a],.03,6,.014),i.add("bronze",new An(.025,.007,4,8),[r,-.36-o/2,a],[1,1,1],[Math.PI/2,0,0])}}function Z0(i,e,t,n,s){let r=n==="hermes"?s?7:10:6,a=s?11:17,o=r*a,l=new gn(new $n(1,1,1,6),e.cable,o),c=new gn(new kn(1,1,1),e.armor,o),h=new gn(new _n(1,6,4),e.edge,o),f=new gn(new gr(1,1,5),e.bronze,r*2);for(let S of[l,c,h,f])S.instanceMatrix.setUsage(lc),S.frustumCulled=!1,S.name=`articulated-${S===l?"cables":S===c?"armor":S===h?"joints":"claws"}`,i.add(S);let u=Array.from({length:r},(S,I)=>({angle:I/r*jr+(n==="hermes"?0:.14),phase:t()*jr,reach:(n==="hermes"?1.12:.84)+t()*.35,depth:(t()-.5)*.9,curl:t()>.5?1:-1})),d=new pt,g=new Gt,M=new D,m=new D,p=new D,T=new D,C=new D;function v(S,I,x,A,N){let k=S.angle+Math.sin(x*.27+S.phase)*.065*A+S.curl*I*I*.75,V=.43+Math.sin(I*1.37)*S.reach,$=Math.sin(x*.48+S.phase-I*3.9)*.085*A*I;return N.set(Math.cos(k)*V,Math.sin(k)*V*.61-I*I*.35+$,-.1+Math.sin(I*Math.PI)*S.depth+Math.cos(x*.39+S.phase)*.07*A*I),N}function w(S,I){let x=0;for(let A=0;A<u.length;A++){let N=u[A];for(let k=0;k<a;k++,x++){let V=k/a;v(N,V,S,I,M),v(N,(k+1)/a,S,I,m),T.copy(m).sub(M);let $=T.length();g.setFromUnitVectors(Dc,T.normalize()),p.copy(M).add(m).multiplyScalar(.5);let U=(1-V*.77)*.029;C.set(U,$,U),d.compose(p,g,C),l.setMatrixAt(x,d),C.set(U*2.4,$*.58,U*2.15),d.compose(p,g,C),c.setMatrixAt(x,d),C.setScalar(U*1.08),d.compose(M,g,C),h.setMatrixAt(x,d)}v(N,1,S,I,M);for(let k=0;k<2;k++)v(N,.96,S,I,m),T.copy(M).sub(m).normalize(),T.z+=k?.4:-.4,T.normalize(),p.copy(M).addScaledVector(T,.047),g.setFromUnitVectors(Dc,T),d.compose(p,g,C.set(.015,.12,.015)),f.setMatrixAt(A*2+k,d)}for(let A of[l,c,h,f])A.instanceMatrix.needsUpdate=!0}return w(0,0),{update:w,armCount:r,segments:a}}function kh({kind:i="hermes",seed:e=1,low:t=!1}={}){let n=new zt;n.name=`flying-${i}-machine`;let s=new zt;s.name="hovering-articulated-body",n.add(s);let r=Uh(e),a=Fh(),o=new dl(a);i==="codex"?Y0(o,r,t):$0(o,r,t);let l=o.finish(s),c=Z0(s,a,r,i,t),h=r()*jr,f=1,u="",d=0;return{group:n,update({time:g=0,state:M="idle",reduced:m=!1,delta:p=1/60}={}){let T=["offline","unavailable","unknown","disconnected"].includes(M),C=["working","tool","delegating","receiving","speaking"].includes(M),v=["error","blocked","waiting_user"].includes(M),w=T?.09:v?.75:C?1.4:.72;f=m?w:f+(w-f)*Math.min(1,p*4),a.lens.emissiveIntensity=f*2,a.light.emissiveIntensity=f*.62,M!==u&&(a.lens.emissive.setHex(v?16474676:16754235),a.light.emissive.setHex(v?15888690:16753719),u=M);let S=m||T?0:C?1:.46;s.position.y=Math.sin(g*.53+h)*.045*S,s.rotation.y=Math.sin(g*.24+h)*.1*S,s.rotation.z=Math.sin(g*.31+h)*.025*S,s.rotation.x=Math.sin(g*.29+h*.3)*.024*S,(!t||d++%2===0||m)&&c.update(m?0:g,S)},diagnostics(){return{kind:i,geometryOnly:!0,staticPieces:o.count,articulatedArms:c.armCount,segmentsPerArm:c.segments,drawCalls:l+4,nominalCoreDiameter:1.2,fullSpan:i==="hermes"?3.65:3.15}}}}function Oh({low:i=!1}={}){let e=new zt;e.name="machine-city-architecture";let t=Uh(691309),n=Fh();n.black.color.setHex(133133),n.armor.color.setHex(1188138),n.edge.color.setHex(2179408),n.bronze.color.setHex(2573133),n.cable.color.setHex(463899),n.light.color.setHex(2990020),n.light.emissive.setHex(1740216),n.light.emissiveIntensity=.42;let s=new dl(n),r=[],a=i?18:30;for(let l=0;l<a;l++){let c=l%2?1:-1,h=13+t()*18,f=c*(8.6+t()*17),u=-h,d=.45+t()*.9,g=8+t()*15,M=-7.5+g/2;r.push({x:f,z:u,width:d,height:g}),s.box("black",[f,M,u],[d,g,d*.92]);let m=i?2:3;for(let T=0;T<m;T++){let C=f+(T/Math.max(1,m-1)-.5)*d*1.12,v=d*(.58+t()*.18);s.box("armor",[C,M,u+v*.14],[d*.09,g*.94,v]),s.box("edge",[C,M,u+v*.67],[.018,g*.9,.018])}let p=Math.floor(g/1.18);for(let T=0;T<p;T++){let C=-7.25+T*1.18;s.box("armor",[f,C,u+d*.12],[d*1.13,.035,d*.92]),T%4===0&&s.box("edge",[f,C+.09,u+d*.53],[d*.92,.015,.02]);let v=i?1:2;for(let w=0;w<v;w++)t()<.68||s.box("light",[f+((w+.5)/v-.5)*d*.72,C+.18,u+d*.49],[.022+t()*.025,.045+t()*.06,.012])}}for(let l=0;l<(i?4:7);l++){let c=l%2?1:-1,h=c*(8.3+t()*2.2),f=c*(18+t()*8),u=-4.8+t()*12.5,d=-14-t()*10,g=Math.abs(f-h),M=(h+f)/2;s.box("black",[M,u,d],[g,.11,.36]),s.box("edge",[M,u+.34,d+.16],[g,.022,.022]);for(let m=0;m<Math.floor(g/2);m++){let p=Math.min(h,f)+m*2;s.strut("armor",[p,u-.24,d+.2],[p+c*.55,u+.34,d+.2],.014),m%3===0&&s.box("light",[p,u+.1,d+.25],[.025,.035,.01])}}for(let l of[-1,1])for(let c=0;c<(i?3:5);c++){let h=l*(9+t()*6),f=-14-t()*10,u=l*(.5+t()*.55);s.cable("cable",[[h,13,f],[h+u*.25,7,f+.35],[h+u*.65,1,f],[h+u,-7,f-.5]],.012+t()*.018,18)}let o=s.finish(e);return{group:e,update(){},diagnostics(){return{geometryOnly:!0,towers:r.length,staticPieces:s.count,drawCalls:o,centerClearance:8,depthRange:[-31,-13],visualMode:"quiet-server-room"}}}}var j0=["majak-hermes","majak-codex","quantlab-hermes","quantlab-codex"],Jr=(i,e,t)=>new D(i,e,t),J0={working:"working",blocked:"waiting_user",done:"complete",idle:"idle",unknown:"offline",offline:"offline"},Bh=new Set(["offline","unavailable","unknown","disconnected"]);function K0(i,e,t,n=12){let s=Math.min(e/2,t/2+n);return Math.max(s,Math.min(e-s,i))}function Q0(i,e,t,n,s){let r=Math.tan(e*Math.PI/360)*t*i,a=24/s*r*2,o=Math.max(0,r-1.4*n-.18-a);return Math.min(i<1?2.48:Math.min(5.35,i*2.58),o)}function zh(i,e){let t=new il({canvas:i,antialias:!0,powerPreference:"high-performance"}),n=innerWidth<760||navigator.deviceMemory&&navigator.deviceMemory<=4,s=Math.min(devicePixelRatio,n?1:1.5);t.setPixelRatio(s),t.outputColorSpace=dn,t.toneMapping=Xi,t.toneMappingExposure=1.2;let r=new Bi;r.background=new Ke(133393),r.fog=new or(463644,.041);let a=new Jt(35,1,.1,90);a.position.set(.35,.55,13.8),a.lookAt(0,.35,0);let o=new Os(t),l=new hl,c=o.fromScene(l,.08).texture;r.environment=c,r.environmentIntensity=.72,l.dispose(),o.dispose(),r.add(new Tr(9423327,329997,.82));let h=new Gi(12115434,3.6);h.position.set(-5,7,8),r.add(h);let f=new Gi(4169662,1.35);f.position.set(5,1,6),r.add(f);let u=new Gi(5228520,4.4);u.position.set(4,6,-6),r.add(u);let d=new ai(14917708,7.5,13,2);d.position.set(-1,-3,3),r.add(d);let g=Dh({low:n}),M=new zt;M.position.set(0,.42,-.35),M.add(g.group),r.add(M);let m=Oh({low:n});r.add(m.group);let p=new Map;for(let[L,z]of j0.entries()){let ne=kh({kind:z.endsWith("hermes")?"hermes":"codex",seed:L+71,low:n});ne.group.userData.agentId=z,ne.base=Jr(0,0,0),ne.id=z,ne.status="offline",ne.group.traverse(_e=>{_e.userData.agentId=z}),r.add(ne.group),p.set(z,ne)}let T=new zt;T.name="swarm-task-nodes",r.add(T);let C=new zt;C.name="swarm-task-links",r.add(C);let v=new Map,w=[],S={running:7598815,pending:12163946,blocked:16747634,failed:16736082,done:7522710},I={running:0,blocked:1,failed:2,pending:3,done:4},x=null,A=()=>{};function N(L){T.remove(L.group),L.group.traverse(z=>{if(z.geometry?.dispose(),z.material)for(let ne of Array.isArray(z.material)?z.material:[z.material])ne.dispose()})}function k(L,z,ne,_e=0){let ce=new zt;ce.name=_e?"swarm-task-cluster":`swarm-task-${L}`;let pe=S[z]||10261639,ye=new yt(_e?new _r(.22,0):new vr(.16,0),new jt({color:2435885,emissive:pe,emissiveIntensity:z==="running"?1.8:.75,metalness:.72,roughness:.28})),we=new yt(new An(_e?.3:.23,.012,5,20),new fn({color:pe,transparent:!0,opacity:.7}));we.rotation.x=Math.PI/2,ce.add(ye,we),ce.userData.taskId=_e?null:L,ce.userData.clusterCount=_e,ce.traverse(O=>{O.userData.taskId=_e?null:L});let ke={id:L,status:z,index:ne,clusterCount:_e,group:ce,body:ye,ring:we,base:new D};return T.add(ce),ke}function V(){let L=[...v.values()],z=L.length;L.forEach((ne,_e)=>{let ce=_e<10?0:1,pe=ce?_e-10:_e,ye=ce?Math.max(1,z-10):Math.min(10,z),we=-Math.PI*.92+pe/Math.max(1,ye-1)*Math.PI*1.84,ke=ce?3.55:2.65,O=ce?2.38:1.82;ne.base.set(Math.cos(we)*ke,.42+Math.sin(we)*O,ce?1.48:1.18),ne.group.position.copy(ne.base),ne.group.scale.setScalar(ne.clusterCount?.9:.72)})}function $(){for(;w.length;){let L=w.pop();C.remove(L.line),L.line.geometry.dispose(),L.line.material.dispose()}}function U(){for(let L of w){let z=v.get(L.from),ne=v.get(L.to);if(!z||!ne){L.line.visible=!1;continue}L.line.visible=!0,L.line.geometry.setFromPoints([z.group.position,ne.group.position])}}function W(L){$();let z=new Set;for(let ne of L){let _e=[];ne.parent_task_id&&_e.push([ne.parent_task_id,"parent"]);for(let ce of ne.dependencies||[])_e.push([ce,"dependency"]);for(let[ce,pe]of _e){if(!v.has(ce)||!v.has(ne.task_id))continue;let ye=`${ce}\0${ne.task_id}\0${pe}`;if(z.has(ye))continue;z.add(ye);let we=new Rt,ke=new ri({color:pe==="dependency"?14981684:7598815,transparent:!0,opacity:pe==="dependency"?.26:.34}),O=new Vi(we,ke);O.name=`swarm-task-${pe}-edge`,O.renderOrder=-1,C.add(O),w.push({line:O,from:ce,to:ne.task_id,kind:pe})}}U()}function ee(L){let z=[...Array.isArray(L)?L:[]].filter(ye=>ye&&ye.status!=="done").sort((ye,we)=>(I[ye.status]??9)-(I[we.status]??9)||(we.updated_at||0)-(ye.updated_at||0)||String(ye.task_id).localeCompare(String(we.task_id))),ne=20,_e=z.slice(0,ne),ce=new Map(_e.map((ye,we)=>[ye.task_id,{row:ye,index:we}])),pe=Math.max(0,z.length-ne);pe&&ce.set("__cluster__",{row:{task_id:"__cluster__",status:"pending"},index:_e.length,clusterCount:pe});for(let[ye,we]of[...v])ce.has(ye)||(N(we),v.delete(ye));for(let[ye,we]of ce){let ke=v.get(ye);(!ke||ke.status!==we.row.status||ke.clusterCount!==(we.clusterCount||0))&&(ke&&N(ke),ke=k(ye,we.row.status,we.index,we.clusterCount||0),v.set(ye,ke)),ke.index=we.index,ke.status=we.row.status}x&&!v.has(x)&&(x=null),V(),W(_e),Se=!0}let ie=new Rt;ie.setAttribute("position",new Kt(new Float32Array(195),3));let Z=new Vi(ie,new ri({color:9035184,transparent:!0,opacity:.32}));Z.visible=!1,r.add(Z);let Q=new gn(new _n(.028,6,4),new fn({color:12582855}),12);Q.visible=!1,r.add(Q);let ue=new pt,se=Jr(1,1,1),Ge=new Gt,Pe=new ll(t);Pe.addPass(new cl(r,a));let ot=new Vs(new Ue(1,1),.38,.38,1.18);Pe.addPass(ot),Pe.addPass(new ul);let $e="offline",Xe=matchMedia("(prefers-reduced-motion: reduce)").matches,K=!0,re=!1,Se=!0,Le={enabled:!1,state:"idle",target:"majak-codex"},Ie=null,Ze=()=>{},ht=0,st=0,it=0,Qe=0,rt=0,gt=!1,Ct=0,Ut=0,_t={running:0,pending:0,blocked:0,workingAgents:0,activeAgent:null},Et=new Cr,B=new Ue,wt=new D,ct=L=>{let z=p.get(L);return z?.group.visible?z:null};function P(L){re||(re=!0,cancelAnimationFrame(Qe),Qe=0,e.hidden=!1,i.dispatchEvent(new CustomEvent("scene-unavailable",{bubbles:!0})),L&&console.error("Machine City renderer unavailable",L))}let _=()=>{if(!re)try{let{width:L,height:z}=i.getBoundingClientRect();if(!L||!z)return;a.aspect=L/z,a.position.z=a.aspect<1?17.6:13.8,a.updateProjectionMatrix(),a.updateMatrixWorld(),t.setSize(L,z,!1),Pe.setSize(L,z);let ne=a.aspect<1?.48:.7,_e=a.getWorldDirection(Jr(0,0,0));[...p.values()].forEach((ce,pe)=>{let ye=pe%2===0?.5:1.05,we=Q0(a.aspect,a.fov,Math.max(.1,a.position.z-ye-.25),ne,L),ke=a.position.x+(ye-a.position.z)/_e.z*_e.x;ce.base.set(ke+(pe<2?-we:we),pe%2===0?2.15:-1.1,ye),ce.group.scale.setScalar(ne),ce.group.position.copy(ce.base)}),V(),Se=!0}catch(L){P(L)}},G=new ResizeObserver(_);G.observe(i);function j(L){let z=i.getBoundingClientRect();return!z.width||!z.height?null:(B.set((L.clientX-z.left)/z.width*2-1,-(L.clientY-z.top)/z.height*2+1),Et.setFromCamera(B,a),Et.intersectObjects([...v.values()].map(_e=>_e.group),!0).find(_e=>!!_e.object.userData.taskId)?.object.userData.taskId||null)}i.addEventListener("pointermove",L=>{let z=i.getBoundingClientRect();Ct=(L.clientX-z.left)/z.width-.5,Ut=(L.clientY-z.top)/z.height-.5;let ne=j(L);i.dispatchEvent(new CustomEvent("swarm-task-hover",{bubbles:!0,detail:{taskId:ne,x:L.clientX-z.left,y:L.clientY-z.top}}))}),i.addEventListener("pointerleave",()=>{Ct=0,Ut=0,i.dispatchEvent(new CustomEvent("swarm-task-hover",{bubbles:!0,detail:{taskId:null,x:0,y:0}}))}),i.addEventListener("click",L=>{if(re||!K)return;let z=i.getBoundingClientRect();if(!z.width||!z.height)return;B.set((L.clientX-z.left)/z.width*2-1,-(L.clientY-z.top)/z.height*2+1),Et.setFromCamera(B,a);let ne=[...p.values()].filter(ce=>ce.group.visible).map(ce=>ce.group).concat([...v.values()].map(ce=>ce.group)),_e=Et.intersectObjects(ne,!0).find(ce=>{for(let pe=ce.object;pe;pe=pe.parent)if(!pe.visible)return!1;return!!(ce.object.userData.agentId||ce.object.userData.taskId)});if(_e){let ce=_e.object.userData.taskId,pe=_e.object.userData.agentId;ce?A(ce):pe&&Ze(pe)}}),i.addEventListener("webglcontextlost",L=>{L.preventDefault(),P()}),i.addEventListener("webglcontextrestored",()=>{e.hidden=!1}),document.addEventListener("visibilitychange",()=>{it=0,Se=!0});function oe(){r.updateMatrixWorld(),a.updateMatrixWorld();let L=i.getBoundingClientRect();if(!L.width||!L.height)return;for(let[ne,_e]of p){let ce=document.querySelector(`#film-view [data-agent="${ne}"]`);if(!ce||!_e.group.visible)continue;_e.group.getWorldPosition(wt),wt.y-=.78*_e.group.scale.x,wt.project(a);let pe=ce.offsetParent?.getBoundingClientRect()||L,ye=K0((wt.x*.5+.5)*L.width,L.width,ce.offsetWidth);ce.style.setProperty("--agent-x",`${L.left-pe.left+ye}px`),ce.style.setProperty("--agent-y",`${L.top-pe.top+(-wt.y*.5+.5)*L.height}px`)}let z=x?v.get(x):null;z?(z.group.getWorldPosition(wt),wt.project(a),i.dispatchEvent(new CustomEvent("swarm-task-focus-position",{bubbles:!0,detail:{taskId:z.id,x:(wt.x*.5+.5)*L.width,y:(-wt.y*.5+.5)*L.height}}))):i.dispatchEvent(new CustomEvent("swarm-task-focus-position",{bubbles:!0,detail:{taskId:null,x:0,y:0}}))}function Me(L){if(Qe=0,!re){try{if(document.hidden||!K||Xe&&!Se){Qe=requestAnimationFrame(Me);return}let z=it?Math.min((L-it)/1e3,.08):1/60;it=L,Xe||(st+=z);let ne=Xe?0:st,_e=Xe||Bh.has($e);M.rotation.y=ht||(_e?0:ne*.028+Ct*.11),M.rotation.x=_e?0:-Ut*.07+Math.sin(ne*.17)*.025;let ce=[...p.values()].filter(Y=>Y.group.visible&&Y.status==="working").length;g.update({time:ne,state:$e,reduced:Xe,delta:z,activity:{..._t,workingAgents:ce}}),m.update({time:ne,reduced:Xe});let pe=0;for(let Y of p.values()){let be=pe*1.83,Ae=Le.enabled?Y.id===Le.target?$e:"idle":J0[Y.status]||"offline";Y.group.position.copy(Y.base),!Xe&&!Bh.has(Ae)&&(Y.group.position.x+=Math.sin(ne*.24+be)*.18,Y.group.position.y+=Math.sin(ne*.37+be)*.15,Y.group.position.z+=Math.cos(ne*.22+be)*.25),Y.group.rotation.y=Y.base.x<0?.3:-.3,Y.update({time:ne,state:Ae,reduced:Xe,delta:z}),pe++}let ye=0;for(let Y of v.values()){let be=ye*.73;Y.group.position.copy(Y.base),Xe?(Y.ring.rotation.z=be,Y.group.rotation.y=0):(Y.group.position.y+=Math.sin(ne*.42+be)*.055,Y.group.position.z+=Math.cos(ne*.31+be)*.08,Y.ring.rotation.z=ne*(Y.status==="running"?.75:.18)+be,Y.group.rotation.y=ne*.08+be*.2);let Ae=x===Y.id,de=Y.clusterCount?.9:.72;Y.group.scale.setScalar(Ae?de*1.45:de),Y.body.material.emissiveIntensity=(Y.status==="running"?1.8:.75)+(Ae?.9:0),ye++}U();let we=_t.activeAgent?ct(_t.activeAgent):[...p.values()].find(Y=>Y.group.visible&&["working","blocked"].includes(Y.status)),ke=Le.enabled?ct(Le.target):we,O=Le.enabled?$e:$e==="waiting_user"||(_t.userBlocked||0)>0||ke?.status==="blocked"?"waiting_user":"working",Te=!!(ke&&(Le.enabled?["delegating","waiting_result","complete","tool"].includes($e):["working","waiting_user"].includes(O)));if(Z.visible=Te,Q.visible=Te&&O!=="waiting_user",Te){let Y=ke.group.position,be=new Hi(Jr(Y.x<0?-1.55:1.55,.5,.6),Jr(Y.x*.56,Y.y-.42,2.05),Y.clone()),Ae=be.getPoints(64);ie.setFromPoints(Ae);let de=O==="waiting_user"?16742500:Y.x<0?16758359:7598815;Z.material.color.setHex(de),Q.material.color.setHex(de),Z.material.opacity=O==="waiting_user"?.2:.43;for(let Ve=0;Ve<12;Ve++){let ze=Xe?(Ve+1)/13:(ne*(.3+Math.min(_t.running||0,2)*.08)+Ve/12)%1;Le.enabled&&$e==="complete"&&(ze=1-ze),ue.compose(be.getPoint(ze),Ge,se),Q.setMatrixAt(Ve,ue)}Q.instanceMatrix.needsUpdate=!0}oe(),Pe.render(),Se=!1,!Xe&&z>.048?rt++:rt=Math.max(0,rt-1),rt>90&&!gt&&(s=1,t.setPixelRatio(1),Pe.setPixelRatio(1),ot.enabled=!1,gt=!0,_())}catch(z){P(z);return}re||(Qe=requestAnimationFrame(Me))}}_(),re||(Qe=requestAnimationFrame(Me));let Ee=document.querySelector("#inspect-model");return Ee?.addEventListener("click",()=>{ht=ht===0?.6:ht===.6?1.2:0,Ee.textContent=ht===0?"Prohl\xE9dnout j\xE1dro":ht===.6?"J\xE1dro ze t\u0159\xED \u010Dtvrtin":"J\xE1dro z boku",Se=!0}),{setState(L){$e!==L&&($e=L,Se=!0)},setReduced(L){Xe=L,Se=!0,it=0},setActive(L){K=L,Se=!0,it=0,L&&_()},setGaze(){},setActivity(L){_t={..._t,...L},g.setActivity(_t),Se=!0},setAgents(L){for(let z of p.values()){let ne=L.find(_e=>(_e.id||_e.agent)===z.id);z.status=ne?.status||"offline",z.group.visible=!!ne&&ne.visible!==!1}ct(Ie)||(Ie=null),ct(Le.target)||(Le.target=null),Se=!0},setTasks(L){ee(L)},focusAgent(L){Ie=ct(L)?L:null,Se=!0},focusTask(L){x=L&&v.has(L)?L:null,Se=!0},setDemo(L){Le={...Le,...L},ct(Le.target)||(Le.target=null),Se=!0},onSelect(L){Ze=L},onTaskSelect(L){A=L},diagnostics(){return{geometry:"true-3d",state:$e,reduced:Xe,active:K,contextLost:re,quality:gt?"adaptive-low":n?"low":"high",core:g.diagnostics(),drones:[...p.values()].map(L=>({id:L.id,position:L.group.position.toArray(),...L.diagnostics()})),tasks:[...v.values()].map(L=>({id:L.id,status:L.status,clusterCount:L.clusterCount,position:L.group.position.toArray()})),taskEdges:w.map(L=>({from:L.from,to:L.to,kind:L.kind})),drawCalls:t.info.render.calls,triangles:t.info.render.triangles}},quality:n?"\xDAsporn\xE1":"Vysok\xE1",dispose(){cancelAnimationFrame(Qe),G.disconnect(),r.traverse(L=>{if(L.geometry?.dispose(),L.material)for(let z of Array.isArray(L.material)?L.material:[L.material])z.dispose()}),c.dispose(),Pe.dispose(),t.dispose()}}}var Gs={idle:{label:"\u010Cek\xE1",copy:"Klidov\xFD re\u017Eim \xB7 \u017E\xE1dn\xE1 hl\xE1\u0161en\xE1 aktivn\xED pr\xE1ce",tone:"amber"},receiving:{label:"P\u0159ij\xEDm\xE1 zad\xE1n\xED",copy:"Demo p\u0159ijet\xED nov\xE9ho zad\xE1n\xED",tone:"amber"},working:{label:"Zpracov\xE1v\xE1 \xFAlohu",copy:"Demo zpracov\xE1n\xED \xFAlohy",tone:"amber"},tool:{label:"Pou\u017E\xEDv\xE1 n\xE1stroj",copy:"Demo n\xE1strojov\xE9 operace \xB7 \u017Eiv\xFD zdroj tuto ud\xE1lost neposkytuje",tone:"green"},delegating:{label:"Deleguje",copy:"Demo p\u0159ed\xE1n\xED \xFAkolu vybran\xE9mu agentovi",tone:"green"},waiting_result:{label:"\u010Cek\xE1 na v\xFDsledek",copy:"Demo \u010Dek\xE1n\xED \xB7 neprob\xEDh\xE1 intenzivn\xED pr\xE1ce",tone:"amber"},waiting_user:{label:"\u010Cek\xE1 na z\xE1sah",copy:"Agent je blokovan\xFD a pot\u0159ebuje kontrolu",tone:"red"},speaking:{label:"Mluv\xED",copy:"Stylizovan\xE1 animace odpov\u011Bdi \xB7 audio nen\xED p\u0159ipojeno",tone:"green"},complete:{label:"\xDAloha dokon\u010Dena",copy:"Agent ohl\xE1sil stav done",tone:"green"},error:{label:"Probl\xE9m syst\xE9mu",copy:"Jeden nebo v\xEDce datov\xFDch zdroj\u016F selhalo",tone:"red"},offline:{label:"Odpojeno",copy:"\u010Cerstv\xFD \u017Eiv\xFD stav nen\xED dostupn\xFD",tone:"muted"}},vn=["majak","quantlab"],Vh=new Set(["majak-hermes","majak-codex","quantlab-hermes","quantlab-codex"]),Hh={hermes:"Orchestrace, pam\u011B\u0165, n\xE1stroje a \u0159\xEDzen\xED pr\xE1ce",codex:"Implementace, testov\xE1n\xED a technick\xE1 revize"},Gh={idle:"\u010Cek\xE1",working:"Pracuje",blocked:"Blokov\xE1no",done:"Hotovo",unknown:"Nezn\xE1m\xE9",offline:"Odpojeno"},on={pending:"\u010Cek\xE1",running:"B\u011B\u017E\xED",blocked:"Blokov\xE1no",done:"Hotovo",failed:"Selhalo"},Wh={pending:"pending",ready:"pending",running:"running",review:"running",blocked:"blocked",done:"done",failed:"failed",cancelled:"done"},qh="Bbambaaamm/Autonomous-Quant-Lab",kt=new Intl.NumberFormat("cs-CZ"),ji=new Intl.NumberFormat("cs-CZ",{notation:"compact",maximumFractionDigits:1}),ve=i=>String(i??"").replace(/[&<>"']/g,e=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[e]),Pt=i=>i==null?"Nedostupn\xE9":kt.format(i),Ii=i=>i==null?"Nezn\xE1m\xE9":i===0?"0 USD":`${(i/1e6).toFixed(4)} USD`,Ji=i=>i==null?"Nedostupn\xE9":i<1e3?`${kt.format(Math.round(i))} ms`:`${(i/1e3).toFixed(2)} s`,ci=i=>Number.isFinite(i)?`${Math.max(0,Math.floor(Date.now()/1e3-i))} s`:"Nedostupn\xE9",ui=i=>Number.isFinite(i)?new Date(i*1e3).toLocaleString("cs-CZ",{day:"2-digit",month:"2-digit",hour:"2-digit",minute:"2-digit"}):"\u2014",nn=i=>Number.isFinite(i?.issue)?`#${i.issue}`:"bez issue",Kr=i=>i.endsWith("-hermes")?"hermes":"codex",Uc=i=>Gh[i]||Gh.unknown,e_=i=>({green:"#6adf9a",red:"#ff7159",muted:"#716d66",amber:"#e49a34"})[i],Xh=(i,e="provider")=>{let t=i.filter(r=>typeof r[e]=="string"&&Number.isFinite(r.last_used_at)).sort((r,a)=>a.last_used_at-r.last_used_at||r[e].localeCompare(a[e])),n=t[0]?.[e]||null,s=[...new Set(t.map(r=>r[e]))].filter(r=>r!==n);return{currentProvider:n,historicalProviders:s}};function $h(i){let e=b=>document.querySelector(b),t={film:e("#film-view"),work:e("#work-view"),faceState:e("#face-state"),faceTask:e("#face-task"),faceSignal:e("#face-signal"),header:e("#header-status"),liveDot:e("#live-dot"),snapshotAge:e("#snapshot-age"),agentCount:e("#agent-count"),queueCount:e("#queue-count"),requestCount:e("#request-count"),searchCount:e("#search-count"),searchLatency:e("#search-latency"),costTotal:e("#cost-total"),attention:e("#attention-action"),coordinatorCurrent:e("#coordinator-current"),coordinatorNext:e("#coordinator-next"),demo:e("#demo-panel"),demoStates:e("#demo-states"),detail:e("#agent-detail"),backdrop:e("#drawer-backdrop"),canvas:e("#machine-scene"),fallback:e("#webgl-fallback"),swarmKpis:e("#swarm-kpis"),kpiActive:e("#kpi-active"),kpiRunning:e("#kpi-running"),kpiWaiting:e("#kpi-waiting"),kpiBlocked:e("#kpi-blocked"),kpiQueue:e("#kpi-queue"),kpiSuccess:e("#kpi-success"),kpiRetries:e("#kpi-retries"),kpiAvgTask:e("#kpi-avg-task"),kpiTokens:e("#kpi-tokens"),kpiCost:e("#kpi-cost"),dagStatus:e("#taskgraph-status"),dagNodes:e("#taskgraph-nodes"),analyticsGrid:e("#swarm-analytics-grid")},n=null,s=!1,r="idle",a="work",o=null,l=null,c="all",h=matchMedia("(prefers-reduced-motion: reduce)").matches,f=null,u=!1,d=null,g="",M=null,m=!1,p="Na\u010D\xEDt\xE1m skute\u010Dn\xE1 data";function T(){u=!0,t.fallback.hidden=!1;try{f?.setActive(!1)}catch{}Li("work")}try{f=i(t.canvas,t.fallback),u=!f}catch{u=!0,t.fallback.hidden=!1}t.canvas.addEventListener("webglcontextlost",b=>{b.preventDefault(),T()}),t.canvas.addEventListener("scene-unavailable",T),t.canvas.addEventListener("swarm-task-hover",b=>{let R=e("#task-hover-label"),E=b.detail||{},H=$e(E.taskId);if(!R||!H||a!=="film"){R&&(R.hidden=!0);return}R.textContent=`${nn(H)} \xB7 ${on[H.status]||H.status} \xB7 ${H.issue_title||H.task_id}`,R.style.left=`${Math.max(12,E.x+14)}px`,R.style.top=`${Math.max(72,E.y+14)}px`,R.hidden=!1}),t.canvas.addEventListener("swarm-task-focus-position",b=>{let R=e("#task-selected-label"),E=b.detail||{},H=$e(E.taskId);if(!R||!H||a!=="film"||l!==H.task_id){R&&(R.hidden=!0);return}R.innerHTML=`<b>${ve(nn(H))}</b><span>${ve(on[H.status]||H.status)}</span>`,R.style.left=`${Math.max(56,E.x)}px`,R.style.top=`${Math.max(110,E.y)}px`,R.hidden=!1});function C(b,...R){if(!(!f||u||typeof f[b]!="function"))try{return f[b](...R)}catch{T()}}function v(b,R){return n?.sources.find(E=>E.profile===b&&E.kind===R)}function w(){return vn.map(b=>v(b,"queue")).filter(Boolean)}function S(b=null){return(b?[v(b,"queue")].filter(Boolean):w()).flatMap(E=>E?.status==="available"?E.rows:[])}function I(b){return b?.repo==="Bbambaaamm/dotacni-majak"?"majak":"quantlab"}function x(b){return b==="majak-hermes"?"dotacni-majak-hermes":b}function A(b){return b==="dotacni-majak-hermes"?"majak-hermes":b}function N(){return v("quantlab","swarm")}function k(){let b=N();return b?.status==="available"&&b.rows.length===1?b.rows[0]:null}function V(){let b=k(),R=N();if(!b)return[];let E=/^\d+$/.test(b.issue)?Number(b.issue):null,H=R?.data_at??R?.observed_at??null;return b.tasks.map(he=>({task_id:he.task_id,status:Wh[he.state]||"blocked",raw_state:he.state,attempts:he.attempt,max_attempts:he.max_attempts,not_before:null,updated_at:H,agent:he.agent_id||null,kind:"herdr_swarm",blocker:he.blocker,pr_number:null,issue:E,issue_state:b.issue_state||"unknown",issue_title:`Herdr swarm \xB7 ${he.role}`,repo:b.repo,parent_task_id:he.parent_task_id,parent_agent_id:he.parent_agent_id,dependencies:he.dependencies,result_sha:he.result_sha,model:he.model,fallback_model:he.fallback_model,fencing_token:he.fencing_token}))}function $(b){return b?.issue_state==="closed"||b?.issue_open===!1&&b?.scheduler_state==="closed"}function U(b){return!$(b)||["running","pending"].includes(b.status)}function W(b=null){return S(b).filter(U)}function ee(){return V().filter(U)}function ie(){return k()?.agents||[]}function Z(){return k()?.edges||[]}function Q(){return k()?[...V(),...S("majak")]:S()}function ue(){return v("quantlab","admission")}function se(){let b=ue();return b?.status==="available"?b.rows:[]}function Ge(){return se().filter(b=>b.event==="deny")}function Pe(){let b=v("quantlab","release");return b?.status==="available"&&b.rows.length===1?b.rows[0]:null}function ot(){return W().filter(b=>b.status!=="done")}function $e(b){return Q().find(R=>R.task_id===b)||S().find(R=>R.task_id===b)||null}let Xe=new Set(["user_action_required","agent_interactive_input_required","github_write_auth_required"]);function K(b=null){return W(b).filter(R=>["blocked","failed"].includes(R.status)&&Xe.has(R.blocker))}function re(b=null){return W(b).filter(R=>["blocked","failed"].includes(R.status)&&!Xe.has(R.blocker))}function Se(b=null){let R={running:0,blocked:1,failed:2};return W().filter(E=>(!b||E.agent===b)&&Object.hasOwn(R,E.status)).sort((E,H)=>R[E.status]-R[H.status]||(H.updated_at||0)-(E.updated_at||0)||E.task_id.localeCompare(H.task_id))[0]}function Le(b=null){return W().filter(R=>(!b||R.agent===b)&&R.status==="pending").sort((R,E)=>(R.not_before??Number.MAX_SAFE_INTEGER)-(E.not_before??Number.MAX_SAFE_INTEGER)||R.task_id.localeCompare(E.task_id))[0]}function Ie(b){return b?`${nn(b)} \xB7 ${b.task_id}`:"\u017D\xE1dn\xE1"}function Ze(b){return b?`${Pt(b.attempts)} / ${Pt(b.max_attempts)}`:"Nedostupn\xE9"}function ht(b){return Number.isFinite(b?.issue)?`https://github.com/${b.repo||qh}/issues/${b.issue}`:null}function st(b){return Number.isFinite(b?.pr_number)?`https://github.com/${b.repo||qh}/pull/${b.pr_number}`:null}function it(b,R){return b?`<a href="${ve(b)}" target="_blank" rel="noopener noreferrer">${ve(R)}</a>`:""}function Qe(){return vn.flatMap(b=>{let R=v(b,"herdr");return R?.status==="available"?R.rows.map(E=>({...E,profile:b})):[]})}function rt(b){let R=Qe().filter(E=>E.profile===b);return R.length?R:["hermes","codex"].map(E=>({agent:`${b}-${E}`,profile:b,status:"offline",unavailable:!0}))}function gt(b){let R=v(b,"router"),E=R?.status==="available",H=E?R.rows:[],he=E?H.reduce((xe,qe)=>xe+qe.requests,0):null,te=xe=>!E||H.some(qe=>!Number.isFinite(qe[xe]))?null:H.reduce((qe,We)=>qe+We[xe],0),me=xe=>{if(!E)return{known:null,knownRequests:null,unknownRequests:null,coverage:null};let qe=0,We=0,cn=0;for(let y of H)Number.isFinite(y[xe])?(qe+=y[xe],We+=y.requests):cn+=y.requests;return{known:qe,knownRequests:We,unknownRequests:cn,coverage:he===0?100:Math.round(We/he*100)}},fe=me("input_tokens"),ae=me("output_tokens"),Ye=me("cost_microusd"),je=Xh(H);return{requests:he,input:te("input_tokens"),output:te("output_tokens"),cost:te("cost_microusd"),inputKnown:fe.known,outputKnown:ae.known,costKnown:Ye.known,inputKnownRequests:fe.knownRequests,outputKnownRequests:ae.knownRequests,costKnownRequests:Ye.knownRequests,inputUnknownRequests:fe.unknownRequests,outputUnknownRequests:ae.unknownRequests,costUnknownRequests:Ye.unknownRequests,inputCoverage:fe.coverage,outputCoverage:ae.coverage,costCoverage:Ye.coverage,fallbacks:te("fallback_count"),models:[...new Set(H.map(xe=>xe.actual_model).filter(xe=>typeof xe=="string"))],providers:[...new Set(H.map(xe=>xe.provider).filter(xe=>typeof xe=="string"))],...je,rows:H,router:R}}function Ct(b){let R=v(b,"search"),E=R?.status==="available",H=E?R.rows:[],he=je=>!E||H.some(xe=>!Number.isFinite(xe[je]))?null:H.reduce((xe,qe)=>xe+qe[je],0),te=E?he("searches"):null,me=E?he("duration_ms"):null,fe=E?H.length?Math.max(...H.map(je=>je.max_duration_ms).filter(Number.isFinite)):0:null,ae=Object.fromEntries(["fast","deep","browser"].map(je=>[je,E?H.filter(xe=>xe.route_mode===je).reduce((xe,qe)=>xe+(Number.isFinite(qe.searches)?qe.searches:0),0):null])),Ye=Xh(H);return{searches:te,successful:E?he("successful_searches"):null,duration:me,avgLatency:te==null||me==null?null:te===0?0:me/te,maxLatency:fe,fallbacks:E?he("fallback_count"):null,cost:E?he("cost_microusd"):null,results:E?he("result_count"):null,extracts:E?he("extract_count"):null,providers:[...new Set(H.map(je=>je.provider).filter(je=>typeof je=="string"))],fallbackProviders:[...new Set(H.map(je=>je.fallback_provider).filter(je=>typeof je=="string"))],...Ye,routes:ae,search:R}}function Ut(){let b=v("majak","codex");return{source:b,row:b?.status==="available"&&b.rows.length===1?b.rows[0]:null}}function _t(){return vn.flatMap(b=>gt(b).rows.map(R=>({...R,profile:b})))}function Et(){let b=new Map;for(let R of _t()){let E=R.actual_model;b.has(E)||b.set(E,{model:E,requests:0,fallbacks:0,successes:0,durationMs:0,durationRequests:0,inputTokens:0,outputTokens:0,tokenKnownRequests:0,tokenUnknownRequests:0});let H=b.get(E);H.requests+=R.requests,H.fallbacks+=R.fallback_count,H.successes+=R.successful_requests,Number.isFinite(R.duration_ms)&&(H.durationMs+=R.duration_ms,H.durationRequests+=R.requests),Number.isFinite(R.input_tokens)&&Number.isFinite(R.output_tokens)?(H.inputTokens+=R.input_tokens,H.outputTokens+=R.output_tokens,H.tokenKnownRequests+=R.requests):H.tokenUnknownRequests+=R.requests}return[...b.values()].sort((R,E)=>E.requests-R.requests||R.model.localeCompare(E.model))}function B(){let b=k()?[...ee(),...W("majak")]:W(),R=ge=>b.filter(Fe=>Fe.status===ge).length,E=R("running"),H=R("pending"),he=R("failed"),te=R("blocked"),me=R("done"),fe=te+he,ae=k()?ie().length+Qe().filter(ge=>ge.profile==="majak"&&ge.status==="working").length:Qe().filter(ge=>ge.status==="working").length,Ye=b.reduce((ge,Fe)=>ge+(Number.isSafeInteger(Fe.attempts)?Math.max(0,Fe.attempts-1):0),0),je=me+he,xe=je?Math.round(me/je*100):null,qe=vn.map(gt),We=qe.every(ge=>ge.router?.status==="available"),cn=We?qe.reduce((ge,Fe)=>ge+(Fe.inputKnown||0),0):null,y=We?qe.reduce((ge,Fe)=>ge+(Fe.outputKnown||0),0):null,F=We?qe.reduce((ge,Fe)=>ge+(Fe.inputUnknownRequests||0)+(Fe.outputUnknownRequests||0),0):null,J=We?qe.reduce((ge,Fe)=>ge+(Fe.costKnown||0),0):null,X=We?qe.reduce((ge,Fe)=>ge+(Fe.costUnknownRequests||0),0):null,q=Et(),Re=q.reduce((ge,Fe)=>ge+Fe.durationMs,0),Ne=q.reduce((ge,Fe)=>ge+Fe.durationRequests,0),Ce=Ne?Re/Ne:null,Be=qe.every(ge=>ge.fallbacks!=null)?qe.reduce((ge,Fe)=>ge+Fe.fallbacks,0):null;return{queue:b,running:E,waiting:H,blocked:fe,blockedOnly:te,done:me,failed:he,activeAgents:ae,retries:Ye,success:xe,activeQueue:E+H+fe,inputTokens:cn,outputTokens:y,tokenUnknownRequests:F,cost:J,costUnknownRequests:X,requestLatency:Ce,fallbacks:Be,models:q}}function wt(){let b=e("#swarm-kpis");if(!b)return;if(!n){b.innerHTML='<div class="swarm-kpi"><span>Swarm</span><b>\u2014</b><small>telemetrie nedostupn\xE1</small></div>';return}let R=B(),E=R.inputTokens==null||R.outputTokens==null?"\u2014":ji.format(R.inputTokens+R.outputTokens),H=R.cost==null?"\u2014":Ii(R.cost),he=[["Active",R.activeAgents,"\u017Eiv\xED agenti",R.activeAgents?"running":""],["Running",R.running,"b\u011B\u017E\xEDc\xED tasky",R.running?"running":""],["Waiting",R.waiting,"pending",R.waiting?"waiting":""],["Blocked / Failed",`${R.blockedOnly} / ${R.failed}`,"odd\u011Blen\xE9 stavy",R.blocked?"blocked":""],["Queue",R.activeQueue,"aktivn\xED tasky",""],["Terminal success",R.success==null?"\u2014":`${R.success} %`,`${R.done} done \xB7 ${R.failed} failed`,""],["Retries",R.retries,"opakovan\xE9 pokusy",R.retries?"waiting":""],["Avg task","\u2014","duration telemetry chyb\xED",""],["Tokens",E,R.tokenUnknownRequests?`${R.tokenUnknownRequests} req bez token\u016F`:"known input + output",""],["Cost known",H,R.costUnknownRequests?`${R.costUnknownRequests} req unknown`:"v\u0161echny requesty ocen\u011Bn\xE9",""]];b.innerHTML=he.map(([te,me,fe,ae])=>`<article class="swarm-kpi" data-state="${ae}"><span>${ve(te)}</span><b>${ve(String(me))}</b><small>${ve(fe)}</small></article>`).join("")}function ct(b){return[{running:0,blocked:1,failed:2,pending:3,done:4}[b.status]??9,-(b.updated_at||0),b.task_id]}function P(){return[...Q()].sort((b,R)=>{let E=ct(b),H=ct(R);return E[0]-H[0]||E[1]-H[1]||String(E[2]).localeCompare(String(H[2]))})}function _(b){return c==="all"?!0:c==="blocked"?b.status==="blocked"||b.status==="failed":b.status===c}function G(b){let R=b.raw_state||on[b.status]||b.status;return`<button type="button" class="taskgraph-node" role="option" aria-selected="${String(l===b.task_id)}" data-task-id="${ve(b.task_id)}" data-status="${ve(b.status)}"><b>${ve(nn(b))} \xB7 ${ve(b.task_id)}</b><span>${ve(R)}</span><small>${ve(b.issue_title||b.kind)} \xB7 pokus ${ve(Ze(b))}</small></button>`}function j(b,R,E){if(!R.length)return"";let H=R.slice(0,E),he=R.length-H.length;return`<div class="taskgraph-lane" role="group" aria-label="${ve(b)}"><span class="taskgraph-lane-label">${ve(b)}</span><div class="taskgraph-lane-track">${H.map(G).join("")}${he?`<div class="taskgraph-node taskgraph-cluster" data-status="pending"><b>+${he} uzl\u016F</b><span>LOD cluster</span><small>dal\u0161\xED sanitizovan\xE9 tasky</small></div>`:""}</div></div>`}function oe(b,R){let E=b.filter(te=>R.has(te.from_task)&&R.has(te.to_task));if(!E.length)return"";let H=E.slice(0,16),he=E.length-H.length;return`<div class="taskgraph-edge-strip" aria-label="Autoritativn\xED DAG hrany">${H.map(te=>`<span class="taskgraph-edge" data-edge-kind="${ve(te.kind)}"><b>${ve(te.from_task)}</b><i>\u2192</i><b>${ve(te.to_task)}</b><small>${ve(te.kind)}</small></span>`).join("")}${he?`<span class="taskgraph-edge taskgraph-edge-overflow">+${he} hran</span>`:""}</div>`}function Me(){let b=e("#taskgraph-nodes"),R=e("#taskgraph-status");if(!b||!R)return;let E=N(),H=w().filter(xe=>xe.status==="available"),he=k()?E:H.length?{status:"available",observed_at:Math.max(...H.map(xe=>xe.observed_at||0))}:null;if(!he||he.status!=="available"){R.textContent="Task telemetry nen\xED dostupn\xE1.",b.innerHTML='<div class="obs-empty">TaskGraph nelze zobrazit bez durable queue.</div>',C("setTasks",[]);return}let te=P(),me=te.filter(_);document.querySelectorAll("[data-task-filter]").forEach(xe=>xe.setAttribute("aria-pressed",String(xe.dataset.taskFilter===c)));let fe=c==="all"?"v\u0161echny stavy":c==="pending"?"\u010Dekaj\xEDc\xED":c==="blocked"?"blocked + failed":c,ae=Z();if(R.textContent=k()?`Autoritativn\xED Herdr DAG \xB7 ${ae.length} hran \xB7 filtr: ${fe}.`:`Dependency telemetry nen\xED v aktu\xE1ln\xEDm kontraktu \xB7 hrany se nevym\xFD\u0161lej\xED \xB7 filtr: ${fe}.`,!te.length){b.innerHTML='<div class="obs-empty">Durable queue je pr\xE1zdn\xE1.</div>',C("setTasks",[]);return}if(!me.length){b.innerHTML='<div class="obs-empty">Pro zvolen\xFD filtr nejsou \u017E\xE1dn\xE9 tasky.</div>',C("setTasks",te.filter(xe=>xe.status!=="done"));return}let Ye=k()?oe(ae,new Set(me.map(xe=>xe.task_id))):"";if(c==="all"){let xe=me.filter(We=>["running","blocked","failed"].includes(We.status)),qe=me.filter(We=>!["running","blocked","failed"].includes(We.status));b.innerHTML=Ye+j("Aktivn\xED / probl\xE9mov\xE9",xe,10)+j("\u010Cekaj\xEDc\xED / hotov\xE9",qe,14)}else b.innerHTML=Ye+j(fe,me,18);let je=[...b.querySelectorAll("[data-task-id]")];je.forEach((xe,qe)=>{xe.addEventListener("click",()=>ln(xe.dataset.taskId)),xe.addEventListener("keydown",We=>{if(!["ArrowRight","ArrowLeft","ArrowDown","ArrowUp","Home","End","Enter"," "].includes(We.key))return;if(We.key==="Enter"||We.key===" "){We.preventDefault(),ln(xe.dataset.taskId);return}We.preventDefault();let cn=We.key==="ArrowDown"?2:We.key==="ArrowUp"?-2:We.key==="ArrowRight"?1:We.key==="ArrowLeft"?-1:0,y=We.key==="Home"?0:We.key==="End"?je.length-1:Math.max(0,Math.min(je.length-1,qe+cn));je[y]?.focus()})}),C("setTasks",te.filter(xe=>xe.status!=="done"))}function Ee(){let b=e("#swarm-analytics-grid");if(!b)return;if(!n){b.innerHTML='<article class="swarm-card"><header><h3>Swarm</h3></header><strong>\u2014</strong><p>\u017Div\xE1 telemetrie nen\xED dostupn\xE1.</p></article>';return}let R=B(),E=R.queue.length||1,H=`<div class="swarm-mini">${["running","pending","blocked","failed","done"].map(ae=>{let Ye=R.queue.filter(je=>je.status===ae).length;return Ye?`<i class="${ae}" style="width:${(Ye/E*100).toFixed(1)}%" title="${ve(on[ae]||ae)}: ${Ye}"></i>`:""}).join("")}</div>`,he=R.inputTokens==null||R.outputTokens==null?"\u2014":ji.format(R.inputTokens+R.outputTokens),te=R.cost==null?"\u2014":Ii(R.cost),me=R.models.slice(0,4),fe=me.length?me.map(ae=>`${ve(ae.model)} ${kt.format(ae.requests)}`).join(" \xB7 "):"Model telemetry nen\xED dostupn\xE1.";b.innerHTML=['<article class="swarm-card"><header><h3>Throughput</h3><span>tasks / time</span></header><strong>\u2014</strong><p>\u010Casov\xE1 \u0159ada dokon\u010Den\xFDch task\u016F nen\xED v autoritativn\xEDm kontraktu; hodnotu neodhadujeme.</p></article>',`<article class="swarm-card"><header><h3>Queue depth</h3><span>snapshot</span></header><strong>${kt.format(R.activeQueue)}</strong>${H}<p>${R.running} running \xB7 ${R.waiting} waiting \xB7 ${R.blockedOnly} blocked \xB7 ${R.failed} failed \xB7 ${R.done} done</p></article>`,`<article class="swarm-card"><header><h3>Latency</h3><span>router request avg</span></header><strong>${ve(Ji(R.requestLatency))}</strong><p>Task queue/review p50+p95 nejsou dostupn\xE9; zobrazen je pouze m\u011B\u0159en\xFD router request pr\u016Fm\u011Br.</p></article>`,`<article class="swarm-card"><header><h3>Tokens & cost</h3><span>known telemetry</span></header><strong>${ve(he)}</strong><p>${ve(te)} known \xB7 ${R.costUnknownRequests||0} req unknown \xB7 ${R.tokenUnknownRequests||0} token fields unknown.</p></article>`,`<article class="swarm-card"><header><h3>Model mix</h3><span>requests</span></header><strong>${kt.format(R.models.reduce((ae,Ye)=>ae+Ye.requests,0))}</strong><p>${fe}</p></article>`,`<article class="swarm-card"><header><h3>Reliability</h3><span>snapshot</span></header><strong>${kt.format(R.retries)}</strong><p>true retries \xB7 ${R.blockedOnly} blocked \xB7 ${R.failed} failed \xB7 ${Pt(R.fallbacks)} model fallback\u016F.</p></article>`].join("")}function L(){wt(),Me(),Ee()}function z(b){return Number.isFinite(b)?new Date(b*1e3).toLocaleString("cs-CZ",{day:"2-digit",month:"2-digit",hour:"2-digit",minute:"2-digit"}):"Nezn\xE1m\xFD"}function ne(b){if(!Number.isFinite(b))return"\u010Das resetu nen\xED dostupn\xFD";let R=Math.max(0,b-Date.now()/1e3),E=Math.ceil(R/3600);return E<48?`za ${E} h`:`za ${Math.ceil(E/24)} dn\xED`}function _e(b,R,{id:E,suffix:H="",maxValue:he=null}={}){if(!b.length)return'<div class="obs-empty">Zat\xEDm bez \u010Dasov\xE9 \u0159ady.</div>';let te=680,me=178,fe=42,ae=12,Ye=12,je=26,xe=b.map(ge=>Number(ge[R])).filter(Number.isFinite);if(!xe.length)return'<div class="obs-empty">Zat\xEDm bez m\u011B\u0159en\xFDch hodnot.</div>';let qe=Math.max(he??0,...xe,1),We=ge=>b.length===1?(fe+te-ae)/2:fe+ge/(b.length-1)*(te-fe-ae),cn=ge=>Ye+(1-Math.max(0,ge)/qe)*(me-Ye-je),y=b.map((ge,Fe)=>[We(Fe),cn(Number(ge[R]))]),F=y.map(([ge,Fe],at)=>`${at?"L":"M"}${ge.toFixed(1)},${Fe.toFixed(1)}`).join(" "),J=`${F} L${We(b.length-1).toFixed(1)},${me-je} L${We(0).toFixed(1)},${me-je} Z`,X=b[0].day||ui(b[0].at),q=b[Math.floor((b.length-1)/2)],Re=q.day||ui(q.at),Ne=b[b.length-1],Ce=Ne.day||ui(Ne.at),Be=ve(E||"obs");return`<svg class="obs-chart" viewBox="0 0 ${te} ${me}" role="img">
      <defs><linearGradient id="${Be}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#70ddd0"/><stop offset="1" stop-color="#70ddd0" stop-opacity="0"/></linearGradient></defs>
      ${[0,.25,.5,.75,1].map(ge=>`<line class="grid" x1="${fe}" y1="${(Ye+ge*(me-Ye-je)).toFixed(1)}" x2="${te-ae}" y2="${(Ye+ge*(me-Ye-je)).toFixed(1)}"/>`).join("")}
      <path class="area" style="fill:url(#${Be})" d="${J}"/><path class="line" d="${F}"/>
      ${y.slice(-12).map(([ge,Fe])=>`<circle class="point" cx="${ge.toFixed(1)}" cy="${Fe.toFixed(1)}" r="2.1"/>`).join("")}
      <text class="axis" x="2" y="${Ye+4}">${ve(ji.format(qe)+H)}</text><text class="axis" x="2" y="${me-je+3}">0${ve(H)}</text>
      <text class="axis" x="${fe}" y="${me-7}">${ve(X)}</text><text class="axis" text-anchor="middle" x="${(te/2).toFixed(1)}" y="${me-7}">${ve(Re)}</text><text class="axis" text-anchor="end" x="${te-ae}" y="${me-7}">${ve(Ce)}</text>
    </svg>`}function ce(b,R,E,{percent:H=!1,alert:he=!1}={}){if(!b.length)return'<div class="obs-empty">\u017D\xE1dn\xE1 m\u011B\u0159en\xE1 data.</div>';let te=Math.max(...b.map(R),H?100:1);return`<div class="obs-bars">${b.map(me=>{let fe=R(me),ae=te?Math.max(1,fe/te*100):0;return`<div class="obs-bar" data-alert="${he?String(he(me)):"false"}"><label title="${ve(me.model||me.label)}">${ve(me.model||me.label)}</label><div class="obs-bar-track"><i class="obs-bar-fill" style="--bar:${ae.toFixed(1)}%"></i></div><strong>${ve(E(fe,me))}</strong></div>`}).join("")}</div>`}function pe(){if(s)return r;if(!n)return"offline";let b=k(),R=Qe();if(b){let he=ee(),te=he.filter(We=>["blocked","failed"].includes(We.status)),me=R.filter(We=>We.profile==="majak"),fe=W("majak"),ae=v("majak","herdr"),Ye=n.sources.some(We=>We.profile==="majak");if(te.some(We=>Xe.has(We.blocker))||me.some(We=>We.status==="blocked")||K("quantlab").length||K("majak").length)return"waiting_user";if(Ye&&(!ae||ae.status!=="available"))return he.length||R.length?"error":"offline";if(ie().length||he.some(We=>We.status==="running")||me.some(We=>We.status==="working")||fe.some(We=>We.status==="running"))return"working";if(te.length||re("majak").length)return"waiting_result";let qe=fe.some(We=>We.status!=="done");return he.length&&he.every(We=>We.raw_state==="done")&&!qe?"complete":(me.some(We=>We.status==="idle"),"idle")}let E=R.filter(he=>Kr(he.agent)==="hermes"),H=W();return R.some(he=>he.status==="blocked")||K().length?"waiting_user":n.sources.some(he=>he.kind==="herdr"&&he.status!=="available")?R.length?"error":"offline":E.some(he=>he.status==="working")||H.some(he=>he.status==="running")?"working":re().length?"waiting_result":E.some(he=>he.status==="idle")?"idle":E.length&&E.every(he=>he.status==="done")?"complete":"offline"}function ye(){return Vh.has(o)?o:"majak-codex"}function we(b){if(s)return`DEMO \xB7 ${Gs[b].copy}`;let R=k(),E=Qe(),H=R?[...ie().map(te=>te.agent_id).filter(Boolean),...E.filter(te=>te.profile==="majak"&&te.status==="working").map(te=>te.agent)]:E.filter(te=>te.status==="working").map(te=>te.agent),he=R?ee().find(te=>te.status==="running")||W("majak").find(te=>te.status==="running")||null:Se();if(b==="working"&&he)return`${he.repo==="Bbambaaamm/dotacni-majak"?"Maj\xE1k":he.repo==="Bbambaaamm/herdr"?"Herdr":"QuantLab"} ${nn(he)} \xB7 ${he.task_id} \xB7 ${on[he.status]}.`;if(b==="working"||b==="idle"&&H.length)return`Pracuj\xED: ${H.join(", ")}. P\u0159esn\xFD \xFAkol zdroj neposkytuje.`;if(b==="waiting_user"){let te=Qe().filter(ae=>ae.status==="blocked"&&(!R||ae.profile==="majak")).map(ae=>ae.agent),me=R?[...ee(),...K()]:K(),fe=[...new Map(me.map(ae=>[ae.task_id,ae])).values()].filter(ae=>["blocked","failed"].includes(ae.status)&&Xe.has(ae.blocker)).map(ae=>`${nn(ae)} ${ae.task_id}`);return`Zkontrolujte: ${[...te,...fe].join(", ")||"blokovanou \xFAlohu"}.`}return b==="waiting_result"?`\u010Cekaj\xED technick\xE9 z\xE1vislosti: ${(R?ee():re()).filter(me=>["blocked","failed"].includes(me.status)&&!Xe.has(me.blocker)).map(me=>`${nn(me)} ${me.blocker||me.task_id}`).join(", ")||"intern\xED kontrola"}.`:b==="offline"?p:b==="error"?n.sources.filter(te=>te.status==="unavailable"&&te.reason!=="not_configured").map(te=>`${te.profile}/${te.kind}: ${te.reason}`).join(" \xB7 ")||"\u017Div\xFD stav jednoho projektu nen\xED dostupn\xFD.":Gs[b].copy}function ke(){let b=pe(),R=Gs[b],E=e_(R.tone),H=Se(),he=Le(H?.agent||null);t.faceState.textContent=R.label,t.faceTask.textContent=we(b),t.coordinatorCurrent.textContent=s?`DEMO \xB7 ${Gs[b].label}`:Ie(H),t.coordinatorNext.textContent=s?`DEMO \xB7 ${ye()}`:Ie(he),t.coordinatorCurrent.title=t.coordinatorCurrent.textContent,t.coordinatorNext.title=t.coordinatorNext.textContent,t.faceSignal.style.background=E,t.faceSignal.style.color=E,t.faceSignal.style.boxShadow=h?"none":`0 0 13px ${E}`,b!==d&&(C("setState",b),d=b);let te=k(),me=te?[...ee(),...W("majak")]:W(),fe=Qe().filter(qe=>qe.status==="working"),ae=fe.filter(qe=>qe.profile==="majak"),Ye=te?ie():null;C("setActivity",{running:me.filter(qe=>qe.status==="running").length,pending:me.filter(qe=>qe.status==="pending").length,blocked:me.filter(qe=>["blocked","failed"].includes(qe.status)).length,userBlocked:K().length,workingAgents:Ye?Ye.length+ae.length:fe.length,activeAgent:Ye?Ye[0]?.agent_id||ae[0]?.agent||null:A(H?.agent)||fe[0]?.agent||null});let je=ye(),xe=`${s}:${r}:${je}`;xe!==g&&(C("setDemo",{enabled:s,state:r,target:je}),g=xe),t.attention.hidden=s||!["waiting_user","error","offline"].includes(b),t.attention.textContent=b==="offline"?"Obnovit data":b==="waiting_user"?"Otev\u0159\xEDt blokovan\xE9ho agenta":"Zkontrolovat zdroje"}function O(b){let R=Kr(b.agent),E=s?"Uk\xE1zkov\xFD stroj \xB7 syntetick\xFD":b.unavailable?"Stav nen\xED dostupn\xFD":R==="hermes"?"Koordin\xE1tor":"V\xFDvojov\xFD agent",H=s?b.agent===ye()?r:"idle":b.status,he=s?`DEMO \xB7 ${Gs[H].label}`:Uc(H);return`<button class="agent-node" data-agent="${ve(b.agent)}" data-state="${ve(H)}" aria-label="${ve(`${b.agent}: ${he}`)}"><span class="agent-copy"><b>${ve(b.agent)}</b><small>${E}</small></span><span class="state-chip">${ve(he)}</span></button>`}function Te(){let b=[],R=0;for(let E of vn){let H=Qe().filter(xe=>xe.profile===E),he=["hermes","codex"].map(xe=>H.find(qe=>qe.agent===`${E}-${xe}`)||{agent:`${E}-${xe}`,profile:E,status:"offline",unavailable:!0}),te=H.filter(xe=>!Vh.has(xe.agent));R+=te.length;let me=te.length?`<button type="button" class="scene-overflow" data-overflow-profile="${E}">+${te.length} dal\u0161\xEDch agent\u016F \u2014 pracovn\xED p\u0159ehled</button>`:"";e(`#${E}-agents`).innerHTML=he.map(O).join("")+me;let fe=H.length?H:he,ae=S(E),Ye=K(E).length,je=re(E).length;e(`#${E}-project-state`).textContent=fe.some(xe=>xe.status==="blocked")||Ye?"z\xE1sah":fe.some(xe=>xe.status==="working")||ae.some(xe=>xe.status==="running")?"pracuje":je?"\u010Dek\xE1":fe.every(xe=>xe.unavailable)?"bez dat":"klid",b.push(...he.map(xe=>({...xe,id:xe.agent,role:Kr(xe.agent),visible:!e(`#${E}-agents`).hidden})))}t.film.querySelectorAll("[data-agent]").forEach(E=>E.addEventListener("click",()=>mt(E.dataset.agent))),t.film.querySelectorAll("[data-overflow-profile]").forEach(E=>E.addEventListener("click",()=>Li("work"))),e("#data-caveat").textContent=R?`3D sc\xE9na zobrazuje \u010Dty\u0159i zn\xE1m\xE9 stroje. Dal\u0161\xEDch ${R} agent\u016F je v pracovn\xEDm p\u0159ehledu. Nezn\xE1m\xE9 metriky nejsou odhady.`:"Nezn\xE1m\xE9 hodnoty z\u016Fst\xE1vaj\xED nezn\xE1m\xE9.",C("setAgents",b),e("#link-layer").replaceChildren()}function Y(){if(!n){t.snapshotAge.textContent="Nedostupn\xE9",t.agentCount.textContent="Nezn\xE1m\xE9",t.queueCount.textContent="Nedostupn\xE9",t.requestCount.textContent="Nedostupn\xE9",t.searchCount.textContent="Nedostupn\xE9",t.searchLatency.textContent="Nedostupn\xE9",t.costTotal.textContent="Nedostupn\xE9",e("#work-freshness").textContent=p;return}let b=vn.map(gt),R=xe=>b.every(qe=>qe[xe]!=null)?b.reduce((qe,We)=>qe+We[xe],0):null,E=vn.map(Ct),H=xe=>E.every(qe=>qe[xe]!=null)?E.reduce((qe,We)=>qe+We[xe],0):null,he=H("searches"),te=H("duration");t.snapshotAge.textContent=ci(n.generated_at);let me=vn.every(xe=>v(xe,"herdr")?.status==="available");t.agentCount.textContent=me?String(Qe().length):`${Qe().length} ov\u011B\u0159eno \xB7 \u010D\xE1st nedostupn\xE1`;let fe=[...new Set(n.sources.map(xe=>xe.profile))],ae=w(),Ye=fe.length>0&&fe.every(xe=>v(xe,"queue")?.status==="available");t.queueCount.textContent=Ye?String(ot().length):"Nedostupn\xE9",t.requestCount.textContent=Pt(R("requests")),t.searchCount.textContent=Pt(he),t.searchLatency.textContent=Ji(he==null||te==null?null:he===0?0:te/he);let je=Ut().row;t.costTotal.textContent=je?`${100-je.used_percent} %`:"Nedostupn\xE9",t.costTotal.title=je?`Reset ${z(je.resets_at)}`:"Codex usage snapshot nen\xED dostupn\xFD",e("#work-freshness").textContent=`\u017Div\xFD snapshot p\u0159ed ${ci(n.generated_at)}`}function be(){let b=e("#observability-kpis"),R=e("#observability-grid");if(!n){b.innerHTML="",R.innerHTML='<article class="obs-panel full"><div class="obs-empty">\u017Div\xE1 telemetrie nen\xED dostupn\xE1.</div></article>';return}let E=Ut().row,H=E?.routing_status==="available",he=H?[{label:"FREE",value:E.routing_free},{label:"Sol",value:E.routing_sol},{label:"Astra",value:E.routing_astra}]:[],te=vn.map(gt),me=te.every(le=>le.router?.status==="available"),fe=me?te.reduce((le,tt)=>le+tt.requests,0):null,ae=me?te.reduce((le,tt)=>le+tt.costKnown,0):null,Ye=me?te.reduce((le,tt)=>le+tt.costUnknownRequests,0):null,je=B().activeAgents,xe=ot().length,qe=E?100-E.used_percent:null,We=qe==null?"warn":qe<=5?"critical":qe<=25?"warn":"ok",cn=ae==null?"Nedostupn\xE9":Ye?`${Ii(ae)} zn\xE1m\xE9 \xB7 ${kt.format(Ye)} req bez ceny`:Ii(ae);b.innerHTML=[`<article class="obs-kpi" data-severity="${We}"><span>Codex allowance \xB7 zb\xFDv\xE1</span><b>${qe==null?"\u2014":qe+" %"}</b><div class="obs-gauge"><i style="--gauge:${E?E.used_percent:0}%"></i></div><small>${E?E.ordinary_usage_allowed?"B\u011B\u017En\xE9 pou\u017Eit\xED povoleno":"Limit vy\u010Derp\xE1n":"Zdroj nedostupn\xFD"}</small></article>`,`<article class="obs-kpi"><span>Dal\u0161\xED reset Codex</span><b>${E?ve(z(E.resets_at)):"\u2014"}</b><small>${E?ve(ne(E.resets_at)):"\u010Cas resetu nen\xED dostupn\xFD"}</small></article>`,`<article class="obs-kpi"><span>Codex lifetime tokeny</span><b>${E?.lifetime_tokens==null?"\u2014":ve(ji.format(E.lifetime_tokens))}</b><small>Peak/day: ${E?.peak_daily_tokens==null?"\u2014":ve(ji.format(E.peak_daily_tokens))}</small></article>`,`<article class="obs-kpi"><span>Router po\u017Eadavky</span><b>${Pt(fe)}</b><small>${me?`${kt.format(te.reduce((le,tt)=>le+(tt.fallbacks||0),0))} fallback\u016F${H?` \xB7 Astra eskalace ${kt.format(E.routing_astra_escalations)}`:""}`:"\u010D\xE1st router\u016F nedostupn\xE1"}</small></article>`,`<article class="obs-kpi"><span>Variabiln\xED n\xE1klady</span><b>${ae==null?"\u2014":ve(Ii(ae))}</b><small>${ve(cn)}</small></article>`,`<article class="obs-kpi" data-severity="${xe?"warn":"ok"}"><span>Aktivn\xED pr\xE1ce</span><b>${kt.format(je)} agent \xB7 ${kt.format(xe)} fronta</b><small>${xe?"Fronta m\xE1 rozpracovan\xE9/\u010Dekaj\xEDc\xED \xFAlohy":"Durable fronta bez aktivn\xEDch polo\u017Eek"}</small></article>`].join("");let y=Et(),F=y.slice(0,8),J=y.filter(le=>le.requests>0).map(le=>({...le,rate:le.fallbacks/le.requests*100})).sort((le,tt)=>tt.rate-le.rate||tt.requests-le.requests).slice(0,8),X=y.filter(le=>le.durationRequests>0).map(le=>({...le,avg:le.durationMs/le.durationRequests})).sort((le,tt)=>tt.avg-le.avg).slice(0,8),q=y.filter(le=>le.tokenKnownRequests>0).map(le=>({...le,tokens:le.inputTokens+le.outputTokens})).sort((le,tt)=>tt.tokens-le.tokens||tt.requests-le.requests).slice(0,8),Re=te.every(le=>le.requests!=null)?te.reduce((le,tt)=>le+tt.requests,0):0,Ne=(le,tt)=>{let un=te.reduce((Mt,Lt)=>Mt+(Lt[le]??0),0),zn=te.reduce((Mt,Lt)=>Mt+(Lt[tt]??0),0),Kn=un+zn;return Kn?Math.round(un/Kn*100):Re===0?100:0},Ce=[["Input tokeny",Ne("inputKnownRequests","inputUnknownRequests")],["Output tokeny",Ne("outputKnownRequests","outputUnknownRequests")],["USD n\xE1klady",Ne("costKnownRequests","costUnknownRequests")]],Be=S(),ge=Object.fromEntries(Object.keys(on).map(le=>[le,Be.filter(tt=>tt.status===le).length])),Fe=Object.values(ge).reduce((le,tt)=>le+tt,0),at=ue(),He=se(),xt=Ge(),Ft=He.filter(le=>le.event==="allow"),At=[...new Map(xt.slice().reverse().map(le=>[le.reason,le])).values()].slice(0,6),Tt=vn.map(Ct),Xt=["fast","deep","browser"].map(le=>({label:le.toUpperCase(),value:Tt.every(tt=>tt.routes[le]!=null)?Tt.reduce((tt,un)=>tt+un.routes[le],0):0})),Oe=(E?.daily||[]).map(le=>({day:le.day.slice(5),tokens:le.tokens})),$t=E?.limit_history||[];R.innerHTML=[`<article class="obs-panel wide"><header><div><h3>Codex tokeny po dnech</h3><span>45 posledn\xEDch m\u011B\u0159en\xFDch dn\xED</span></div><span>${Oe.length?"peak "+ve(ji.format(Math.max(...Oe.map(le=>le.tokens)))):"bez dat"}</span></header>${_e(Oe,"tokens",{id:"codexTokensArea"})}<p class="obs-note">Account-wide token activity z Codex app-serveru. Nen\xED p\u0159ev\xE1d\u011Bna na API cenu.</p></article>`,`<article class="obs-panel"><header><div><h3>Codex allowance</h3><span>\u010Dasov\xE1 \u0159ada vyu\u017Eit\xED</span></div><span>${E?E.used_percent+" % pou\u017Eito":"nedostupn\xE9"}</span></header>${_e($t,"used_percent",{id:"codexLimitArea",suffix:" %",maxValue:100})}<p class="obs-note">${$t.length<2?"Historii jsme pr\xE1v\u011B za\u010Dali sb\xEDrat; graf se bude plnit automaticky.":"Snapshot ka\u017Ed\xFDch p\u0159ibli\u017En\u011B 5 minut."}${H?` \xB7 Router soft ${kt.format(E.routing_soft_limit_pct)} % / hard ${kt.format(E.routing_hard_limit_pct)} %.`:""}</p></article>`,`<article class="obs-panel"><header><div><h3>Cost-aware router</h3><span>FREE / Sol / Astra \xB7 task decisions</span></div><span>${H?ve(E.routing_policy_version):"nedostupn\xE9"}</span></header>${ce(he,le=>le.value,le=>kt.format(le))}<div class="obs-legend"><span>Astra eskalace: ${H?kt.format(E.routing_astra_escalations):"\u2014"}</span><span>Premium blokov\xE1no: ${H?kt.format(E.routing_premium_denied):"\u2014"}</span></div><p class="obs-note">${H?`Posledn\xED route: ${ve(E.last_route_model||"\u2014")} \xB7 ${ve(E.last_route_reason||"\u2014")}`:"Routing telemetry nen\xED dostupn\xE1."}</p></article>`,`<article class="obs-panel"><header><div><h3>Model traffic</h3><span>po\u010Det skute\u010Dn\xFDch provider request\u016F</span></div><span>top 8</span></header>${ce(F,le=>le.requests,le=>kt.format(le))}</article>`,`<article class="obs-panel"><header><div><h3>Model tokeny</h3><span>skute\u010Dn\u011B zm\u011B\u0159en\xE9 router requesty</span></div><span>top 8</span></header>${ce(q,le=>le.tokens,le=>ji.format(le))}<p class="obs-note">Per-model tokeny jsou autoritativn\xED pro Hermes router. Codex Sol/Astra zde nejsou odhadov\xE1ny; jejich account-wide tokeny z\u016Fst\xE1vaj\xED v samostatn\xE9m grafu.</p></article>`,`<article class="obs-panel"><header><div><h3>Fallback pressure</h3><span>fallbacky / po\u017Eadavky</span></div><span>vy\u0161\u0161\xED = hor\u0161\xED</span></header>${ce(J,le=>le.rate,le=>le.toFixed(1)+" %",{percent:!0,alert:le=>le.rate>=25})}</article>`,`<article class="obs-panel"><header><div><h3>Model latency</h3><span>pr\u016Fm\u011Br na request</span></div><span>jen zn\xE1m\xE1 latence</span></header>${ce(X,le=>le.avg,le=>Ji(le))}</article>`,`<article class="obs-panel"><header><div><h3>Data coverage</h3><span>request-weighted completeness</span></div><span>fail-closed</span></header>${Ce.map(([le,tt])=>`<div class="coverage-row"><span>${ve(le)}</span><div class="coverage-track"><i style="width:${tt}%"></i></div><strong>${tt} %</strong></div>`).join("")}<p class="obs-note">100 % znamen\xE1, \u017Ee ka\u017Ed\xE9mu requestu odpov\xEDd\xE1 m\u011B\u0159en\xE1 hodnota. Chyb\u011Bj\xEDc\xED hodnoty nejsou dopo\u010D\xEDt\xE1ny.</p></article>`,`<article class="obs-panel"><header><div><h3>Durable queue</h3><span>stav pr\xE1ce QuantLab</span></div><span>${Fe} z\xE1znam\u016F</span></header>${Fe?`<div class="queue-strip">${Object.entries(ge).filter(([,le])=>le).map(([le,tt])=>`<i class="${le}" style="width:${(tt/Fe*100).toFixed(1)}%" title="${ve(on[le])}: ${tt}"></i>`).join("")}</div><div class="obs-legend">${Object.entries(ge).map(([le,tt])=>`<span>${ve(on[le])}: ${tt}</span>`).join("")}</div>`:'<div class="obs-empty">Fronta je pr\xE1zdn\xE1.</div>'}</article>`,`<article class="obs-panel"><header><div><h3>Swarm admission</h3><span>ALLOW / DENY p\u0159ed spawnem</span></div><span>${at?.status==="available"?`${Ft.length} / ${xt.length}`:"nedostupn\xE9"}</span></header>${at?.status==="available"?`<div class="obs-legend"><span>ALLOW: ${Ft.length}</span><span>DENY: ${xt.length}</span></div>${At.length?`<div class="admission-reasons">${At.map(le=>`<span><b>${ve(le.reason)}</b> \xB7 ${ve(le.repo)} #${ve(le.issue)} \xB7 ${ve(ci(le.observed_at))}</span>`).join("")}</div>`:'<p class="obs-note">V aktu\xE1ln\xEDm bounded tail nejsou \u017E\xE1dn\xE9 denialy.</p>'}<p class="obs-note">Zobrazeny jsou pouze sanitizovan\xE9 reason codes a DAG scope. Prompt, detail toolu ani secrets se neexportuj\xED.</p>`:'<div class="obs-empty">Admission audit nen\xED v aktu\xE1ln\xEDm snapshotu dostupn\xFD.</div>'}</article>`,`<article class="obs-panel"><header><div><h3>Search route mix</h3><span>Fast / Deep / Browser</span></div><span>aktu\xE1ln\xED snapshot</span></header>${ce(Xt,le=>le.value,le=>kt.format(le))}</article>`,`<article class="obs-panel"><header><div><h3>Codex \xFA\u010Det</h3><span>read-only stav</span></div><span>data p\u0159ed ${Ut().source?ve(ci(Ut().source.observed_at)):"\u2014"}</span></header><div class="obs-legend"><span>Kredity: ${E?ve(E.credits_balance??"nezn\xE1m\xE9"):"\u2014"}</span><span>Reset kredity: ${E?kt.format(E.reset_credits_available):"\u2014"}</span><span>Streak: ${E?.current_streak_days==null?"\u2014":kt.format(E.current_streak_days)+" dn\xED"}</span><span>Max streak: ${E?.longest_streak_days==null?"\u2014":kt.format(E.longest_streak_days)+" dn\xED"}</span></div><p class="obs-note">USD odhad se zobraz\xED jen pokud jej billing route skute\u010Dn\u011B poskytne. Subscription allowance se nep\u0159epo\u010D\xEDt\xE1v\xE1 na API cen\xEDk.</p></article>`].join("")}function Ae(){let b=w(),R=e("#queue-summary"),E=e("#queue-list");if(!b.some(me=>me.status==="available")){R.innerHTML="",E.innerHTML='<p class="queue-empty">Stav durable fronty nen\xED v aktu\xE1ln\xEDm snapshotu dostupn\xFD.</p>';return}let H=S(),he=Object.fromEntries(Object.keys(on).map(me=>[me,H.filter(fe=>fe.status===me).length]));R.innerHTML=Object.entries(on).map(([me,fe])=>`<div class="queue-stat" data-status="${ve(me)}"><span>${ve(fe)}</span><b>${Pt(he[me])}</b></div>`).join("");let te=H.slice(0,12);E.innerHTML=te.length?te.map(me=>{let fe=me.blocker||"\u2014",ae=me.status==="pending"?`od ${ui(me.not_before)}`:`zm\u011Bna ${ui(me.updated_at)}`,Ye=me.issue_title||me.kind;return`<article class="queue-task" data-status="${ve(me.status)}"><div class="queue-task-main"><b>${ve(nn(me))} \xB7 <code>${ve(me.task_id)}</code></b><small>${ve(Ye)} \xB7 ${ve(me.kind)} \xB7 ${ve(me.agent)}</small></div><span class="queue-status">${ve(on[me.status]||me.status)}</span><span class="queue-attempt">Pokus ${ve(Ze(me))}</span><time>${ve(ae)}</time><span class="queue-blocker">${ve(fe)}</span></article>`}).join(""):'<p class="queue-empty">Fronta je pr\xE1zdn\xE1.</p>',H.length>te.length&&E.insertAdjacentHTML("beforeend",`<p class="queue-empty">+${H.length-te.length} dal\u0161\xEDch z\xE1znam\u016F v sanitizovan\xE9m snapshotu.</p>`)}function de(){let b=e("#search-grid");b.innerHTML=vn.map(R=>{let E=Ct(R);if(E.search?.status!=="available")return`<article class="search-card is-unavailable"><header><div><span>${ve(R.toUpperCase())}</span><b>Search telemetry</b></div><span class="search-health">Nedostupn\xE9</span></header><p>Zdroj Search Routeru nen\xED v aktu\xE1ln\xEDm snapshotu dostupn\xFD.</p></article>`;let H=E.searches===0?"\u2014":E.successful==null||E.searches==null?"Nedostupn\xE9":`${Math.round(E.successful/E.searches*100)} %`,he=E.currentProvider||"Zat\xEDm bez provozu",te=E.historicalProviders.join(", ")||"\u2014",me=E.fallbackProviders.join(", ")||"\u2014";return`<article class="search-card"><header><div><span>${ve(R.toUpperCase())}</span><b>Search Router</b></div><span class="search-health">${Pt(E.searches)} hled\xE1n\xED</span></header><div class="search-metrics"><div><span>\xDAsp\u011B\u0161nost</span><b>${ve(H)}</b></div><div><span>Latence avg / max</span><b>${ve(`${Ji(E.avgLatency)} / ${Ji(E.maxLatency)}`)}</b></div><div><span>Fallbacky</span><b>${Pt(E.fallbacks)}</b></div><div><span>N\xE1klady</span><b>${ve(Ii(E.cost))}</b></div></div><div class="search-routes"><span>FAST <b>${Pt(E.routes.fast)}</b></span><span>DEEP <b>${Pt(E.routes.deep)}</b></span><span>BROWSER <b>${Pt(E.routes.browser)}</b></span></div><p><span>Aktu\xE1ln\xED provider (posledn\xED b\u011Bh):</span> ${ve(he)}</p><p><span>Historick\xE9 providery:</span> ${ve(te)}</p><p><span>Pozorovan\xE9 fallback providery:</span> ${ve(me)}</p><p><span>V\xFDsledky / extrakce:</span> ${Pt(E.results)} / ${Pt(E.extracts)} \xB7 data p\u0159ed ${ve(ci(E.search.data_at))}</p></article>`}).join("")}function Ve(){e("#project-grid").innerHTML=vn.map(te=>{let me=Qe().filter(xe=>xe.profile===te),fe=gt(te),ae=fe.inputCoverage==null||fe.outputCoverage==null?null:Math.min(fe.inputCoverage,fe.outputCoverage),Ye=fe.inputKnown==null?"Nedostupn\xE9":`${Pt(fe.inputKnown)} / ${Pt(fe.outputKnown)}${ae<100?` \xB7 ${ae} % req`:""}`,je=fe.costKnown==null?"Nedostupn\xE9":`${Ii(fe.costKnown)} zn\xE1m\xE9${fe.costUnknownRequests?` + ${kt.format(fe.costUnknownRequests)} bez ceny`:""}`;return`<article class="work-project"><h2>${te.toUpperCase()}</h2>${me.length?me.map(xe=>`<button class="work-agent" data-agent="${ve(xe.agent)}"><b>${ve(xe.agent)}</b><span>${Uc(xe.status)}</span><small>${Hh[Kr(xe.agent)]}</small></button>`).join(""):"<p>\u017Div\xFD stav agent\u016F nen\xED dostupn\xFD.</p>"}<p class="work-models">Modely profilu: ${ve(fe.models.join(", ")||"Nedostupn\xE9")}</p><p class="work-models">Aktu\xE1ln\xED provider (posledn\xED b\u011Bh): ${ve(fe.currentProvider||"Nedostupn\xE9")}</p><p class="work-models">Historick\xE9 providery: ${ve(fe.historicalProviders.join(", ")||"\u2014")}</p><div class="work-totals"><div><span>Po\u017Eadavky</span><b>${Pt(fe.requests)}</b></div><div><span>Tokeny vstup/v\xFDstup</span><b>${ve(Ye)}</b></div><div><span>Zn\xE1m\xE9 n\xE1klady / fallbacky</span><b>${ve(je)} \xB7 ${Pt(fe.fallbacks)}</b></div></div></article>`}).join(""),e("#project-grid").querySelectorAll("[data-agent]").forEach(te=>te.addEventListener("click",()=>mt(te.dataset.agent))),be(),Ae(),de(),e("#source-grid").innerHTML=(n?.sources||[]).map(te=>{let me=te.kind==="codex"?"CODEX / \xDA\u010CET":`${te.profile} / ${te.kind}`;return`<article class="source-card" data-status="${ve(te.status)}"><b>${ve(me)}</b><span>${ve(te.status)} \xB7 ${ve(te.reason)}</span><span>${te.status==="available"?`${te.rows.length} z\xE1znam\u016F`:"bez dat"}</span></article>`}).join("");let b=new Set(["user_action_required","auth_required","credentials_missing","permission_required"]),R=(n?.sources||[]).filter(te=>te.status==="unavailable"&&b.has(te.reason)),E=Qe().filter(te=>te.status==="blocked"),H=K(),he=e("#attention-summary");if(he.hidden=!!n&&!R.length&&!E.length&&!H.length,he.textContent=n?`Vy\u017Eaduje v\xE1\u0161 z\xE1sah: ${[...E.map(te=>te.agent),...H.map(te=>`${nn(te)} ${te.task_id}`),...R.map(te=>`${te.profile}/${te.kind} (${te.reason})`)].join(", ")}`:p,!he.hidden){let te=document.createElement("button");te.type="button",te.className="attention-action",te.textContent=E.length?"Otev\u0159\xEDt blokovan\xE9ho agenta":H.length?"Otev\u0159\xEDt frontu":"Obnovit data",te.addEventListener("click",()=>E.length?mt(E[0].agent):H.length?e("#queue-title").scrollIntoView({behavior:h?"auto":"smooth"}):Jn(!0)),he.append(" ",te)}}function ze(){let b=$e(l),R=b?.kind==="herdr_swarm",E=b?.raw_state||(b?on[b.status]||b.status:null),H=b?R?[b.parent_task_id?`parent ${b.parent_task_id}`:"root task",b.dependencies?.length?`depends on ${b.dependencies.join(", ")}`:"no dependencies"].join(" \xB7 "):"Nedostupn\xE9 v telemetry kontraktu \xB7 \u017E\xE1dn\xE1 hrana nebyla odvozena":null,he=b?R?`${b.model||"model nehl\xE1\u0161en"} \xB7 fallback ${b.fallback_model||"\u2014"}`:"Nedostupn\xE9 v telemetry kontraktu":null,te=b?R?`result ${b.result_sha||"\u2014"} \xB7 branch/base nejsou v kontraktu`:"Nedostupn\xE9 v telemetry kontraktu":null;e("#detail-profile").textContent="SWARM TASK",e("#detail-title").textContent=b?`${nn(b)} \xB7 ${b.task_id}`:l||"Task",e("#detail-role").textContent="Durable task node \xB7 read only",e("#detail-status").textContent=b?`Stav: ${E}`:"Task u\u017E nen\xED v aktu\xE1ln\xEDm snapshotu",e("#detail-links").innerHTML=b?[it(ht(b),`Otev\u0159\xEDt Issue ${nn(b)}`),it(st(b),b.pr_number?`Otev\u0159\xEDt PR #${b.pr_number}`:"")].filter(Boolean).join(""):"";let me=b?[["Task ID",b.task_id],["Issue / n\xE1zev",`${nn(b)} \xB7 ${b.issue_title||b.kind}`],["Stav / scheduler",`${E} \xB7 ${R?"authoritative swarm":b.scheduler_state||"nehl\xE1\u0161eno"}`],["Pokus / maximum",Ze(b)],["Agent",b.agent||"\u2014"],["Typ",b.kind],["PR",b.pr_number?`#${b.pr_number}`:"Nen\xED hl\xE1\u0161eno"],["Blocker",b.blocker||"\u2014"],["\u010Cas",b.status==="pending"?`nejd\u0159\xEDve ${ui(b.not_before)}`:`zm\u011Bna ${ui(b.updated_at)}`],["Dependency edges",H],["Model / fallback",he],["Fencing token",R?Pt(b.fencing_token):"Nedostupn\xE9 v telemetry kontraktu"],["Runtime / queue wait","Nedostupn\xE9 v telemetry kontraktu"],["Branch / base / result SHA",te],["Test / reviewer","Nedostupn\xE9 v telemetry kontraktu"]]:[["Stav","Task u\u017E nen\xED v aktu\xE1ln\xEDm snapshotu"]];e("#detail-metrics").innerHTML=me.map(([ae,Ye])=>`<div><dt>${ve(ae)}</dt><dd>${ve(Ye)}</dd></div>`).join("");let fe=b?[`Durable queue: ${nn(b)} \xB7 ${b.task_id} \xB7 ${E}`,`Scheduler: ${R?"authoritative swarm":b.scheduler_state||"nehl\xE1\u0161eno"} \xB7 pokus ${Ze(b)}`,b.blocker?`Blocker: ${b.blocker}`:"Bez hl\xE1\u0161en\xE9ho blockeru",R?`Autoritativn\xED DAG: ${H}.`:"Dependency telemetry nen\xED sou\u010D\xE1st\xED aktu\xE1ln\xEDho snapshotu; DAG hrany nejsou odhadov\xE1ny.","Prompt, intern\xED my\u0161lenky a raw log nejsou v dashboardu zobrazov\xE1ny."]:["Task nen\xED v aktu\xE1ln\xEDm snapshotu."];e("#detail-events").innerHTML=fe.map(ae=>`<li>${ve(ae)}</li>`).join("")}function St(){if(l){ze();return}if(!o)return;let b=Qe().find(J=>J.agent===o),R=b?.profile||(o.startsWith("majak-")?"majak":"quantlab"),E=gt(R),H=Ct(R),he=v(R,"herdr"),te=o.endsWith("-hermes"),me=x(o),fe=te?Se(me)||Le(me):null,ae=te?fe?`${nn(fe)} \xB7 ${fe.task_id} \xB7 ${on[fe.status]||fe.status}`:"\u017D\xE1dn\xE1 \xFAloha v durable queue":"Nedostupn\xE9 v datov\xE9m kontraktu",Ye=fe?.issue_title||"Nedostupn\xE9 v telemetry kontraktu",je=fe?`${on[fe.status]||fe.status} \xB7 scheduler ${fe.scheduler_state||"nehl\xE1\u0161eno"}`:"Nedostupn\xE9 v telemetry kontraktu",xe=fe?`${fe.status==="pending"?"nejd\u0159\xEDve "+ui(fe.not_before):"zm\u011Bna "+ui(fe.updated_at)}`:"Nedostupn\xE9 v telemetry kontraktu",qe=E.inputCoverage==null||E.outputCoverage==null?null:Math.min(E.inputCoverage,E.outputCoverage),We=E.inputKnown==null?"Nedostupn\xE9":`${Pt(E.inputKnown)} / ${Pt(E.outputKnown)}${qe<100?` \xB7 coverage ${qe} % req`:""}`,cn=E.costKnown==null?"Nedostupn\xE9":`${Ii(E.costKnown)} zn\xE1m\xE9${E.costUnknownRequests?` + ${kt.format(E.costUnknownRequests)} req bez ceny`:""}`;e("#detail-profile").textContent=R.toUpperCase(),e("#detail-title").textContent=o,e("#detail-role").textContent=Hh[Kr(o)],e("#detail-status").textContent=`\u017Div\xFD stav: ${b?Uc(b.status):"Odpojeno / nezn\xE1m\xE9"}`,e("#detail-links").innerHTML=[it(ht(fe),fe?`Otev\u0159\xEDt Issue ${nn(fe)}`:""),it(st(fe),fe?.pr_number?`Otev\u0159\xEDt PR #${fe.pr_number}`:"")].filter(Boolean).join("");let y=[["Aktu\xE1ln\xED \xFAkol",ae],["Issue / n\xE1zev",fe?`${nn(fe)} \xB7 ${Ye}`:"Nedostupn\xE9 v telemetry kontraktu"],["Task stav",je],["Pokus / maximum",Ze(fe)],["\u010Cas fronty",xe],["PR",fe?.pr_number?`#${fe.pr_number}`:"Nen\xED hl\xE1\u0161eno"],["Blocker",fe?.blocker||"\u2014"],["Modely profilu",E.models.join(", ")||"Nedostupn\xE9 v aktu\xE1ln\xEDm snapshotu"],["Aktu\xE1ln\xED model provider / fallbacky",`${E.currentProvider||"Nedostupn\xE9"} \xB7 ${Pt(E.fallbacks)}`],["Historick\xE9 model providery",E.historicalProviders.join(", ")||"\u2014"],["Tokeny vstup / v\xFDstup",We],["Zn\xE1m\xE9 n\xE1klady profilu",cn],["Aktu\xE1ln\xED search provider / fallbacky",`${H.currentProvider||"Nedostupn\xE9"} \xB7 ${Pt(H.fallbacks)}`],["Historick\xE9 search providery",H.historicalProviders.join(", ")||"\u2014"],["Search / avg latence",`${Pt(H.searches)} \xB7 ${Ji(H.avgLatency)}`],["Runtime / queue wait","Nedostupn\xE9 v telemetry kontraktu"],["Branch / base / result SHA","Nedostupn\xE9 v telemetry kontraktu"],["Test / reviewer","Nedostupn\xE9 v telemetry kontraktu"]];e("#detail-metrics").innerHTML=y.map(([J,X])=>`<div><dt>${ve(J)}</dt><dd>${ve(X)}</dd></div>`).join("");let F=[];b&&F.push(`Herdr hl\xE1s\xED stav \u201E${b.status}\u201C \xB7 pozorov\xE1no p\u0159ed ${ci(he?.observed_at)}`),fe&&F.push(`Durable queue: ${nn(fe)} \xB7 ${fe.task_id} \xB7 ${on[fe.status]||fe.status} \xB7 pokus ${Ze(fe)} \xB7 scheduler ${fe.scheduler_state||"nehl\xE1\u0161eno"}`),fe?.blocker&&F.push(`Blocker: ${fe.blocker}`),E.router?.status==="available"&&F.push(`Router profilu: ${Pt(E.requests)} po\u017Eadavk\u016F \xB7 data p\u0159ed ${ci(E.router.data_at)}`),H.search?.status==="available"&&F.push(`Search Router: ${Pt(H.searches)} hled\xE1n\xED \xB7 ${Ji(H.avgLatency)} pr\u016Fm\u011Br \xB7 ${Pt(H.fallbacks)} fallback\u016F \xB7 data p\u0159ed ${ci(H.search.data_at)}`),F.push("Runtime, branch/SHA, test a reviewer data se nezobrazuj\xED, dokud je autoritativn\xED telemetry kontrakt neposkytuje."),F.push("Zdroj neposkytuje prompt, historii n\xE1stroj\u016F, intern\xED my\u0161lenky ani surov\xE9 provozn\xED z\xE1znamy \xFAlohy."),s&&F.unshift("DEMO: pohyb 3D sc\xE9ny je syntetick\xFD. Tento detail st\xE1le zobrazuje skute\u010Dn\xFD snapshot."),e("#detail-events").innerHTML=F.map(J=>`<li>${ve(J)}</li>`).join("")}function mt(b){vn.flatMap(rt).some(R=>R.agent===b)&&(M=document.activeElement,l=null,o=b,St(),t.detail.hidden=!1,t.backdrop.hidden=!1,document.body.style.overflow="hidden",e("#detail-close").focus(),C("focusTask",null),C("focusAgent",b),s&&Te(),Me(),ke())}function ln(b){$e(b)&&(M=document.activeElement,o=null,l=b,ze(),t.detail.hidden=!1,t.backdrop.hidden=!1,document.body.style.overflow="hidden",e("#detail-close").focus(),C("focusAgent",null),C("focusTask",b),Me(),ke())}function pn(){t.detail.hidden=!0,t.backdrop.hidden=!0,document.body.style.overflow="",C("focusAgent",null),C("focusTask",l||null),M?.isConnected?M.focus():l?document.querySelector(`[data-task-id="${CSS.escape(l)}"]`)?.focus():document.querySelector(`[data-agent="${CSS.escape(o||"")}"]`)?.focus()}function Li(b){a=b,t.film.hidden=b!=="film",t.work.hidden=b!=="work",document.querySelectorAll("[data-view]").forEach(R=>{let E=R.dataset.view===b;R.classList.toggle("is-active",E),R.setAttribute("aria-pressed",String(E))}),C("setActive",b==="film"&&!document.hidden),u&&(t.fallback.hidden=!1)}function Ws(){document.documentElement.dataset.motion=h?"reduced":"full";let b=e("#motion-toggle");b.setAttribute("aria-pressed",String(h)),b.textContent=h?"Povolit pohyb":"Omezit pohyb",C("setReduced",h),ke()}function Ki(){let b=Pe(),R=b?` \xB7 ${b.tag} @ ${b.commit.slice(0,12)}`:"";t.header.textContent=s?"DEMO \xB7 sc\xE9na syntetick\xE1, metriky skute\u010Dn\xE9":n?`\u017Div\xE1 data \xB7 ${ci(n.generated_at)}${R}`:p;let E=s?"#e49a34":n?"#6adf9a":"#ff7159";t.liveDot.style.background=E,t.liveDot.style.color=E}function Ni(){Ki(),Te(),Y(),L(),Ve(),ke(),t.detail.hidden||St()}function fl(b){if(!b||!Number.isFinite(b.generated_at)||!Array.isArray(b.sources))throw new Error("invalid");if(Date.now()/1e3-b.generated_at>90||b.generated_at>Date.now()/1e3+5)throw new Error("stale");for(let R of b.sources){if(!R||!vn.includes(R.profile)||typeof R.kind!="string"||!Array.isArray(R.rows))throw new Error("invalid");if(R.kind==="herdr"&&R.rows.some(E=>typeof E.agent!="string"||typeof E.status!="string"))throw new Error("invalid");if(["router","search"].includes(R.kind)&&R.rows.some(E=>typeof E.provider!="string"||!Number.isFinite(E.last_used_at)))throw new Error("invalid");if(R.kind==="queue"){let E=R.profile==="majak"?{repo:"Bbambaaamm/dotacni-majak",agent:"dotacni-majak-hermes"}:{repo:"Bbambaaamm/Autonomous-Quant-Lab",agent:"quantlab-hermes"};if(R.rows.some(H=>typeof H.task_id!="string"||H.repo!=null&&typeof H.repo!="string"||R.profile==="majak"&&H.repo!==E.repo||R.profile==="quantlab"&&H.repo!=null&&H.repo!==E.repo||H.issue!=null&&(!Number.isSafeInteger(H.issue)||H.issue<0)||H.issue_title!=null&&(typeof H.issue_title!="string"||H.issue_title.length>160)||typeof H.issue_open!="boolean"||H.scheduler_state!=null&&typeof H.scheduler_state!="string"||H.agent!==E.agent||typeof H.kind!="string"||!Object.hasOwn(on,H.status)||!Number.isSafeInteger(H.attempts)||H.attempts<0||!Number.isSafeInteger(H.max_attempts)||H.max_attempts<0||H.not_before!=null&&!Number.isFinite(H.not_before)||!Number.isFinite(H.updated_at)||H.blocker!=null&&typeof H.blocker!="string"||H.pr_number!=null&&(!Number.isSafeInteger(H.pr_number)||H.pr_number<1)))throw new Error("invalid")}if(R.kind==="admission"){if(R.profile!=="quantlab")throw new Error("invalid");if(R.rows.some(E=>!["allow","deny"].includes(E.event)||E.reason!=null&&typeof E.reason!="string"||typeof E.role!="string"||typeof E.repo!="string"||typeof E.issue!="string"||!Number.isSafeInteger(E.node_count)||E.node_count<0||!Number.isSafeInteger(E.max_depth)||E.max_depth<0||!Number.isSafeInteger(E.max_fanout)||E.max_fanout<0||!Number.isSafeInteger(E.child_tools_count)||E.child_tools_count<0||E.agents_after!=null&&(!Number.isSafeInteger(E.agents_after)||E.agents_after<0)||!Number.isFinite(E.observed_at)||E.event==="deny"&&(E.reason==null||E.agents_after!=null)||E.event==="allow"&&(E.reason!=null||E.agents_after==null)))throw new Error("invalid")}if(R.kind==="swarm"){if(R.profile!=="quantlab"||R.status==="available"&&R.rows.length!==1)throw new Error("invalid");for(let E of R.rows){if(E.version!==1||typeof E.repo!="string"||typeof E.issue!="string"||E.issue_state!=null&&!["open","closed","unknown"].includes(E.issue_state)||typeof E.paper_only!="boolean"||!Array.isArray(E.policy_profiles)||!Array.isArray(E.agents)||!Array.isArray(E.tasks)||!Array.isArray(E.edges)||E.repo==="Bbambaaamm/Autonomous-Quant-Lab"&&E.paper_only!==!0)throw new Error("invalid");let H=new Set;for(let ae of E.tasks){if(!ae||typeof ae.task_id!="string"||H.has(ae.task_id)||!Object.hasOwn(Wh,ae.state)||typeof ae.role!="string"||!Number.isSafeInteger(ae.attempt)||ae.attempt<0||!Number.isSafeInteger(ae.max_attempts)||ae.max_attempts<ae.attempt||!Number.isSafeInteger(ae.fencing_token)||ae.fencing_token<0||!Array.isArray(ae.dependencies)||ae.dependencies.some(Ye=>typeof Ye!="string")||ae.parent_task_id!=null&&typeof ae.parent_task_id!="string"||ae.parent_agent_id!=null&&typeof ae.parent_agent_id!="string"||ae.agent_id!=null&&typeof ae.agent_id!="string"||ae.result_sha!=null&&(typeof ae.result_sha!="string"||!/^[0-9a-f]{64}$/.test(ae.result_sha)))throw new Error("invalid");H.add(ae.task_id)}let he=new Map(E.tasks.map(ae=>[ae.task_id,ae])),te=new Set,me=new Set;for(let ae of E.agents){if(!ae||typeof ae.agent_id!="string"||te.has(ae.agent_id)||typeof ae.task_id!="string"||me.has(ae.task_id)||ae.state!=="running"||ae.parent_task_id!=null&&typeof ae.parent_task_id!="string"||ae.parent_agent_id!=null&&typeof ae.parent_agent_id!="string"||!Number.isSafeInteger(ae.fencing_token)||ae.fencing_token<0)throw new Error("invalid");let Ye=he.get(ae.task_id);if(!Ye||Ye.state!=="running"||Ye.agent_id!==ae.agent_id||Ye.parent_task_id!==ae.parent_task_id||Ye.parent_agent_id!==ae.parent_agent_id||Ye.fencing_token!==ae.fencing_token)throw new Error("invalid");te.add(ae.agent_id),me.add(ae.task_id)}let fe=new Set(E.tasks.filter(ae=>ae.state==="running"&&ae.agent_id!=null).map(ae=>ae.task_id));if(fe.size!==me.size||[...fe].some(ae=>!me.has(ae)))throw new Error("invalid");for(let ae of E.edges)if(!ae||!["parent","dependency"].includes(ae.kind)||typeof ae.from_task!="string"||typeof ae.to_task!="string"||!H.has(ae.from_task)||!H.has(ae.to_task))throw new Error("invalid")}}if(R.kind==="release"){if(R.profile!=="quantlab"||R.status==="available"&&R.rows.length!==1)throw new Error("invalid");if(R.rows.some(E=>typeof E.tag!="string"||!/^v[A-Za-z0-9._-]{1,62}$/.test(E.tag)||typeof E.commit!="string"||!/^[0-9a-f]{40}$/.test(E.commit)||typeof E.config_sha256!="string"||!/^[0-9a-f]{64}$/.test(E.config_sha256)||!Number.isSafeInteger(E.deployed_at)||E.deployed_at<0))throw new Error("invalid")}if(R.kind==="codex"){if(R.profile!=="majak"||R.status==="available"&&R.rows.length!==1)throw new Error("invalid");if(R.rows.some(E=>!Number.isFinite(E.used_percent)||E.used_percent<0||E.used_percent>100||!Array.isArray(E.daily)||!Array.isArray(E.limit_history)||!["available","unavailable"].includes(E.routing_status)))throw new Error("invalid");for(let E of R.rows){if(E.routing_status!=="available")continue;let H=["routing_observed_at","routing_soft_limit_pct","routing_hard_limit_pct","routing_decisions","routing_free","routing_sol","routing_astra","routing_astra_escalations","routing_premium_denied"];if(typeof E.routing_policy_version!="string"||E.routing_policy_version.length>64||H.some(he=>!Number.isSafeInteger(E[he])||E[he]<0)||E.routing_soft_limit_pct>=E.routing_hard_limit_pct||E.routing_hard_limit_pct>100||E.routing_free+E.routing_sol+E.routing_astra>E.routing_decisions||E.routing_astra_escalations>E.routing_astra||E.last_route_at!=null&&!Number.isFinite(E.last_route_at)||E.last_route_tier!=null&&!["free","sol","astra"].includes(E.last_route_tier)||E.last_route_model!=null&&typeof E.last_route_model!="string"||E.last_route_reason!=null&&typeof E.last_route_reason!="string")throw new Error("invalid")}}}return b}async function Jn(b=!1){if(m||!b&&document.hidden)return;m=!0;let R=new AbortController,E=setTimeout(()=>R.abort(),1e4);try{let H=await fetch("/agent-platform/api/v1/overview",{cache:"no-store",headers:{Accept:"application/json"},signal:R.signal});if(!H.ok)throw new Error(`HTTP ${H.status}`);n=fl(await H.json()),p="\u010Cerstv\xFD \u017Eiv\xFD stav nen\xED dostupn\xFD",e("#server-fallback-details").removeAttribute("open")}catch(H){n=null,p=H.message==="stale"?"Snapshot je star\u0161\xED ne\u017E 90 s \xB7 obnovte data":"\u017Div\xE1 data nejsou dostupn\xE1 \xB7 ov\u011B\u0159te p\u0159ipojen\xED nebo p\u0159ihl\xE1\u0161en\xED"}finally{clearTimeout(E),m=!1,Ni()}}for(let[b,R]of Object.entries(Gs)){let E=document.createElement("button");E.type="button",E.dataset.demoState=b,E.textContent=R.label,E.addEventListener("click",()=>{r=b,t.demoStates.querySelectorAll("button").forEach(H=>{let he=H.dataset.demoState===b;H.classList.toggle("is-active",he),H.setAttribute("aria-pressed",String(he))}),Te(),ke()}),t.demoStates.append(E)}return document.querySelectorAll("[data-view]").forEach(b=>b.addEventListener("click",()=>Li(b.dataset.view))),document.querySelectorAll("[data-task-filter]").forEach(b=>b.addEventListener("click",()=>{c=b.dataset.taskFilter||"all",Me()})),e("#demo-toggle").addEventListener("click",b=>{s=!s,document.documentElement.dataset.mode=s?"demo":"live",b.currentTarget.setAttribute("aria-pressed",String(s)),b.currentTarget.textContent=s?"Ukon\u010Dit demo":"Demo re\u017Eim",t.demo.hidden=!s,s&&(r="idle",t.demoStates.querySelectorAll("button").forEach(R=>{let E=R.dataset.demoState==="idle";R.classList.toggle("is-active",E),R.setAttribute("aria-pressed",String(E))})),Ki(),Te(),ke(),t.detail.hidden||St(),s||Jn(!0)}),e("#demo-panel > div:first-child > span").textContent="Pouze animace jsou syntetick\xE9. Metriky a detaily z\u016Fst\xE1vaj\xED skute\u010Dn\xE9.",e("#motion-toggle").addEventListener("click",()=>{h=!h,Ws()}),matchMedia("(prefers-reduced-motion: reduce)").addEventListener("change",b=>{h=b.matches,Ws()}),e("#detail-close").addEventListener("click",pn),t.backdrop.addEventListener("click",pn),t.detail.setAttribute("role","dialog"),t.detail.setAttribute("aria-modal","true"),document.addEventListener("keydown",b=>{if(!t.detail.hidden&&(b.key==="Escape"&&pn(),b.key==="Tab")){let R=[...t.detail.querySelectorAll('button:not([disabled]),a[href],[tabindex="0"]')],E=R[0],H=R[R.length-1];b.shiftKey&&document.activeElement===E?(b.preventDefault(),H?.focus()):!b.shiftKey&&document.activeElement===H&&(b.preventDefault(),E?.focus())}}),t.attention.addEventListener("click",()=>{if(!n){Jn(!0);return}let b=Qe().find(R=>R.status==="blocked");b?mt(b.agent):Li("work")}),document.querySelectorAll("[data-project-toggle]").forEach(b=>b.addEventListener("click",()=>{let R=b.closest(".project").querySelector(".agent-list"),E=b.getAttribute("aria-expanded")==="true";b.setAttribute("aria-expanded",String(!E)),R.hidden=E,Te()})),document.addEventListener("visibilitychange",()=>{C("setActive",!document.hidden&&a==="film"),document.hidden||Jn(!0)}),C("onSelect",mt),C("onTaskSelect",ln),Ws(),Li(u?"work":"film"),Ni(),Jn(!0),setInterval(Jn,3e4),setInterval(()=>{document.hidden||(n&&Date.now()/1e3-n.generated_at>90?(n=null,p="Snapshot je star\u0161\xED ne\u017E 90 s \xB7 obnovte data",Ni()):(Y(),Ki(),t.detail.hidden||St()))},1e3),Object.freeze({diagnostics:()=>({view:a,mode:s?"demo":"live",state:pe(),reduced:h,selectedAgent:o,selectedTask:l,sceneAvailable:!!f&&!u,freshSnapshot:!!n,agentCount:Qe().length,queueActive:ot().length})})}$h(zh);document.documentElement.dataset.preview==="true"&&document.querySelector("#demo-toggle").click();})();
/*! Bundled license information:

three/build/three.core.js:
three/build/three.module.js:
  (**
   * @license
   * Copyright 2010-2026 Three.js Authors
   * SPDX-License-Identifier: MIT
   *)
*/
