import{_ as e,j as a,e as d,y as t,O as i,n as l}from"./main-e6d3fb5e.js";import"./c.cc8d7708.js";import"./c.6795ddb8.js";import"./c.5fe2e3ab.js";import"./c.5bcc4ef4.js";import"./c.7a38bd55.js";import"./c.8e28b461.js";import"./c.11013a9d.js";import"./c.54b4c8e8.js";let r=e([l("ha-selector-object")],(function(e,a){return{F:class extends a{constructor(...a){super(...a),e(this)}},d:[{kind:"field",decorators:[d()],key:"hass",value:void 0},{kind:"field",decorators:[d()],key:"value",value:void 0},{kind:"field",decorators:[d()],key:"label",value:void 0},{kind:"field",decorators:[d()],key:"helper",value:void 0},{kind:"field",decorators:[d()],key:"placeholder",value:void 0},{kind:"field",decorators:[d({type:Boolean})],key:"disabled",value:()=>!1},{kind:"field",decorators:[d({type:Boolean})],key:"required",value:()=>!0},{kind:"method",key:"render",value:function(){return t`<ha-yaml-editor
        .hass=${this.hass}
        .readonly=${this.disabled}
        .label=${this.label}
        .required=${this.required}
        .placeholder=${this.placeholder}
        .defaultValue=${this.value}
        @value-changed=${this._handleChange}
      ></ha-yaml-editor>
      ${this.helper?t`<ha-input-helper-text>${this.helper}</ha-input-helper-text>`:""} `}},{kind:"method",key:"_handleChange",value:function(e){const a=e.target.value;e.target.isValid&&this.value!==a&&i(this,"value-changed",{value:a})}}]}}),a);export{r as HaObjectSelector};
