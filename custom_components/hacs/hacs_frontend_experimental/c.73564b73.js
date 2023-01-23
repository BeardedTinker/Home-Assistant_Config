import{_ as e,j as i,e as d,y as t,n as r}from"./main-e6d3fb5e.js";import"./c.3d2c5f40.js";import"./c.46ce3076.js";import"./c.2610e8cd.js";import"./c.6795ddb8.js";import"./c.7a38bd55.js";import"./c.8e28b461.js";import"./c.11013a9d.js";import"./c.54b4c8e8.js";let o=e([r("ha-selector-time")],(function(e,i){return{F:class extends i{constructor(...i){super(...i),e(this)}},d:[{kind:"field",decorators:[d({attribute:!1})],key:"hass",value:void 0},{kind:"field",decorators:[d({attribute:!1})],key:"selector",value:void 0},{kind:"field",decorators:[d()],key:"value",value:void 0},{kind:"field",decorators:[d()],key:"label",value:void 0},{kind:"field",decorators:[d()],key:"helper",value:void 0},{kind:"field",decorators:[d({type:Boolean})],key:"disabled",value:()=>!1},{kind:"field",decorators:[d({type:Boolean})],key:"required",value:()=>!1},{kind:"method",key:"render",value:function(){return t`
      <ha-time-input
        .value=${this.value}
        .locale=${this.hass.locale}
        .disabled=${this.disabled}
        .required=${this.required}
        .helper=${this.helper}
        .label=${this.label}
        enable-second
      ></ha-time-input>
    `}}]}}),i);export{o as HaTimeSelector};
