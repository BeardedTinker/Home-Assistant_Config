import{_ as e,j as i,e as t,y as d,n as r}from"./main-22e4648c.js";import"./c.5e0dc870.js";import"./c.5fd746d5.js";import"./c.2610e8cd.js";import"./c.2c462191.js";import"./c.8e1ed6df.js";import"./c.8e28b461.js";import"./c.fa63af8a.js";import"./c.19945fa6.js";let a=e([r("ha-selector-time")],(function(e,i){return{F:class extends i{constructor(...i){super(...i),e(this)}},d:[{kind:"field",decorators:[t({attribute:!1})],key:"hass",value:void 0},{kind:"field",decorators:[t({attribute:!1})],key:"selector",value:void 0},{kind:"field",decorators:[t()],key:"value",value:void 0},{kind:"field",decorators:[t()],key:"label",value:void 0},{kind:"field",decorators:[t()],key:"helper",value:void 0},{kind:"field",decorators:[t({type:Boolean})],key:"disabled",value:()=>!1},{kind:"field",decorators:[t({type:Boolean})],key:"required",value:()=>!1},{kind:"method",key:"render",value:function(){return d`
      <ha-time-input
        .value=${this.value}
        .locale=${this.hass.locale}
        .disabled=${this.disabled}
        .required=${this.required}
        .helper=${this.helper}
        .label=${this.label}
        enable-second
      ></ha-time-input>
    `}}]}}),i);export{a as HaTimeSelector};
