import{Z as e,W as i,_ as r,j as a,e as t,y as l,J as o,d,n as s}from"./main-ec7846c8.js";import"./c.541a83df.js";import"./c.0e3055bd.js";import"./c.8e28b461.js";import"./c.eea05cf6.js";import"./c.3db34379.js";customElements.define("ha-labeled-slider",class extends e{static get template(){return i`
      <style>
        :host {
          display: block;
        }

        .title {
          margin: 5px 0 8px;
          color: var(--primary-text-color);
        }

        .slider-container {
          display: flex;
        }

        ha-icon {
          margin-top: 4px;
          color: var(--secondary-text-color);
        }

        ha-slider {
          flex-grow: 1;
          background-image: var(--ha-slider-background);
          border-radius: 4px;
        }
      </style>

      <div class="title">[[_getTitle()]]</div>
      <div class="extra-container"><slot name="extra"></slot></div>
      <div class="slider-container">
        <ha-icon icon="[[icon]]" hidden$="[[!icon]]"></ha-icon>
        <ha-slider
          min="[[min]]"
          max="[[max]]"
          step="[[step]]"
          pin="[[pin]]"
          disabled="[[disabled]]"
          value="{{value}}"
        ></ha-slider>
      </div>
      <template is="dom-if" if="[[helper]]">
        <ha-input-helper-text>[[helper]]</ha-input-helper-text>
      </template>
    `}_getTitle(){return`${this.caption}${this.caption&&this.required?" *":""}`}static get properties(){return{caption:String,disabled:Boolean,required:Boolean,min:Number,max:Number,pin:Boolean,step:Number,helper:String,extra:{type:Boolean,value:!1},ignoreBarTouch:{type:Boolean,value:!0},icon:{type:String,value:""},value:{type:Number,notify:!0}}}});let n=r([s("ha-selector-color_temp")],(function(e,i){return{F:class extends i{constructor(...i){super(...i),e(this)}},d:[{kind:"field",decorators:[t()],key:"hass",value:void 0},{kind:"field",decorators:[t()],key:"selector",value:void 0},{kind:"field",decorators:[t()],key:"value",value:void 0},{kind:"field",decorators:[t()],key:"label",value:void 0},{kind:"field",decorators:[t()],key:"helper",value:void 0},{kind:"field",decorators:[t({type:Boolean,reflect:!0})],key:"disabled",value:()=>!1},{kind:"field",decorators:[t({type:Boolean})],key:"required",value:()=>!0},{kind:"method",key:"render",value:function(){var e,i,r,a;return l`
      <ha-labeled-slider
        pin
        icon="hass:thermometer"
        .caption=${this.label||""}
        .min=${null!==(e=null===(i=this.selector.color_temp)||void 0===i?void 0:i.min_mireds)&&void 0!==e?e:153}
        .max=${null!==(r=null===(a=this.selector.color_temp)||void 0===a?void 0:a.max_mireds)&&void 0!==r?r:500}
        .value=${this.value}
        .disabled=${this.disabled}
        .helper=${this.helper}
        .required=${this.required}
        @change=${this._valueChanged}
      ></ha-labeled-slider>
    `}},{kind:"method",key:"_valueChanged",value:function(e){o(this,"value-changed",{value:Number(e.target.value)})}},{kind:"field",static:!0,key:"styles",value:()=>d`
    ha-labeled-slider {
      --ha-slider-background: -webkit-linear-gradient(
        var(--float-end),
        rgb(255, 160, 0) 0%,
        white 50%,
        rgb(166, 209, 255) 100%
      );
      /* The color temp minimum value shouldn't be rendered differently. It's not "off". */
      --paper-slider-knob-start-border-color: var(--primary-color);
    }
  `}]}}),a);export{n as HaColorTempSelector};
