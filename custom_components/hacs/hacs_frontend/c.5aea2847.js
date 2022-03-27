import{a as t,H as i,e,m as o,$ as s,n as r}from"./main-c486ac4b.js";import{m as a}from"./c.20f5b223.js";import"./c.8518b2d7.js";import"./c.82c823fb.js";import"./c.3f18632e.js";import"./c.f23b59f3.js";import"./c.9f27b448.js";import"./c.0a038163.js";let d=t([r("hacs-generic-dialog")],(function(t,i){return{F:class extends i{constructor(...i){super(...i),t(this)}},d:[{kind:"field",decorators:[e({type:Boolean})],key:"markdown",value:()=>!1},{kind:"field",decorators:[e()],key:"repository",value:void 0},{kind:"field",decorators:[e()],key:"header",value:void 0},{kind:"field",decorators:[e()],key:"content",value:void 0},{kind:"field",key:"_getRepository",value:()=>o(((t,i)=>null==t?void 0:t.find((t=>t.id===i))))},{kind:"method",key:"render",value:function(){if(!this.active||!this.repository)return s``;const t=this._getRepository(this.hacs.repositories,this.repository);return s`
      <hacs-dialog .active=${this.active} .narrow=${this.narrow} .hass=${this.hass}>
        <div slot="header">${this.header||""}</div>
        ${this.markdown?this.repository?a.html(this.content||"",t):a.html(this.content||""):this.content||""}
      </hacs-dialog>
    `}}]}}),i);export{d as HacsGenericDialog};
