import{_ as t,H as e,e as i,m as o,p as s,n as r}from"./main-8113c4f2.js";import{m as a}from"./c.a935d548.js";import"./c.868d2b7c.js";import"./c.51469fb0.js";import"./c.e709cbfb.js";import"./c.9f27b448.js";import"./c.0a038163.js";let d=t([r("hacs-generic-dialog")],(function(t,e){return{F:class extends e{constructor(...e){super(...e),t(this)}},d:[{kind:"field",decorators:[i({type:Boolean})],key:"markdown",value:()=>!1},{kind:"field",decorators:[i()],key:"repository",value:void 0},{kind:"field",decorators:[i()],key:"header",value:void 0},{kind:"field",decorators:[i()],key:"content",value:void 0},{kind:"field",key:"_getRepository",value:()=>o((t,e)=>null==t?void 0:t.find(t=>t.id===e))},{kind:"method",key:"render",value:function(){if(!this.active||!this.repository)return s``;const t=this._getRepository(this.hacs.repositories,this.repository);return s`
      <hacs-dialog .active=${this.active} .narrow=${this.narrow} .hass=${this.hass}>
        <div slot="header">${this.header||""}</div>
        ${this.markdown?this.repository?a.html(this.content||"",t):a.html(this.content||""):this.content||""}
      </hacs-dialog>
    `}}]}}),e);export{d as HacsGenericDialog};
