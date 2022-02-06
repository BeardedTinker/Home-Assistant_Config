import{_ as e,H as t,e as i,m as o,$ as s,n as r}from"./main-c4420e0b.js";import{m as a}from"./c.acc0d39e.js";import"./c.00409097.js";import"./c.b771f55c.js";import"./c.154e2e10.js";import"./c.9f27b448.js";import"./c.0a038163.js";let d=e([r("hacs-generic-dialog")],(function(e,t){return{F:class extends t{constructor(...t){super(...t),e(this)}},d:[{kind:"field",decorators:[i({type:Boolean})],key:"markdown",value:()=>!1},{kind:"field",decorators:[i()],key:"repository",value:void 0},{kind:"field",decorators:[i()],key:"header",value:void 0},{kind:"field",decorators:[i()],key:"content",value:void 0},{kind:"field",key:"_getRepository",value:()=>o((e,t)=>null==e?void 0:e.find(e=>e.id===t))},{kind:"method",key:"render",value:function(){if(!this.active||!this.repository)return s``;const e=this._getRepository(this.hacs.repositories,this.repository);return s`
      <hacs-dialog .active=${this.active} .narrow=${this.narrow} .hass=${this.hass}>
        <div slot="header">${this.header||""}</div>
        ${this.markdown?this.repository?a.html(this.content||"",e):a.html(this.content||""):this.content||""}
      </hacs-dialog>
    `}}]}}),t);export{d as HacsGenericDialog};
