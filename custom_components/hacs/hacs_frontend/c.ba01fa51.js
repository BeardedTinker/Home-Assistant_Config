import{a as i,H as s,e,$ as t,d as a,r as o,ap as r,aq as l,am as n,ar as c,as as h,n as d}from"./main-a0d7432d.js";import"./c.7ee871d3.js";import"./c.c608beec.js";import"./c.8e28b461.js";let m=i([d("hacs-removed-dialog")],(function(i,s){return{F:class extends s{constructor(...s){super(...s),i(this)}},d:[{kind:"field",decorators:[e({attribute:!1})],key:"repository",value:void 0},{kind:"field",decorators:[e({type:Boolean})],key:"_updating",value:()=>!1},{kind:"method",key:"render",value:function(){if(!this.active)return t``;const i=this.hacs.removed.find((i=>i.repository===this.repository.full_name));return t`
      <hacs-dialog
        .active=${this.active}
        .hass=${this.hass}
        .title=${this.hacs.localize("entry.messages.removed_repository",{repository:this.repository.full_name})}
      >
        <div class="content">
          <div><b>${this.hacs.localize("dialog_removed.name")}:</b> ${this.repository.name}</div>
          ${i.removal_type?t` <div>
                <b>${this.hacs.localize("dialog_removed.type")}:</b> ${i.removal_type}
              </div>`:""}
          ${i.reason?t` <div>
                <b>${this.hacs.localize("dialog_removed.reason")}:</b> ${i.reason}
              </div>`:""}
          ${i.link?t`          <div>
            </b><hacs-link .url=${i.link}>${this.hacs.localize("dialog_removed.link")}</hacs-link>
          </div>`:""}
        </div>
        <mwc-button slot="secondaryaction" @click=${this._ignoreRepository}>
          ${this.hacs.localize("common.ignore")}
        </mwc-button>
        <mwc-button class="uninstall" slot="primaryaction" @click=${this._uninstallRepository}
          >${this._updating?t`<ha-circular-progress active size="small"></ha-circular-progress>`:this.hacs.localize("common.remove")}</mwc-button
        >
      </hacs-dialog>
    `}},{kind:"get",static:!0,key:"styles",value:function(){return[a,o`
        .uninstall {
          --mdc-theme-primary: var(--hcv-color-error);
        }
      `]}},{kind:"method",key:"_lovelaceUrl",value:function(){var i,s;return`/hacsfiles/${null===(i=this.repository)||void 0===i?void 0:i.full_name.split("/")[1]}/${null===(s=this.repository)||void 0===s?void 0:s.file_name}`}},{kind:"method",key:"_ignoreRepository",value:async function(){await r(this.hass,this.repository.full_name);const i=await l(this.hass);this.dispatchEvent(new CustomEvent("update-hacs",{detail:{removed:i},bubbles:!0,composed:!0})),this.dispatchEvent(new Event("hacs-dialog-closed",{bubbles:!0,composed:!0}))}},{kind:"method",key:"_uninstallRepository",value:async function(){if(this._updating=!0,"plugin"===this.repository.category&&this.hacs.info&&"yaml"!==this.hacs.info.lovelace_mode){(await n(this.hass)).filter((i=>i.url.startsWith(this._lovelaceUrl()))).forEach((i=>{c(this.hass,String(i.id))}))}await h(this.hass,String(this.repository.id)),this._updating=!1,this.active=!1}}]}}),s);export{m as HacsRemovedDialog};
