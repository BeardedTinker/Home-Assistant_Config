import{d as e,bq as a,aG as t,br as s,bs as i,bi as n,bt as o,bu as r,bv as d,bw as c,bx as l,bk as u,by as h,bz as m,bA as p,bB as v,bC as f,bD as b,bE as y,bF as _,bG as g,bH as k,bI as w,bJ as x,bK as $,bL as C,aK as I,bM as j,bN as B,bO as z,aT as S,bP as U,a9 as E,bQ as O,bR as q,aQ as A,bS as D,bT as F,bU as N,bV as L,ba as M,bW as T,bX as V,bY as G,bZ as J,b_ as K,b$ as P,c0 as Q,c1 as H,c2 as R,c3 as W,c4 as X,c5 as Y,c6 as Z,c7 as ee,c8 as ae,c9 as te,ca as se,cb as ie,cc as ne,cd as oe,ce as re,N as de,cf as ce,cg as le,ch as ue,ci as he,cj as me,ck as pe,cl as ve,cm as fe,cn as be,b7 as ye,co as _e,cp as ge,cq as ke,cr as we,cs as xe,ct as $e,cu as Ce,cv as Ie,cw as je,cx as Be,cy as ze,cz as Se,cA as Ue,cB as Ee,cC as Oe,cD as qe,cE as Ae,cF as De,cG as Fe,cH as Ne,cI as Le,cJ as Me,aS as Te,cK as Ve,cL as Ge,cM as Je,cN as Ke,cO as Pe,cP as Qe,cQ as He,cR as Re,cS as We,cT as Xe,cU as Ye,cV as Ze,cW as ea,cX as aa,cY as ta,cZ as sa,c_ as ia,c$ as na,d0 as oa,d1 as ra,d2 as da,d3 as ca,d4 as la,d5 as ua,d6 as ha,d7 as ma,d8 as pa,d9 as va,da as fa,db as ba,dc as ya,dd as _a,de as ga,df as ka,dg as wa,dh as xa,di as $a,dj as Ca,dk as Ia,dl as ja,dm as Ba,dn as za,dp as Sa,dq as Ua,dr as Ea,ds as Oa,dt as qa,du as Aa,dv as Da,dw as Fa,dx as Na,dy as La,dz as Ma,dA as Ta,dB as Va,dC as Ga,dD as Ja,dE as Ka,dF as Pa,dG as Qa,dH as Ha,dI as Ra,dJ as Wa,dK as Xa,dL as Ya,dM as Za,dN as et,dO as at,dP as tt,bl as st,dQ as it,dR as nt,dS as ot,dT as rt,dU as dt,dV as ct,dW as lt,dX as ut,dY as ht,dZ as mt,d_ as pt,d$ as vt,e0 as ft,e1 as bt,e2 as yt,e3 as _t,e4 as gt,e5 as kt,e6 as wt,e7 as xt,e8 as $t,e9 as Ct,ea as It,eb as jt,ec as Bt,_ as zt,j as St,e as Ut,y as Et,n as Ot,t as qt,C as At,p as Dt,E as Ft,G as Nt,i as Lt,a7 as Mt,J as Tt}from"./main-22e4648c.js";import"./c.fa63af8a.js";import{c as Vt}from"./c.d2f13ac1.js";import{c as Gt}from"./c.6eb9fcd4.js";import{c as Jt}from"./c.874c8cfd.js";import"./c.35d79203.js";import{U as Kt,u as Pt}from"./c.811f664e.js";import{c as Qt}from"./c.fa0ef026.js";import"./c.2610e8cd.js";const Ht=e`
  ha-state-icon[data-domain="alert"][data-state="on"],
  ha-state-icon[data-domain="automation"][data-state="on"],
  ha-state-icon[data-domain="binary_sensor"][data-state="on"],
  ha-state-icon[data-domain="calendar"][data-state="on"],
  ha-state-icon[data-domain="camera"][data-state="streaming"],
  ha-state-icon[data-domain="cover"][data-state="open"],
  ha-state-icon[data-domain="device_tracker"][data-state="home"],
  ha-state-icon[data-domain="fan"][data-state="on"],
  ha-state-icon[data-domain="humidifier"][data-state="on"],
  ha-state-icon[data-domain="light"][data-state="on"],
  ha-state-icon[data-domain="input_boolean"][data-state="on"],
  ha-state-icon[data-domain="lock"][data-state="unlocked"],
  ha-state-icon[data-domain="media_player"][data-state="on"],
  ha-state-icon[data-domain="media_player"][data-state="paused"],
  ha-state-icon[data-domain="media_player"][data-state="playing"],
  ha-state-icon[data-domain="remote"][data-state="on"],
  ha-state-icon[data-domain="script"][data-state="on"],
  ha-state-icon[data-domain="sun"][data-state="above_horizon"],
  ha-state-icon[data-domain="switch"][data-state="on"],
  ha-state-icon[data-domain="timer"][data-state="active"],
  ha-state-icon[data-domain="vacuum"][data-state="cleaning"],
  ha-state-icon[data-domain="group"][data-state="on"],
  ha-state-icon[data-domain="group"][data-state="home"],
  ha-state-icon[data-domain="group"][data-state="open"],
  ha-state-icon[data-domain="group"][data-state="locked"],
  ha-state-icon[data-domain="group"][data-state="problem"] {
    color: var(--paper-item-icon-active-color, #fdd835);
  }

  ha-state-icon[data-domain="climate"][data-state="cooling"] {
    color: var(--cool-color, var(--state-climate-cool-color));
  }

  ha-state-icon[data-domain="climate"][data-state="heating"] {
    color: var(--heat-color, var(--state-climate-heat-color));
  }

  ha-state-icon[data-domain="climate"][data-state="drying"] {
    color: var(--dry-color, var(--state-climate-dry-color));
  }

  ha-state-icon[data-domain="alarm_control_panel"] {
    color: var(--alarm-color-armed, var(--label-badge-red));
  }
  ha-state-icon[data-domain="alarm_control_panel"][data-state="disarmed"] {
    color: var(--alarm-color-disarmed, var(--label-badge-green));
  }
  ha-state-icon[data-domain="alarm_control_panel"][data-state="pending"],
  ha-state-icon[data-domain="alarm_control_panel"][data-state="arming"] {
    color: var(--alarm-color-pending, var(--label-badge-yellow));
    animation: pulse 1s infinite;
  }
  ha-state-icon[data-domain="alarm_control_panel"][data-state="triggered"] {
    color: var(--alarm-color-triggered, var(--label-badge-red));
    animation: pulse 1s infinite;
  }

  @keyframes pulse {
    0% {
      opacity: 1;
    }
    50% {
      opacity: 0;
    }
    100% {
      opacity: 1;
    }
  }

  ha-state-icon[data-domain="plant"][data-state="problem"] {
    color: var(--state-icon-error-color);
  }

  /* Color the icon if unavailable */
  ha-state-icon[data-state="unavailable"] {
    color: var(--state-unavailable-color);
  }
`,Rt=a,Wt={alert:t,air_quality:s,automation:i,calendar:n,camera:o,climate:r,configurator:d,conversation:c,counter:l,demo:u,fan:h,google_assistant:m,group:p,homeassistant:u,homekit:v,image_processing:f,input_button:b,input_datetime:y,input_number:_,input_select:g,input_text:k,light:w,mailbox:x,notify:$,number:_,persistent_notification:C,person:I,plant:j,proximity:B,remote:z,scene:S,schedule:y,script:U,select:g,sensor:E,siren:O,simple_alarm:C,sun:q,timer:A,updater:D,vacuum:F,water_heater:N,weather:L,zone:M},Xt={apparent_power:T,aqi:s,carbon_dioxide:V,carbon_monoxide:G,current:J,date:n,distance:K,duration:P,energy:Q,frequency:H,gas:R,humidity:W,illuminance:X,moisture:W,monetary:Y,nitrogen_dioxide:Z,nitrogen_monoxide:Z,nitrous_oxide:Z,ozone:Z,pm1:Z,pm10:Z,pm25:Z,power:T,power_factor:ee,pressure:ae,reactive_power:T,signal_strength:te,speed:se,sulphur_dioxide:Z,temperature:N,timestamp:ie,volatile_organic_compounds:Z,voltage:H,weight:ne},Yt={"clear-night":re,cloudy:L,exceptional:de,fog:ce,hail:le,lightning:ue,"lightning-rainy":he,partlycloudy:me,pouring:pe,rainy:ve,snowy:fe,"snowy-rainy":be,sunny:ye,windy:_e,"windy-variant":ge};e`
  .rain {
    fill: var(--weather-icon-rain-color, #30b3ff);
  }
  .sun {
    fill: var(--weather-icon-sun-color, #fdd93c);
  }
  .moon {
    fill: var(--weather-icon-moon-color, #fcf497);
  }
  .cloud-back {
    fill: var(--weather-icon-cloud-back-color, #d4d4d4);
  }
  .cloud-front {
    fill: var(--weather-icon-cloud-front-color, #f9f9f9);
  }
`;const Zt={10:Fa,20:Na,30:La,40:Ma,50:Ta,60:Va,70:Ga,80:Ja,90:Ka,100:va},es={10:Pa,20:Qa,30:Ha,40:Ra,50:Wa,60:Xa,70:Ya,80:Za,90:et,100:fa},as=(e,a)=>{const t=Number(e);if(isNaN(t))return"off"===e?va:"on"===e?Oa:qa;const s=10*Math.round(t/10);return a&&t>=10?es[s]:a?Aa:t<=5?Da:Zt[s]},ts=e=>{const a=null==e?void 0:e.attributes.device_class;if(a&&a in Xt)return Xt[a];if("battery"===a)return e?((e,a)=>{const t=e.state,s=a&&"on"===a.state;return as(t,s)})(e):va;const t=null==e?void 0:e.attributes.unit_of_measurement;return"°C"===t||"°F"===t?N:void 0},ss=(e,a,t)=>{const s=void 0!==t?t:null==a?void 0:a.state;switch(e){case"alarm_control_panel":return(e=>{switch(e){case"armed_away":return ze;case"armed_vacation":return Be;case"armed_home":return je;case"armed_night":return Ie;case"armed_custom_bypass":return Ce;case"pending":return $e;case"triggered":return xe;case"disarmed":return we;default:return ke}})(s);case"binary_sensor":return((e,a)=>{const t="off"===e;switch(null==a?void 0:a.attributes.device_class){case"battery":return t?va:ba;case"battery_charging":return t?va:fa;case"carbon_monoxide":return t?ma:pa;case"cold":return t?N:ha;case"connectivity":return t?la:ua;case"door":return t?da:ca;case"garage_door":return t?oa:ra;case"power":case"plug":return t?Je:Ke;case"gas":case"problem":case"safety":case"tamper":return t?ia:na;case"smoke":return t?ta:sa;case"heat":return t?N:aa;case"light":return t?X:ea;case"lock":return t?Ye:Ze;case"moisture":return t?We:Xe;case"motion":return t?He:Re;case"occupancy":case"presence":return t?Ve:Ge;case"opening":return t?Pe:Qe;case"running":return t?Me:Te;case"sound":return t?Ne:Le;case"update":return t?De:Fe;case"vibration":return t?qe:Ae;case"window":return t?Ee:Oe;default:return t?Se:Ue}})(s,a);case"button":switch(null==a?void 0:a.attributes.device_class){case"restart":return Bt;case"update":return Fe;default:return b}case"cover":return((e,a)=>{const t="closed"!==e;switch(null==a?void 0:a.attributes.device_class){case"garage":switch(e){case"opening":return _a;case"closing":return ya;case"closed":return oa;default:return ra}case"gate":switch(e){case"opening":case"closing":return Ea;case"closed":return Ua;default:return Sa}case"door":return t?ca:da;case"damper":return t?Ba:za;case"shutter":switch(e){case"opening":return _a;case"closing":return ya;case"closed":return ja;default:return Ia}case"curtain":switch(e){case"opening":return Ca;case"closing":return $a;case"closed":return xa;default:return wa}case"blind":case"shade":switch(e){case"opening":return _a;case"closing":return ya;case"closed":return ka;default:return ga}case"window":switch(e){case"opening":return _a;case"closing":return ya;case"closed":return Ee;default:return Oe}}switch(e){case"opening":return _a;case"closing":return ya;case"closed":return Ee;default:return Oe}})(s,a);case"device_tracker":return"router"===(null==a?void 0:a.attributes.source_type)?"home"===s?xt:$t:["bluetooth","bluetooth_le"].includes(null==a?void 0:a.attributes.source_type)?"home"===s?Ct:It:"not_home"===s?jt:I;case"humidifier":return t&&"off"===t?kt:wt;case"input_boolean":return"on"===s?_t:gt;case"input_datetime":if(null==a||!a.attributes.has_date)return ie;if(!a.attributes.has_time)return n;break;case"lock":switch(s){case"unlocked":return Ze;case"jammed":return yt;case"locking":case"unlocking":return bt;default:return Ye}case"media_player":switch(null==a?void 0:a.attributes.device_class){case"speaker":switch(s){case"playing":return ft;case"paused":return vt;case"off":return pt;default:return mt}case"tv":switch(s){case"playing":return ht;case"paused":return ut;case"off":return lt;default:return ct}default:switch(s){case"playing":case"paused":return dt;case"off":return rt;default:return ot}}case"switch":switch(null==a?void 0:a.attributes.device_class){case"outlet":return"on"===s?Ke:Je;case"switch":return"on"===s?it:nt;default:return it}case"sensor":{const e=ts(a);if(e)return e;break}case"sun":return"above_horizon"===(null==a?void 0:a.state)?Wt[e]:re;case"switch_as_x":return st;case"threshold":return tt;case"update":return"on"===s?Pt(a)?at:Fe:De;case"weather":return((e,a)=>e?a&&"partlycloudy"===e?oe:Yt[e]:void 0)(null==a?void 0:a.state)}if(e in Wt)return Wt[e]},is=e=>e?((e,a,t)=>ss(e,a,t)||(console.warn(`Unable to find icon for domain ${e}`),Rt))(Vt(e.entity_id),e):Rt;zt([Ot("ha-state-icon")],(function(e,a){return{F:class extends a{constructor(...a){super(...a),e(this)}},d:[{kind:"field",decorators:[Ut({attribute:!1})],key:"state",value:void 0},{kind:"field",decorators:[Ut()],key:"icon",value:void 0},{kind:"method",key:"render",value:function(){var e,a;return this.icon||null!==(e=this.state)&&void 0!==e&&e.attributes.icon?Et`<ha-icon
        .icon=${this.icon||(null===(a=this.state)||void 0===a?void 0:a.attributes.icon)}
      ></ha-icon>`:Et`<ha-svg-icon .path=${is(this.state)}></ha-svg-icon>`}}]}}),St);let ns=zt(null,(function(a,s){class i extends s{constructor(...e){super(...e),a(this)}}return{F:i,d:[{kind:"field",key:"hass",value:void 0},{kind:"field",decorators:[Ut()],key:"stateObj",value:void 0},{kind:"field",decorators:[Ut()],key:"overrideIcon",value:void 0},{kind:"field",decorators:[Ut()],key:"overrideImage",value:void 0},{kind:"field",decorators:[Ut({type:Boolean})],key:"stateColor",value:void 0},{kind:"field",decorators:[Ut({type:Boolean,reflect:!0,attribute:"icon"})],key:"_showIcon",value:()=>!0},{kind:"field",decorators:[qt()],key:"_iconStyle",value:()=>({})},{kind:"method",key:"render",value:function(){const e=this.stateObj;if(!e&&!this.overrideIcon&&!this.overrideImage)return Et`<div class="missing">
        <ha-svg-icon .path=${t}></ha-svg-icon>
      </div>`;if(!this._showIcon)return Et``;const a=e?Qt(e):void 0;return Et`<ha-state-icon
      style=${At(this._iconStyle)}
      data-domain=${Dt(this.stateColor||"light"===a&&!1!==this.stateColor?a:void 0)}
      data-state=${e?(e=>{if(Kt.includes(e.state))return e.state;const a=e.entity_id.split(".")[0];let t=e.state;return"climate"===a&&(t=e.attributes.hvac_action),t})(e):""}
      .icon=${this.overrideIcon}
      .state=${e}
    ></ha-state-icon>`}},{kind:"method",key:"willUpdate",value:function(e){if(Ft(Nt(i.prototype),"willUpdate",this).call(this,e),!e.has("stateObj")&&!e.has("overrideImage")&&!e.has("overrideIcon"))return;const a=this.stateObj,t={},s={backgroundImage:""};if(this._showIcon=!0,a&&void 0===this.overrideImage)if(!a.attributes.entity_picture_local&&!a.attributes.entity_picture||this.overrideIcon){if("on"===a.state&&(!1!==this.stateColor&&a.attributes.rgb_color&&(t.color=`rgb(${a.attributes.rgb_color.join(",")})`),a.attributes.brightness&&!1!==this.stateColor)){const e=a.attributes.brightness;if("number"!=typeof e){const t=`Type error: state-badge expected number, but type of ${a.entity_id}.attributes.brightness is ${typeof e} (${e})`;console.warn(t)}t.filter=`brightness(${(e+245)/5}%)`}}else{let e=a.attributes.entity_picture_local||a.attributes.entity_picture;this.hass&&(e=this.hass.hassUrl(e)),"camera"===Vt(a.entity_id)&&(e=`${e}&width=${80}&height=${80}`),s.backgroundImage=`url(${e})`,this._showIcon=!1}else if(this.overrideImage){let e=this.overrideImage;this.hass&&(e=this.hass.hassUrl(e)),s.backgroundImage=`url(${e})`,this._showIcon=!1}this._iconStyle=t,Object.assign(this.style,s)}},{kind:"get",static:!0,key:"styles",value:function(){return[Ht,e`
        :host {
          position: relative;
          display: inline-block;
          width: 40px;
          color: var(--paper-item-icon-color, #44739e);
          border-radius: 50%;
          height: 40px;
          text-align: center;
          background-size: cover;
          line-height: 40px;
          vertical-align: middle;
          box-sizing: border-box;
        }
        :host(:focus) {
          outline: none;
        }
        :host(:not([icon]):focus) {
          border: 2px solid var(--divider-color);
        }
        :host([icon]:focus) {
          background: var(--divider-color);
        }
        ha-state-icon {
          transition: color 0.3s ease-in-out, filter 0.3s ease-in-out;
        }
        .missing {
          color: #fce588;
        }
      `]}}]}}),St);customElements.define("state-badge",ns);const os=e=>Et`<mwc-list-item graphic="avatar" .twoline=${!!e.entity_id}>
    ${e.state?Et`<state-badge slot="graphic" .stateObj=${e}></state-badge>`:""}
    <span>${e.friendly_name}</span>
    <span slot="secondary">${e.entity_id}</span>
  </mwc-list-item>`;zt([Ot("ha-entity-picker")],(function(e,a){return{F:class extends a{constructor(...a){super(...a),e(this)}},d:[{kind:"field",decorators:[Ut({attribute:!1})],key:"hass",value:void 0},{kind:"field",decorators:[Ut({type:Boolean})],key:"autofocus",value:()=>!1},{kind:"field",decorators:[Ut({type:Boolean})],key:"disabled",value:void 0},{kind:"field",decorators:[Ut({type:Boolean})],key:"required",value:void 0},{kind:"field",decorators:[Ut({type:Boolean,attribute:"allow-custom-entity"})],key:"allowCustomEntity",value:void 0},{kind:"field",decorators:[Ut()],key:"label",value:void 0},{kind:"field",decorators:[Ut()],key:"value",value:void 0},{kind:"field",decorators:[Ut()],key:"helper",value:void 0},{kind:"field",decorators:[Ut({type:Array,attribute:"include-domains"})],key:"includeDomains",value:void 0},{kind:"field",decorators:[Ut({type:Array,attribute:"exclude-domains"})],key:"excludeDomains",value:void 0},{kind:"field",decorators:[Ut({type:Array,attribute:"include-device-classes"})],key:"includeDeviceClasses",value:void 0},{kind:"field",decorators:[Ut({type:Array,attribute:"include-unit-of-measurement"})],key:"includeUnitOfMeasurement",value:void 0},{kind:"field",decorators:[Ut({type:Array,attribute:"include-entities"})],key:"includeEntities",value:void 0},{kind:"field",decorators:[Ut({type:Array,attribute:"exclude-entities"})],key:"excludeEntities",value:void 0},{kind:"field",decorators:[Ut()],key:"entityFilter",value:void 0},{kind:"field",decorators:[Ut({type:Boolean})],key:"hideClearIcon",value:()=>!1},{kind:"field",decorators:[qt()],key:"_opened",value:()=>!1},{kind:"field",decorators:[Lt("ha-combo-box",!0)],key:"comboBox",value:void 0},{kind:"method",key:"open",value:function(){this.updateComplete.then((()=>{var e;null===(e=this.comboBox)||void 0===e||e.open()}))}},{kind:"method",key:"focus",value:function(){this.updateComplete.then((()=>{var e;null===(e=this.comboBox)||void 0===e||e.focus()}))}},{kind:"field",key:"_initedStates",value:()=>!1},{kind:"field",key:"_states",value:()=>[]},{kind:"field",key:"_getStates",value(){return Mt(((e,a,t,s,i,n,o,r,d)=>{let c=[];if(!a)return[];let l=Object.keys(a.states);return l.length?r?(l=l.filter((e=>this.includeEntities.includes(e))),l.map((e=>({...a.states[e],friendly_name:Gt(a.states[e])||e}))).sort(((e,a)=>Jt(e.friendly_name,a.friendly_name)))):(d&&(l=l.filter((e=>!d.includes(e)))),t&&(l=l.filter((e=>t.includes(Vt(e))))),s&&(l=l.filter((e=>!s.includes(Vt(e))))),c=l.map((e=>({...a.states[e],friendly_name:Gt(a.states[e])||e}))).sort(((e,a)=>Jt(e.friendly_name,a.friendly_name))),n&&(c=c.filter((e=>e.entity_id===this.value||e.attributes.device_class&&n.includes(e.attributes.device_class)))),o&&(c=c.filter((e=>e.entity_id===this.value||e.attributes.unit_of_measurement&&o.includes(e.attributes.unit_of_measurement)))),i&&(c=c.filter((e=>e.entity_id===this.value||i(e)))),c.length?c:[{entity_id:"",state:"",last_changed:"",last_updated:"",context:{id:"",user_id:null,parent_id:null},friendly_name:this.hass.localize("ui.components.entity.entity-picker.no_match"),attributes:{friendly_name:this.hass.localize("ui.components.entity.entity-picker.no_match"),icon:"mdi:magnify"}}]):[{entity_id:"",state:"",last_changed:"",last_updated:"",context:{id:"",user_id:null,parent_id:null},friendly_name:this.hass.localize("ui.components.entity.entity-picker.no_entities"),attributes:{friendly_name:this.hass.localize("ui.components.entity.entity-picker.no_entities"),icon:"mdi:magnify"}}]}))}},{kind:"method",key:"shouldUpdate",value:function(e){return!!(e.has("value")||e.has("label")||e.has("disabled"))||!(!e.has("_opened")&&this._opened)}},{kind:"method",key:"willUpdate",value:function(e){(!this._initedStates||e.has("_opened")&&this._opened)&&(this._states=this._getStates(this._opened,this.hass,this.includeDomains,this.excludeDomains,this.entityFilter,this.includeDeviceClasses,this.includeUnitOfMeasurement,this.includeEntities,this.excludeEntities),this._initedStates&&(this.comboBox.filteredItems=this._states),this._initedStates=!0)}},{kind:"method",key:"render",value:function(){return Et`
      <ha-combo-box
        item-value-path="entity_id"
        item-label-path="friendly_name"
        .hass=${this.hass}
        .value=${this._value}
        .label=${void 0===this.label?this.hass.localize("ui.components.entity.entity-picker.entity"):this.label}
        .helper=${this.helper}
        .allowCustomValue=${this.allowCustomEntity}
        .filteredItems=${this._states}
        .renderer=${os}
        .required=${this.required}
        .disabled=${this.disabled}
        @opened-changed=${this._openedChanged}
        @value-changed=${this._valueChanged}
        @filter-changed=${this._filterChanged}
      >
      </ha-combo-box>
    `}},{kind:"get",key:"_value",value:function(){return this.value||""}},{kind:"method",key:"_openedChanged",value:function(e){this._opened=e.detail.value}},{kind:"method",key:"_valueChanged",value:function(e){e.stopPropagation();const a=e.detail.value;a!==this._value&&this._setValue(a)}},{kind:"method",key:"_filterChanged",value:function(e){const a=e.detail.value.toLowerCase();this.comboBox.filteredItems=this._states.filter((e=>e.entity_id.toLowerCase().includes(a)||Gt(e).toLowerCase().includes(a)))}},{kind:"method",key:"_setValue",value:function(e){this.value=e,setTimeout((()=>{Tt(this,"value-changed",{value:e}),Tt(this,"change")}),0)}}]}}),St);
