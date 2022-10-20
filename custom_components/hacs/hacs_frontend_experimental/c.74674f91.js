import{_ as e,e as i,t,i as a,y as s,eE as d,a_ as n,aA as c,k as r,eF as o,I as l,J as h,d as p,a5 as u,n as v,j as _,a7 as m,E as y,G as k}from"./main-22e4648c.js";import{b as f,s as g,d as $,a as b,g as x}from"./c.f0a491f8.js";import{f as j,a as F,b as D}from"./c.6f18200a.js";import{S as z}from"./c.3704df89.js";import{c as C}from"./c.19945fa6.js";import"./c.f4a1d0ac.js";import{e as E}from"./c.3f62d98e.js";import{c as I}from"./c.d2f13ac1.js";import{c as P}from"./c.6eb9fcd4.js";import"./c.55c2f3c1.js";import"./c.4f8a1d9d.js";import"./c.7c49f57f.js";import"./c.2c462191.js";import"./c.8e1ed6df.js";import"./c.8e28b461.js";import"./c.fa63af8a.js";import"./c.874c8cfd.js";import"./c.fa0ef026.js";import"./c.1024e243.js";import"./c.35d79203.js";import"./c.811f664e.js";import"./c.04ecc0ad.js";import"./c.2610e8cd.js";import"./c.474ee2a6.js";e([v("ha-target-picker")],(function(e,v){return{F:class extends v{constructor(...i){super(...i),e(this)}},d:[{kind:"field",decorators:[i({attribute:!1})],key:"hass",value:void 0},{kind:"field",decorators:[i({attribute:!1})],key:"value",value:void 0},{kind:"field",decorators:[i()],key:"label",value:void 0},{kind:"field",decorators:[i()],key:"helper",value:void 0},{kind:"field",decorators:[i({type:Array,attribute:"include-domains"})],key:"includeDomains",value:void 0},{kind:"field",decorators:[i({type:Array,attribute:"include-device-classes"})],key:"includeDeviceClasses",value:void 0},{kind:"field",decorators:[i()],key:"deviceFilter",value:void 0},{kind:"field",decorators:[i()],key:"entityRegFilter",value:void 0},{kind:"field",decorators:[i()],key:"entityFilter",value:void 0},{kind:"field",decorators:[i({type:Boolean,reflect:!0})],key:"disabled",value:()=>!1},{kind:"field",decorators:[i({type:Boolean})],key:"horizontal",value:()=>!1},{kind:"field",decorators:[t()],key:"_areas",value:void 0},{kind:"field",decorators:[t()],key:"_devices",value:void 0},{kind:"field",decorators:[t()],key:"_entities",value:void 0},{kind:"field",decorators:[t()],key:"_addMode",value:void 0},{kind:"field",decorators:[a("#input")],key:"_inputElement",value:void 0},{kind:"method",key:"hassSubscribe",value:function(){return[f(this.hass.connection,(e=>{const i={};for(const t of e)i[t.area_id]=t;this._areas=i})),g(this.hass.connection,(e=>{const i={};for(const t of e)i[t.id]=t;this._devices=i})),$(this.hass.connection,(e=>{this._entities=e}))]}},{kind:"method",key:"render",value:function(){return this._areas&&this._devices&&this._entities?s`
      ${this.horizontal?s`
            <div class="horizontal-container">
              ${this._renderChips()} ${this._renderPicker()}
            </div>
            ${this._renderItems()}
          `:s`
            <div>
              ${this._renderItems()} ${this._renderPicker()}
              ${this._renderChips()}
            </div>
          `}
    `:s``}},{kind:"method",key:"_renderItems",value:function(){var e,i,t;return s`
      <div class="mdc-chip-set items">
        ${null!==(e=this.value)&&void 0!==e&&e.area_id?E(this.value.area_id).map((e=>{const i=this._areas[e];return this._renderChip("area_id",e,(null==i?void 0:i.name)||e,void 0,d)})):""}
        ${null!==(i=this.value)&&void 0!==i&&i.device_id?E(this.value.device_id).map((e=>{const i=this._devices[e];return this._renderChip("device_id",e,i?b(i,this.hass):e,void 0,n)})):""}
        ${null!==(t=this.value)&&void 0!==t&&t.entity_id?E(this.value.entity_id).map((e=>{const i=this.hass.states[e];return this._renderChip("entity_id",e,i?P(i):e,i)})):""}
      </div>
    `}},{kind:"method",key:"_renderChips",value:function(){return s`
      <div class="mdc-chip-set">
        <div
          class="mdc-chip area_id add"
          .type=${"area_id"}
          @click=${this._showPicker}
        >
          <div class="mdc-chip__ripple"></div>
          <ha-svg-icon
            class="mdc-chip__icon mdc-chip__icon--leading"
            .path=${c}
          ></ha-svg-icon>
          <span role="gridcell">
            <span role="button" tabindex="0" class="mdc-chip__primary-action">
              <span class="mdc-chip__text"
                >${this.hass.localize("ui.components.target-picker.add_area_id")}</span
              >
            </span>
          </span>
        </div>
        <div
          class="mdc-chip device_id add"
          .type=${"device_id"}
          @click=${this._showPicker}
        >
          <div class="mdc-chip__ripple"></div>
          <ha-svg-icon
            class="mdc-chip__icon mdc-chip__icon--leading"
            .path=${c}
          ></ha-svg-icon>
          <span role="gridcell">
            <span role="button" tabindex="0" class="mdc-chip__primary-action">
              <span class="mdc-chip__text"
                >${this.hass.localize("ui.components.target-picker.add_device_id")}</span
              >
            </span>
          </span>
        </div>
        <div
          class="mdc-chip entity_id add"
          .type=${"entity_id"}
          @click=${this._showPicker}
        >
          <div class="mdc-chip__ripple"></div>
          <ha-svg-icon
            class="mdc-chip__icon mdc-chip__icon--leading"
            .path=${c}
          ></ha-svg-icon>
          <span role="gridcell">
            <span role="button" tabindex="0" class="mdc-chip__primary-action">
              <span class="mdc-chip__text"
                >${this.hass.localize("ui.components.target-picker.add_entity_id")}</span
              >
            </span>
          </span>
        </div>
      </div>
      ${this.helper?s`<ha-input-helper-text>${this.helper}</ha-input-helper-text>`:""}
    `}},{kind:"method",key:"_showPicker",value:async function(e){this._addMode=e.currentTarget.type,await this.updateComplete,setTimeout((()=>{var e,i;null===(e=this._inputElement)||void 0===e||e.open(),null===(i=this._inputElement)||void 0===i||i.focus()}),0)}},{kind:"method",key:"_renderChip",value:function(e,i,t,a,d){return s`
      <div
        class="mdc-chip ${r({[e]:!0})}"
      >
        ${d?s`<ha-svg-icon
              class="mdc-chip__icon mdc-chip__icon--leading"
              .path=${d}
            ></ha-svg-icon>`:""}
        ${a?s`<ha-state-icon
              class="mdc-chip__icon mdc-chip__icon--leading"
              .state=${a}
            ></ha-state-icon>`:""}
        <span role="gridcell">
          <span role="button" tabindex="0" class="mdc-chip__primary-action">
            <span class="mdc-chip__text">${t}</span>
          </span>
        </span>
        ${"entity_id"===e?"":s` <span role="gridcell">
              <ha-icon-button
                class="expand-btn mdc-chip__icon mdc-chip__icon--trailing"
                tabindex="-1"
                role="button"
                .label=${this.hass.localize("ui.components.target-picker.expand")}
                .path=${o}
                hideTooltip
                .id=${i}
                .type=${e}
                @click=${this._handleExpand}
              ></ha-icon-button>
              <paper-tooltip class="expand" animation-delay="0"
                >${this.hass.localize(`ui.components.target-picker.expand_${e}`)}</paper-tooltip
              >
            </span>`}
        <span role="gridcell">
          <ha-icon-button
            class="mdc-chip__icon mdc-chip__icon--trailing"
            tabindex="-1"
            role="button"
            .label=${this.hass.localize("ui.components.target-picker.remove")}
            .path=${l}
            hideTooltip
            .id=${i}
            .type=${e}
            @click=${this._handleRemove}
          ></ha-icon-button>
          <paper-tooltip animation-delay="0"
            >${this.hass.localize(`ui.components.target-picker.remove_${e}`)}</paper-tooltip
          >
        </span>
      </div>
    `}},{kind:"method",key:"_renderPicker",value:function(){switch(this._addMode){case"area_id":return s`
          <ha-area-picker
            .hass=${this.hass}
            id="input"
            .type=${"area_id"}
            .label=${this.hass.localize("ui.components.target-picker.add_area_id")}
            no-add
            .deviceFilter=${this.deviceFilter}
            .entityFilter=${this.entityRegFilter}
            .includeDeviceClasses=${this.includeDeviceClasses}
            .includeDomains=${this.includeDomains}
            @value-changed=${this._targetPicked}
          ></ha-area-picker>
        `;case"device_id":return s`
          <ha-device-picker
            .hass=${this.hass}
            id="input"
            .type=${"device_id"}
            .label=${this.hass.localize("ui.components.target-picker.add_device_id")}
            .deviceFilter=${this.deviceFilter}
            .entityFilter=${this.entityRegFilter}
            .includeDeviceClasses=${this.includeDeviceClasses}
            .includeDomains=${this.includeDomains}
            @value-changed=${this._targetPicked}
          ></ha-device-picker>
        `;case"entity_id":return s`
          <ha-entity-picker
            .hass=${this.hass}
            id="input"
            .type=${"entity_id"}
            .label=${this.hass.localize("ui.components.target-picker.add_entity_id")}
            .entityFilter=${this.entityFilter}
            .includeDeviceClasses=${this.includeDeviceClasses}
            .includeDomains=${this.includeDomains}
            @value-changed=${this._targetPicked}
            allow-custom-entity
          ></ha-entity-picker>
        `}return s``}},{kind:"method",key:"_targetPicked",value:function(e){if(e.stopPropagation(),!e.detail.value)return;const i=e.detail.value,t=e.currentTarget;t.value="",this._addMode=void 0,h(this,"value-changed",{value:this.value?{...this.value,[t.type]:this.value[t.type]?[...E(this.value[t.type]),i]:i}:{[t.type]:i}})}},{kind:"method",key:"_handleExpand",value:function(e){const i=e.currentTarget,t=[],a=[];if("area_id"===i.type)Object.values(this._devices).forEach((e=>{var a;e.area_id!==i.id||null!==(a=this.value.device_id)&&void 0!==a&&a.includes(e.id)||!this._deviceMeetsFilter(e)||t.push(e.id)})),this._entities.forEach((e=>{var t;e.area_id!==i.id||null!==(t=this.value.entity_id)&&void 0!==t&&t.includes(e.entity_id)||!this._entityRegMeetsFilter(e)||a.push(e.entity_id)}));else{if("device_id"!==i.type)return;this._entities.forEach((e=>{var t;e.device_id!==i.id||null!==(t=this.value.entity_id)&&void 0!==t&&t.includes(e.entity_id)||!this._entityRegMeetsFilter(e)||a.push(e.entity_id)}))}let s=this.value;a.length&&(s=this._addItems(s,"entity_id",a)),t.length&&(s=this._addItems(s,"device_id",t)),s=this._removeItem(s,i.type,i.id),h(this,"value-changed",{value:s})}},{kind:"method",key:"_handleRemove",value:function(e){const i=e.currentTarget;h(this,"value-changed",{value:this._removeItem(this.value,i.type,i.id)})}},{kind:"method",key:"_addItems",value:function(e,i,t){return{...e,[i]:e[i]?E(e[i]).concat(t):t}}},{kind:"method",key:"_removeItem",value:function(e,i,t){const a=E(e[i]).filter((e=>String(e)!==t));if(a.length)return{...e,[i]:a};const s={...e};return delete s[i],Object.keys(s).length?s:void 0}},{kind:"method",key:"_deviceMeetsFilter",value:function(e){var i;const t=null===(i=this._entities)||void 0===i?void 0:i.filter((i=>i.device_id===e.id));if(this.includeDomains){if(!t||!t.length)return!1;if(!t.some((e=>this.includeDomains.includes(I(e.entity_id)))))return!1}if(this.includeDeviceClasses){if(!t||!t.length)return!1;if(!t.some((e=>{const i=this.hass.states[e.entity_id];return!!i&&(i.attributes.device_class&&this.includeDeviceClasses.includes(i.attributes.device_class))})))return!1}return!this.deviceFilter||this.deviceFilter(e)}},{kind:"method",key:"_entityRegMeetsFilter",value:function(e){if(e.entity_category)return!1;if(this.includeDomains&&!this.includeDomains.includes(I(e.entity_id)))return!1;if(this.includeDeviceClasses){const i=this.hass.states[e.entity_id];if(!i)return!1;if(!i.attributes.device_class||!this.includeDeviceClasses.includes(i.attributes.device_class))return!1}return!this.entityRegFilter||this.entityRegFilter(e)}},{kind:"get",static:!0,key:"styles",value:function(){return p`
      ${u(C)}
      .horizontal-container {
        display: flex;
        flex-wrap: wrap;
        min-height: 56px;
        align-items: center;
      }
      .mdc-chip {
        color: var(--primary-text-color);
      }
      .items {
        z-index: 2;
      }
      .mdc-chip-set {
        padding: 4px 0;
      }
      .mdc-chip.add {
        color: rgba(0, 0, 0, 0.87);
      }
      .mdc-chip:not(.add) {
        cursor: default;
      }
      .mdc-chip ha-icon-button {
        --mdc-icon-button-size: 24px;
        display: flex;
        align-items: center;
        outline: none;
      }
      .mdc-chip ha-icon-button ha-svg-icon {
        border-radius: 50%;
        background: var(--secondary-text-color);
      }
      .mdc-chip__icon.mdc-chip__icon--trailing {
        width: 16px;
        height: 16px;
        --mdc-icon-size: 14px;
        color: var(--secondary-text-color);
        margin-inline-start: 4px !important;
        margin-inline-end: -4px !important;
        direction: var(--direction);
      }
      .mdc-chip__icon--leading {
        display: flex;
        align-items: center;
        justify-content: center;
        --mdc-icon-size: 20px;
        border-radius: 50%;
        padding: 6px;
        margin-left: -14px !important;
        margin-inline-start: -14px !important;
        margin-inline-end: 4px !important;
        direction: var(--direction);
      }
      .expand-btn {
        margin-right: 0;
      }
      .mdc-chip.area_id:not(.add) {
        border: 2px solid #fed6a4;
        background: var(--card-background-color);
      }
      .mdc-chip.area_id:not(.add) .mdc-chip__icon--leading,
      .mdc-chip.area_id.add {
        background: #fed6a4;
      }
      .mdc-chip.device_id:not(.add) {
        border: 2px solid #a8e1fb;
        background: var(--card-background-color);
      }
      .mdc-chip.device_id:not(.add) .mdc-chip__icon--leading,
      .mdc-chip.device_id.add {
        background: #a8e1fb;
      }
      .mdc-chip.entity_id:not(.add) {
        border: 2px solid #d2e7b9;
        background: var(--card-background-color);
      }
      .mdc-chip.entity_id:not(.add) .mdc-chip__icon--leading,
      .mdc-chip.entity_id.add {
        background: #d2e7b9;
      }
      .mdc-chip:hover {
        z-index: 5;
      }
      paper-tooltip.expand {
        min-width: 200px;
      }
      :host([disabled]) .mdc-chip {
        opacity: var(--light-disabled-opacity);
        pointer-events: none;
      }
    `}}]}}),z(_));let w=e([v("ha-selector-target")],(function(e,a){class d extends a{constructor(...i){super(...i),e(this)}}return{F:d,d:[{kind:"field",decorators:[i()],key:"hass",value:void 0},{kind:"field",decorators:[i()],key:"selector",value:void 0},{kind:"field",decorators:[i()],key:"value",value:void 0},{kind:"field",decorators:[i()],key:"label",value:void 0},{kind:"field",decorators:[i()],key:"helper",value:void 0},{kind:"field",decorators:[i({type:Boolean})],key:"disabled",value:()=>!1},{kind:"field",decorators:[t()],key:"_entitySources",value:void 0},{kind:"field",decorators:[t()],key:"_entities",value:void 0},{kind:"field",key:"_deviceIntegrationLookup",value:()=>m(x)},{kind:"method",key:"hassSubscribe",value:function(){return[$(this.hass.connection,(e=>{this._entities=e.filter((e=>null!==e.device_id))}))]}},{kind:"method",key:"updated",value:function(e){var i,t;y(k(d.prototype),"updated",this).call(this,e),e.has("selector")&&(null!==(i=this.selector.target.device)&&void 0!==i&&i.integration||null!==(t=this.selector.target.entity)&&void 0!==t&&t.integration)&&!this._entitySources&&j(this.hass).then((e=>{this._entitySources=e}))}},{kind:"method",key:"render",value:function(){var e,i;return(null!==(e=this.selector.target.device)&&void 0!==e&&e.integration||null!==(i=this.selector.target.entity)&&void 0!==i&&i.integration)&&!this._entitySources?s``:s`<ha-target-picker
      .hass=${this.hass}
      .value=${this.value}
      .helper=${this.helper}
      .deviceFilter=${this._filterDevices}
      .entityFilter=${this._filterEntities}
      .disabled=${this.disabled}
    ></ha-target-picker>`}},{kind:"field",key:"_filterEntities",value(){return e=>!this.selector.target.entity||F(this.selector.target.entity,e,this._entitySources)}},{kind:"field",key:"_filterDevices",value(){return e=>{if(!this.selector.target.device)return!0;const i=this._entitySources&&this._entities?this._deviceIntegrationLookup(this._entitySources,this._entities):void 0;return D(this.selector.target.device,e,i)}}},{kind:"get",static:!0,key:"styles",value:function(){return p`
      ha-target-picker {
        display: block;
      }
    `}}]}}),z(_));export{w as HaTargetSelector};
