import{_ as e,j as a,e as t,y as i,O as d,d as l,n as s}from"./main-c66a9a06.js";import"./c.bbadaeea.js";import"./c.6912e15e.js";import"./c.a5550d10.js";import"./c.8e28b461.js";import"./c.41d13611.js";import"./c.930daaba.js";let o=e([s("ha-selector-boolean")],(function(e,a){return{F:class extends a{constructor(...a){super(...a),e(this)}},d:[{kind:"field",decorators:[t()],key:"hass",value:void 0},{kind:"field",decorators:[t()],key:"value",value:void 0},{kind:"field",decorators:[t()],key:"label",value:void 0},{kind:"field",decorators:[t()],key:"helper",value:void 0},{kind:"field",decorators:[t({type:Boolean})],key:"disabled",value:()=>!1},{kind:"method",key:"render",value:function(){return i`
      <ha-formfield alignEnd spaceBetween .label=${this.label}>
        <ha-switch
          .checked=${this.value}
          @change=${this._handleChange}
          .disabled=${this.disabled}
        ></ha-switch>
      </ha-formfield>
      ${this.helper?i`<ha-input-helper-text>${this.helper}</ha-input-helper-text>`:""}
    `}},{kind:"method",key:"_handleChange",value:function(e){const a=e.target.checked;this.value!==a&&d(this,"value-changed",{value:a})}},{kind:"get",static:!0,key:"styles",value:function(){return l`
      ha-formfield {
        display: flex;
        height: 56px;
        align-items: center;
        --mdc-typography-body2-font-size: 1em;
      }
    `}}]}}),a);export{o as HaBooleanSelector};
