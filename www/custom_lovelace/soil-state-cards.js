(function () {
    'use strict';

    /**
     * We're reusing LitElement from other exisitng component this way we don't need to include it in our bundle.
     *
     * Maybe in the future LitElement will be globally available but currently only Polymer.Element is there.
     */
    var LitElement = LitElement || Object.getPrototypeOf(customElements.get("home-assistant-main"));
    const { html, css } = LitElement.prototype;

    console.info("%c SOIL-STATE-CARD %c 1.6.4", "color: white; background: forestgreen; font-weight: 700;", "color: forestgreen; background: white; font-weight: 700;");
    /**
     * Logs message in developer console
     * @param message Message to log
     * @param level Message level/importance
     */
    const log = (message, level = "warn") => {
        console[level]("[soil-state-card] " + message);
    };
    /**
     * Converts HTML hex color to RGB values
     *
     * @param color Color to convert
     */
    const convertHexColorToRGB = (color) => {
        color = color.replace("#", "");
        return {
            r: parseInt(color.substr(0, 2), 16),
            g: parseInt(color.substr(2, 2), 16),
            b: parseInt(color.substr(4, 2), 16),
        };
    };
    /**
     * Gets color interpolation for given color range and percentage
     *
     * @param colors HTML hex color values
     * @param pct Percent
     */
    const getColorInterpolationForPercentage = function (colors, pct) {
        // convert from 0-100 to 0-1 range
        pct = pct / 100;
        const percentColors = colors.map((color, index) => {
            return {
                pct: (1 / (colors.length - 1)) * index,
                color: convertHexColorToRGB(color)
            };
        });
        let colorBucket = 1;
        for (colorBucket = 1; colorBucket < percentColors.length - 1; colorBucket++) {
            if (pct < percentColors[colorBucket].pct) {
                break;
            }
        }
        const lower = percentColors[colorBucket - 1];
        const upper = percentColors[colorBucket];
        const range = upper.pct - lower.pct;
        const rangePct = (pct - lower.pct) / range;
        const pctLower = 1 - rangePct;
        const pctUpper = rangePct;
        const color = {
            r: Math.floor(lower.color.r * pctLower + upper.color.r * pctUpper),
            g: Math.floor(lower.color.g * pctLower + upper.color.g * pctUpper),
            b: Math.floor(lower.color.b * pctLower + upper.color.b * pctUpper)
        };
        return "rgb(" + [color.r, color.g, color.b].join(",") + ")";
    };
    /**
     * Checks whether given value is a number
     * @param val String value to check
     */
    const isNumber = (val) => !isNaN(Number(val));
    /**
     * Returns array of values regardles if given value is string array or null
     * @param val Value to process
     */
    const safeGetArray = (val) => {
        if (Array.isArray(val)) {
            return val;
        }
        return val ? [val] : [];
    };
    /**
     * Converts string to object with given property or returns the object if it is not a string
     * @param value Value from the config
     * @param propertyName Property name of the expected config object to which value will be assigned
     */
    const safeGetConfigObject = (value, propertyName) => {
        switch (typeof value) {
            case "string":
                const result = {};
                result[propertyName] = value;
                return result;
            case "object":
                // make a copy as the original one is immutable
                return Object.assign({}, value);
        }
        return value;
    };
    /**
     * Converts given date to localized string representation of relative time
     * @param hass Home Assistant instance
     * @param rawDate Date string
     */
    const getRelativeTime = (hass, rawDate) => {
        let time = Date.parse(rawDate);
        if (isNaN(time)) {
            return hass.localize("ui.components.relative_time.never");
        }
        time = Math.round((Date.now() - time) / 1000); // convert to seconds diff
        // https://github.com/yosilevy/home-assistant-polymer/blob/master/src/translations/en.json
        let relativeTime = "";
        if (time < 60) {
            relativeTime = hass.localize("ui.components.relative_time.past_duration.second", "count", time);
        }
        else if (time < 60 * 60) {
            relativeTime = hass.localize("ui.components.relative_time.past_duration.minute", "count", Math.round(time / 60));
        }
        else if (time < 60 * 60 * 24) {
            relativeTime = hass.localize("ui.components.relative_time.past_duration.hour", "count", Math.round(time / (60 * 60)));
        }
        else if (time < 60 * 60 * 24 * 7) {
            relativeTime = hass.localize("ui.components.relative_time.past_duration.day", "count", Math.round(time / (60 * 60 * 24)));
        }
        else {
            relativeTime = hass.localize("ui.components.relative_time.past_duration.week", "count", Math.round(time / (60 * 60 * 24 * 7)));
        }
        return relativeTime;
    };
    /**
     * Prefixes all css selectors with given value.
     * @param containerCssPath Prefix to be added
     * @param styles Styles to process
     */
    const processStyles = (containerCssPath, styles) => styles.replace(/([^\r\n,{}]+)(,(?=[^}]*{)|\s*{)/g, match => `${containerCssPath} ${match}`);
    /**
     * Throttles given function calls. In given throttle time always the last arriving call is executed.
     * @param func Function to call
     * @param throttleMs Number of ms to wait before calling
     */
    const throttledCall = function (func, throttleMs) {
        let timeoutHook;
        return ((...args) => {
            if (timeoutHook) {
                // cancel previous call
                clearTimeout(timeoutHook);
                timeoutHook = null;
            }
            // schedule new call
            timeoutHook = setTimeout(() => func.apply(null, args), 100);
        });
    };

    const header = (text) => html `<div class="card-header"><div class="truncate">${text}</div></div>`;
    const secondaryInfo = (text) => text && html `<div class="secondary">${text}</div>`;
    const icon = (icon, color) => icon && html `<div class="icon"><ha-icon style="color:${color}" icon="${icon}"></ha-icon></div>`;
    const soil = (model) => html `<div class="entity-row entity-spacing soil ${model.classNames}" @click="${model.action}">${icon(model.icon, model.levelColor)}<div class="name truncate">${model.name} ${secondaryInfo(model.secondary_info)}</div><div class="state">${model.level}${isNumber(model.level) ? html ` %` : ""}</div></div>`;
    const card = (headerText, contents) => {
        return html `<ha-card>${headerText ? header(headerText) : ""}<div class="card-content">${contents}</div></ha-card>`;
    };
    const collapsableWrapper = (contents, model) => {
        "expander" + Math.random().toString().substr(2);
        return html `<div class="expandWrapper entity-spacing"><div class="entity-row toggler" @click="${(e) => e.currentTarget.classList.toggle("expanded")}">${icon(model.icon, model.iconColor)}<div class="name truncate">${model.name} ${secondaryInfo(model.secondary_info)}</div><div class="chevron">‹</div></div><div style="max-height:${contents.length * 50}">${contents}</div></div>`;
    };
    const empty = () => html ``;

    const styles = css `.clickable{cursor:pointer}.truncate{white-space:nowrap;text-overflow:ellipsis;overflow:hidden}.entity-spacing{margin:8px 0}.entity-spacing:first-child{margin-top:0}.entity-spacing:last-child{margin-bottom:0}.entity-row{display:flex;align-items:center}.entity-row .name{flex:1;margin:0 6px}.entity-row .secondary{color:var(--secondary-text-color)}.entity-row .icon{flex:0 0 40px;border-radius:50%;text-align:center;line-height:40px;margin-right:10px}.expandWrapper>.toggler{cursor:pointer}.expandWrapper>.toggler>.name{flex:1}.expandWrapper>.toggler div.chevron{transform:rotate(-90deg);font-size:26px;height:40px;width:40px;display:flex;justify-content:center;align-items:center}.expandWrapper>.toggler .chevron,.expandWrapper>.toggler+div{transition:all .5s ease}.expandWrapper>.toggler.expanded .chevron{transform:rotate(-90deg) scaleX(-1)}.expandWrapper>.toggler+div{overflow:hidden}.expandWrapper>.toggler:not(.expanded)+div{max-height:0!important}`;

    const nameToFuncMap = {
        "more-info": (data) => {
            const evt = new Event('hass-more-info', { composed: true });
            evt.detail = { entityId: data.entity.entity };
            data.card.dispatchEvent(evt);
        },
        "navigate": (data) => {
            if (!data.config.navigation_path) {
                log("Missing 'navigation_path' for 'navigate' tap action");
                return;
            }
            window.history.pushState(null, "", data.config.navigation_path);
            const evt = new Event("location-changed", { composed: true });
            evt.detail = { replace: false };
            window.dispatchEvent(evt);
        },
        "call-service": (data) => {
            if (!data.config.service) {
                log("Missing 'service' for 'call-service' tap action");
                return;
            }
            const [domain, service] = data.config.service.split(".", 2);
            const serviceData = Object.assign({}, data.config.service_data);
            ActionFactory.hass.callService(domain, service, serviceData);
        },
        "url": data => {
            if (!data.config.url_path) {
                log("Missing 'url_path' for 'url' tap action");
                return;
            }
            window.location.href = data.config.url_path;
        }
    };
    /**
     * Helper class for creating actions - tap/click handlers.
     */
    class ActionFactory {
        /**
         * Returns action for given action data.
         *
         * @param data Action data object
         */
        static getAction(data) {
            if (!data.config || data.config.action == "none") {
                return null;
            }
            return evt => {
                evt.stopPropagation();
                if (!(data.config.action in nameToFuncMap)) {
                    log("Unknown tap action type: " + data.config.action);
                    return;
                }
                nameToFuncMap[data.config.action](data);
            };
        }
    }

    /**
     * soil view model.
     */
    class soilViewModel {
        /**
         * @param config soil entity
         */
        constructor(config, action) {
            this.config = config;
            this.action = action;
            this._level = "Unknown";
            this._fertilize_state = false;
            this._secondary_info = null;
            this._is_hidden = false;
            this.updated = false;
            this.colorPattern = /^#[A-Fa-f0-9]{6}$/;
            /**
             * Some sensor may produce string value like "45%". This regex is meant to parse such values.
             */
            this.stringValuePattern = /\b([0-9]{1,3})\s?%/;
            this._name = config.name || config.entity;
        }
        get entity_id() {
            return this.config.entity;
        }
        /**
         * List of entity ids for which data is required.
         */
        get data_required_for() {
            var _a;
            return ((_a = this.config.fertilize_state) === null || _a === void 0 ? void 0 : _a.entity_id) ?
                [this.config.entity, this.config.fertilize_state.entity_id] :
                [this.config.entity];
        }
        /**
         * Device name to display.
         */
        set name(name) {
            this.updated = this.updated || this._name != name;
            this._name = name;
        }
        /**
         * Device name to display.
         */
        get name() {
            let name = this._name;
            // since the getter is called only during rendering while setter always to check
            // if value has changed it is more efficient to apply rename here
            const renameRules = safeGetArray(this.config.bulk_rename);
            renameRules.forEach(r => {
                if (r.from[0] == "/" && r.from[r.from.length - 1] == "/") {
                    // create regexp after removing slashes
                    name = name.replace(new RegExp(r.from.substr(1, r.from.length - 2)), r.to || "");
                }
                else {
                    name = name.replace(r.from, r.to || "");
                }
            });
            return name;
        }
        /**
         * soil level.
         */
        set level(level) {
            this.updated = this.updated || this._level != level;
            this._level = level;
        }
        /**
         * soil level.
         */
        get level() {
            return this._level;
        }
        set fertilize_state(fertilize_state) {
            this.updated = this.updated || this.fertilize_state != fertilize_state;
            this._fertilize_state = fertilize_state;
        }
        get fertilize_state() {
            return this._fertilize_state;
        }
        get is_hidden() {
            return this._is_hidden;
        }
        set is_hidden(val) {
            this.updated = this.updated || this._is_hidden != val;
            this._is_hidden = val;
        }
        get secondary_info() {
            return this._secondary_info;
        }
        set secondary_info(val) {
            this.updated = this.updated || this._secondary_info != val;
            this._secondary_info = val;
        }
        /**
         * soil level color.
         */
        get levelColor() {
            var _a, _b;
            const defaultColor = "inherit";
            const level = Number(this._level);
            if (this.fertilize_state && ((_a = this.config.fertilize_state) === null || _a === void 0 ? void 0 : _a.color)) {
                return this.config.fertilize_state.color;
            }
            if (isNaN(level) || level > 150 || level < 0) {
                return defaultColor;
            }
            if (this.config.color_gradient && this.isColorGradientValid(this.config.color_gradient)) {
                return getColorInterpolationForPercentage(this.config.color_gradient, level);
            }
            const thresholds = this.config.color_thresholds ||
                [{ value: 20, color: "var(--label-badge-red)" }, { value: 55, color: "var(--label-badge-yellow)" }, { value: 101, color: "var(--label-badge-green)" }];
            return ((_b = thresholds.find(th => level <= th.value)) === null || _b === void 0 ? void 0 : _b.color) || defaultColor;
        }
        /**
         * Icon showing soil level/state.
         */
        get icon() {
            var _a;
            const level = Number(this._level);
            if (this.fertilize_state && ((_a = this.config.fertilize_state) === null || _a === void 0 ? void 0 : _a.icon)) {
                return this.config.fertilize_state.icon;
            }
            if (this.config.icon) {
                return this.config.icon;
            }
            if (isNaN(level) || level > 150 || level < 0) {
                return "mdi:mdi:water-off";
            }
            const roundedLevel = Math.round(level / 10) * 10;
            switch (roundedLevel) {
                case 150:
                    return this.fertilize_state ? 'mdi:water-check' : "mdi:water-check";
                case 140:
                    return this.fertilize_state ? 'mdi:water-check' : "mdi:water-check";
                case 130:
                    return this.fertilize_state ? 'mdi:water-check' : "mdi:water-check";
                case 120:
                    return this.fertilize_state ? 'mdi:water-check' : "mdi:water-check";
                case 110:
                    return this.fertilize_state ? 'mdi:water-check' : "mdi:water-check";
                case 100:
                    return this.fertilize_state ? 'mdi:water-check' : "mdi:water-check";
                case 0:
                    return this.fertilize_state ? 'mdi:water-alert' : "mdi:water-alert";
                default:
                    return this.fertilize_state ? "mdi:water-percent" : "mdi:water-percent";
                // return (this.soil ? "mdi:soil-soil-" : "mdi:soil-") + roundedLevel;
            }
        }
        get classNames() {
            const classNames = [];
            this.action && classNames.push("clickable");
            !isNumber(this.level) && classNames.push("non-numeric-state");
            return classNames.join(" ");
        }
        /**
         * Updates soil data.
         * @param entityData HA entity data
         */
        update(hass) {
            const entityData = hass.states[this.config.entity];
            if (!entityData) {
                log("Entity not found: " + this.config.entity, "error");
                return;
            }
            this.updated = false;
            this.name = this.config.name || entityData.attributes.friendly_name;
            this.level = this.getLevel(entityData, hass);
            // must be called after getting soil level
            this.fertilize_state = this.getfertilize_stateState(hass);
            // must be called after getting fertilize_state state
            this.secondary_info = this.setSecondaryInfo(hass, entityData);
        }
        /**
         * Gets soil level
         * @param entityData Entity state data
         */
        getLevel(entityData, hass) {
            var _a;
            const UnknownLevel = hass.localize("state.default.unknown");
            let level;
            if (this.config.attribute) {
                level = entityData.attributes[this.config.attribute];
                if (level == undefined) {
                    log(`Attribute "${this.config.attribute}" doesn't exist on "${this.config.entity}" entity`);
                    level = UnknownLevel;
                }
            }
            else {
                const candidates = [
                    entityData.attributes.soil_level,
                    entityData.attributes.soil,
                    entityData.state
                ];
                level = ((_a = candidates.find(n => n !== null && n !== undefined)) === null || _a === void 0 ? void 0 : _a.toString()) || UnknownLevel;
            }
            // check if we should convert value eg. for binary sensors
            if (this.config.state_map) {
                const convertedVal = this.config.state_map.find(s => s.from === level);
                if (convertedVal === undefined) {
                    if (!isNumber(level)) {
                        log(`Missing option for '${level}' in 'state_map'`);
                    }
                }
                else {
                    level = convertedVal.to.toString();
                }
            }
            if (!isNumber(level)) {
                const match = this.stringValuePattern.exec(level);
                if (match != null) {
                    level = match[1];
                }
            }
            if (this.config.multiplier && isNumber(level)) {
                level = (this.config.multiplier * Number(level)).toString();
            }
            // for dev/testing purposes we allow override for value
            level = this.config.value_override === undefined ? level : this.config.value_override;
            if (!isNumber(level)) {
                // capitalize first letter
                level = level.charAt(0).toUpperCase() + level.slice(1);
            }
            return level;
        }
        /**
         * Gets fertilize_state state if configuration specified.
         * @param entityDataList HA entity data
         */
        getfertilize_stateState(hass) {
            const fertilize_stateConfig = this.config.fertilize_state;
            if (!fertilize_stateConfig) {
                return false;
            }
            // take the state from the level property as it originate from various places
            let state = this.level;
            let entityWithfertilize_stateState = hass.states[this.config.entity];
            // check whether we should use different entity to get fertilize_state state
            if (fertilize_stateConfig.entity_id) {
                entityWithfertilize_stateState = hass.states[fertilize_stateConfig.entity_id];
                if (!entityWithfertilize_stateState) {
                    log(`'fertilize_state' entity id (${fertilize_stateConfig.entity_id}) not found`);
                    return false;
                }
                state = entityWithfertilize_stateState.state;
            }
            const attributesLookup = safeGetArray(fertilize_stateConfig.attribute);
            // check if we should take the state from attribute
            if (attributesLookup.length != 0) {
                // take first attribute name which exists on entity
                const exisitngAttrib = attributesLookup.find(attr => entityWithfertilize_stateState.attributes[attr.name] != undefined);
                if (exisitngAttrib) {
                    return exisitngAttrib.value != undefined ?
                        entityWithfertilize_stateState.attributes[exisitngAttrib.name] == exisitngAttrib.value :
                        true;
                }
                else {
                    // if there is no attribute indicating fertilize_state it means the fertilize_state state is false
                    return false;
                }
            }
            const statesIndicatingfertilize_state = safeGetArray(fertilize_stateConfig.state);
            return statesIndicatingfertilize_state.length == 0 ? !!state : statesIndicatingfertilize_state.some(s => s == state);
        }
        /**
         * Gets secondary info
         * @param hass Home Assistant instance
         * @param entityData Entity state data
         */
        setSecondaryInfo(hass, entityData) {
            var _a;
            if (this.config.secondary_info) {
                if (this.config.secondary_info == "needed") {
                    //    alert("secondary 2nd if");
                    if (this.fertilize_state) {
                        //        alert("secondary 3rd if");
                        return ((_a = this.config.fertilize_state) === null || _a === void 0 ? void 0 : _a.secondary_info_text) || "Det ville være smart at gøde"; // todo: think about i18n
                    }
                    //    alert("secondary first if");
                    return null;
                }
                else {
                    //    alert("secondary ELSE");
                    //    alert(this.config.secondary_info);
                    const val = entityData[this.config.secondary_info] || entityData.attributes[this.config.secondary_info] || this.config.secondary_info;
                    return isNaN(Date.parse(val)) ? val : getRelativeTime(hass, val);
                }
            }
            return null;
        }
        /**
         * Validates if given color values are correct
         * @param color_gradient List of color values to validate
         */
        isColorGradientValid(color_gradient) {
            if (color_gradient.length < 2) {
                log("Value for 'color_gradient' should be an array with at least 2 colors.");
                return;
            }
            for (const color of color_gradient) {
                if (!this.colorPattern.test(color)) {
                    log("Color '${color}' is not valid. Please provide valid HTML hex color in #XXXXXX format.");
                    return false;
                }
            }
            return true;
        }
    }

    /**
     * Returns soil collections to render
     * @param config Collapsing config
     * @param soils soil view models
     * @param haGroupData Home assistant group data
     */
    const getsoilCollections = (config, soils, haGroupData) => {
        const result = {
            soils: [],
            groups: []
        };
        if (!config) {
            result.soils = soils;
            return result;
        }
        if (typeof config == "number") {
            let visiblesoils = soils.filter(b => !b.is_hidden);
            result.soils = visiblesoils.slice(0, config);
            result.groups.push(createGroup(haGroupData, visiblesoils.slice(config)));
        }
        else { // make sure that max property is set for every group
            populateMinMaxFields(config);
            soils.forEach(b => {
                const foundIndex = getGroupIndex(config, b, haGroupData);
                if (foundIndex == -1) {
                    // soils without group
                    result.soils.push(b);
                }
                else {
                    // bumping group index as the first group is for the orphans
                    result.groups[foundIndex] = result.groups[foundIndex] || createGroup(haGroupData, [], config[foundIndex]);
                    result.groups[foundIndex].soils.push(b);
                }
            });
        }
        // update group name and secondary info / replace keywords with values
        result.groups.forEach(g => {
            if (g.name) {
                g.name = getEnrichedText(g.name, g);
            }
            if (g.secondary_info) {
                g.secondary_info = getEnrichedText(g.secondary_info, g);
            }
        });
        return result;
    };
    /**
     * Returns group index to which soil should be assigned.
     * @param config Collapsing groups config
     * @param soil Batterry view model
     * @param haGroupData Home assistant group data
     */
    const getGroupIndex = (config, soil, haGroupData) => {
        return config.findIndex(group => {
            var _a, _b;
            if (group.group_id && !((_b = (_a = haGroupData[group.group_id]) === null || _a === void 0 ? void 0 : _a.entity_id) === null || _b === void 0 ? void 0 : _b.some(id => soil.entity_id == id))) {
                return false;
            }
            if (group.entities && !group.entities.some(id => soil.entity_id == id)) {
                return false;
            }
            const level = isNaN(Number(soil.level)) ? 0 : Number(soil.level);
            return level >= group.min && level <= group.max;
        });
    };
    /**
     * Sets missing max/min fields.
     * @param config Collapsing groups config
     */
    var populateMinMaxFields = (config) => config.forEach(groupConfig => {
        if (groupConfig.min == undefined) {
            groupConfig.min = 0;
        }
        if (groupConfig.max != undefined && groupConfig.max < groupConfig.min) {
            log("Collapse group min value should be lower than max.\n" + JSON.stringify(groupConfig, null, 2));
            return;
        }
        if (groupConfig.max == undefined) {
            groupConfig.max = 100;
        }
    });
    /**
     * Creates and returns group view data object.
     * @param haGroupData Home assistant group data
     * @param soils Batterry view model
     * @param config Collapsing group config
     */
    const createGroup = (haGroupData, soils = [], config) => {
        if ((config === null || config === void 0 ? void 0 : config.group_id) && !haGroupData[config.group_id]) {
            throw new Error("Group not found: " + config.group_id);
        }
        let name = config === null || config === void 0 ? void 0 : config.name;
        if (!name && (config === null || config === void 0 ? void 0 : config.group_id)) {
            name = haGroupData[config.group_id].friendly_name;
        }
        let icon = config === null || config === void 0 ? void 0 : config.icon;
        if (icon === undefined && (config === null || config === void 0 ? void 0 : config.group_id)) {
            icon = haGroupData[config.group_id].icon;
        }
        return {
            name: name,
            icon: icon,
            soils: soils,
            secondary_info: config === null || config === void 0 ? void 0 : config.secondary_info
        };
    };
    /**
     * Replaces all keywords, used in the text, with values
     * @param text Text to process
     * @param group soil group view data
     */
    const getEnrichedText = (text, group) => {
        text = text.replace(/\{[a-z]+\}/g, keyword => {
            switch (keyword) {
                case "{min}":
                    return group.soils.reduce((agg, b) => agg > Number(b.level) ? Number(b.level) : agg, 100).toString();
                case "{max}":
                    return group.soils.reduce((agg, b) => agg < Number(b.level) ? Number(b.level) : agg, 0).toString();
                case "{count}":
                    return group.soils.length.toString();
                case "{range}":
                    const min = group.soils.reduce((agg, b) => agg > Number(b.level) ? Number(b.level) : agg, 100).toString();
                    const max = group.soils.reduce((agg, b) => agg < Number(b.level) ? Number(b.level) : agg, 0).toString();
                    return min == max ? min : min + "-" + max;
                default:
                    return keyword;
            }
        });
        return text;
    };

    /**
     * Properties which should be copied over to individual entities from the card
     */
    const entititesGlobalProps = ["tap_action", "state_map", "fertilize_state", "secondary_info", "color_thresholds", "color_gradient", "bulk_rename", "icon"];
    const regExpPattern = /\/([^/]+)\/([igmsuy]*)/;
    /**
     * Functions to check if filter condition is met
     */
    const operatorHandlers = {
        "exists": val => val !== undefined,
        "contains": (val, searchString) => val !== undefined && val.toString().indexOf(searchString.toString()) != -1,
        "=": (val, expectedVal) => val == expectedVal,
        ">": (val, expectedVal) => Number(val) > expectedVal,
        "<": (val, expectedVal) => Number(val) < expectedVal,
        ">=": (val, expectedVal) => Number(val) >= expectedVal,
        "<=": (val, expectedVal) => Number(val) <= expectedVal,
        "matches": (val, pattern) => {
            if (val === undefined) {
                return false;
            }
            pattern = pattern.toString();
            let exp;
            const regexpMatch = pattern.match(regExpPattern);
            if (regexpMatch) {
                // create regexp after removing slashes
                exp = new RegExp(regexpMatch[1], regexpMatch[2]);
            }
            else if (pattern.indexOf("*") != -1) {
                exp = new RegExp("^" + pattern.replace(/\*/g, ".*") + "$");
            }
            return exp ? exp.test(val.toString()) : val === pattern;
        }
    };
    /**
     * Filter class
     */
    class Filter {
        constructor(config) {
            this.config = config;
        }
        /**
         * Whether filter is permanent.
         *
         * Permanent filters removes entities/soils from collections permanently
         * instead of making them hidden.
         */
        get is_permanent() {
            return this.config.name != "state";
        }
        /**
         * Checks whether entity meets the filter conditions.
         * @param entity Hass entity
         * @param state State override - soil state/level
         */
        isValid(entity, state) {
            const val = this.getValue(entity, state);
            return this.meetsExpectations(val);
        }
        /**
         * Gets the value to validate.
         * @param entity Hass entity
         * @param state State override - soil state/level
         */
        getValue(entity, state) {
            if (!this.config.name) {
                log("Missing filter 'name' property");
                return;
            }
            if (this.config.name.indexOf("attributes.") == 0) {
                return entity.attributes[this.config.name.substr(11)];
            }
            if (this.config.name == "state" && state !== undefined) {
                return state;
            }
            return entity[this.config.name];
        }
        /**
         * Checks whether value meets the filter conditions.
         * @param val Value to validate
         */
        meetsExpectations(val) {
            let operator = this.config.operator;
            if (!operator) {
                if (this.config.value === undefined) {
                    operator = "exists";
                }
                else {
                    const expectedVal = this.config.value.toString();
                    operator = expectedVal.indexOf("*") != -1 || (expectedVal[0] == "/" && expectedVal[expectedVal.length - 1] == "/") ?
                        "matches" :
                        "=";
                }
            }
            const func = operatorHandlers[operator];
            if (!func) {
                log(`Operator '${this.config.operator}' not supported. Supported operators: ${Object.keys(operatorHandlers).join(", ")}`);
                return false;
            }
            return func(val, this.config.value);
        }
    }
    /**
     * Class responsible for intializing soil view models based on given configuration.
     */
    class soilProvider {
        constructor(config, cardNode) {
            var _a, _b, _c, _d;
            this.config = config;
            this.cardNode = cardNode;
            /**
             * soil view models.
             */
            this.soils = [];
            /**
             * Groups to be resolved on HA state update.
             */
            this.groupsToResolve = [];
            /**
             * Collection of groups and their properties taken from HA
             */
            this.groupsData = {};
            /**
             * Whether include filters were processed already.
             */
            this.initialized = false;
            this.include = (_b = (_a = config.filter) === null || _a === void 0 ? void 0 : _a.include) === null || _b === void 0 ? void 0 : _b.map(f => new Filter(f));
            this.exclude = (_d = (_c = config.filter) === null || _c === void 0 ? void 0 : _c.exclude) === null || _d === void 0 ? void 0 : _d.map(f => new Filter(f));
            if (!this.include) {
                this.initialized = false;
            }
            this.processExplicitEntities();
        }
        update(hass) {
            let updated = false;
            if (!this.initialized) {
                // groups and includes should be processed just once
                this.initialized = true;
                updated = this.processGroups(hass) || updated;
                updated = this.processIncludes(hass) || updated;
            }
            updated = this.updatesoils(hass) || updated;
            if (updated) {
                this.processExcludes(hass);
            }
            return updated;
        }
        /**
         * Return soils
         * @param hass Home Assistant instance
         */
        getsoils() {
            return getsoilCollections(this.config.collapse, this.soils, this.groupsData);
        }
        /**
         * Creates and returns new soil View Model
         */
        createsoil(entity) {
            // assing card-level values if they were not defined on entity-level
            entititesGlobalProps
                .filter(p => entity[p] == undefined)
                .forEach(p => entity[p] = this.config[p]);
            return new soilViewModel(entity, ActionFactory.getAction({
                card: this.cardNode,
                config: safeGetConfigObject(entity.tap_action || this.config.tap_action || null, "action"),
                entity: entity
            }));
        }
        /**
         * Adds soils based on entities from config.
         */
        processExplicitEntities() {
            let entities = this.config.entity
                ? [this.config]
                : (this.config.entities || []).map((entity) => {
                    // check if it is just the id string
                    if (typeof (entity) === "string") {
                        entity = { entity: entity };
                    }
                    return entity;
                });
            // remove groups to add them later
            entities = entities.filter(e => {
                if (!e.entity) {
                    throw new Error("Invalid configuration - missing property 'entity' on:\n" + JSON.stringify(e));
                }
                if (e.entity.startsWith("group.")) {
                    this.groupsToResolve.push(e.entity);
                    return false;
                }
                return true;
            });
            // processing groups and entities from collapse property
            // this way user doesn't need to put same IDs twice in the configuration
            if (this.config.collapse && Array.isArray(this.config.collapse)) {
                this.config.collapse.forEach(group => {
                    if (group.group_id) {
                        // check if it's not there already
                        if (this.groupsToResolve.indexOf(group.group_id) == -1) {
                            this.groupsToResolve.push(group.group_id);
                        }
                    }
                    else if (group.entities) {
                        group.entities.forEach(entity_id => {
                            // check if it's not there already
                            if (!entities.some(e => e.entity == entity_id)) {
                                entities.push({ entity: entity_id });
                            }
                        });
                    }
                });
            }
            this.soils = entities.map(entity => this.createsoil(entity));
        }
        /**
         * Adds soils based on filter.include config.
         * @param hass Home Assistant instance
         */
        processIncludes(hass) {
            let updated = false;
            if (!this.include) {
                return updated;
            }
            Object.keys(hass.states).forEach(entity_id => {
                var _a;
                // check if entity matches filter conditions
                if (((_a = this.include) === null || _a === void 0 ? void 0 : _a.some(filter => filter.isValid(hass.states[entity_id]))) &&
                    // check if soil is not added already (via explicit entities)
                    !this.soils.some(b => b.entity_id == entity_id)) {
                    updated = true;
                    this.soils.push(this.createsoil({ entity: entity_id }));
                }
            });
            return updated;
        }
        /**
         * Adds soils from group entities (if they were on the list)
         * @param hass Home Assistant instance
         */
        processGroups(hass) {
            let updated = false;
            this.groupsToResolve.forEach(group_id => {
                const groupEntity = hass.states[group_id];
                if (!groupEntity) {
                    log(`Group "${group_id}" not found`);
                    return;
                }
                const groupData = groupEntity.attributes;
                if (!Array.isArray(groupData.entity_id)) {
                    log(`Entities not found in "${group_id}"`);
                    return;
                }
                groupData.entity_id.forEach(entity_id => {
                    // check if soil is on the list already
                    if (this.soils.some(b => b.entity_id == entity_id)) {
                        return;
                    }
                    updated = true;
                    this.soils.push(this.createsoil({ entity: entity_id }));
                });
                this.groupsData[group_id] = groupData;
            });
            this.groupsToResolve = [];
            return updated;
        }
        /**
         * Removes or hides soils based on filter.exclude config.
         * @param hass Home Assistant instance
         */
        processExcludes(hass) {
            if (this.exclude == undefined) {
                return;
            }
            const filters = this.exclude;
            const toBeRemoved = [];
            this.soils.forEach((soil, index) => {
                let is_hidden = false;
                for (let filter of filters) {
                    // passing HA entity state together with VM soil level as the source of this value can vary
                    if (filter.isValid(hass.states[soil.entity_id], soil.level)) {
                        if (filter.is_permanent) {
                            // permanent filters have conditions based on static values so we can safely
                            // remove such soil to avoid updating it unnecessarily
                            toBeRemoved.push(index);
                        }
                        else {
                            is_hidden = true;
                        }
                    }
                }
                // we keep the view model to keep updating it
                // it might be shown/not-hidden next time
                soil.is_hidden = is_hidden;
            });
            // we need to reverse otherwise the indexes will be messed up after removing
            toBeRemoved.reverse().forEach(i => this.soils.splice(i, 1));
        }
        /**
         * Updates soil view models based on HA states.
         * @param hass Home Assistant instance
         */
        updatesoils(hass) {
            let updated = false;
            this.soils.forEach((soil, index) => {
                soil.update(hass);
                updated = updated || soil.updated;
            });
            if (updated) {
                switch (this.config.sort_by_level) {
                    case "asc":
                        this.soils.sort((a, b) => this.sort(a.level, b.level));
                        break;
                    case "desc":
                        this.soils.sort((a, b) => this.sort(b.level, a.level));
                        break;
                    default:
                        if (this.config.sort_by_level) {
                            log("Unknown sort option. Allowed values: 'asc', 'desc'");
                        }
                }
                // trigger the UI update
                this.soils = [...this.soils];
            }
            return updated;
        }
        /**
         * Sorting function for soil levels which can have "Unknown" state.
         * @param a First value
         * @param b Second value
         */
        sort(a, b) {
            let aNum = Number(a);
            let bNum = Number(b);
            aNum = isNaN(aNum) ? -1 : aNum;
            bNum = isNaN(bNum) ? -1 : bNum;
            return aNum - bNum;
        }
    }

    /**
     * Card main class.
     */
    class soilStateCard extends LitElement {
        constructor() {
            super(...arguments);
            /**
             * Raw config used to check if there were changes.
             */
            this.rawConfig = "";
            /**
             * Card configuration.
             */
            this.config = {};
            /**
             * Whether we should render it as an entity - not a card.
             */
            this.simpleView = false;
            /**
             * soil provider for soil view models.
             */
            this.soilProvider = null;
            /**
             * Custom styles comming from config.
             */
            this.cssStyles = "";
            /**
             * Triggers rendering in a safe way
             *
             * @description Overtriggering UI update can cause rendering issues (see #111)
             */
            this.triggerRender = throttledCall(() => this.requestUpdate());
        }
        /**
         * CSS for the card
         */
        static get styles() {
            return styles;
        }
        /**
         * Called by HA on init or when configuration is updated.
         *
         * @param config Card configuration
         */
        setConfig(config) {
            var _a;
            if (!config.entities &&
                !config.entity &&
                !((_a = config.filter) === null || _a === void 0 ? void 0 : _a.include) &&
                !Array.isArray(config.collapse)) {
                throw new Error("You need to define entities, filter.include or collapse.group");
            }
            // check for changes
            const rawConfig = JSON.stringify(config);
            if (this.rawConfig === rawConfig) {
                // no changes so stop processing
                return;
            }
            this.rawConfig = rawConfig;
            // config is readonly and we want to apply default values so we need to recreate it
            this.config = JSON.parse(rawConfig);
            this.simpleView = !!this.config.entity;
            this.soilProvider = new soilProvider(this.config, this);
            // rendering in case we won't get state update
            this.triggerRender();
        }
        /**
         * Called when HA state changes (very often).
         */
        set hass(hass) {
            ActionFactory.hass = hass;
            const updated = this.soilProvider.update(hass);
            if (updated) {
                this.triggerRender();
            }
        }
        /**
         * Renders the card. Called when update detected.
         */
        render() {
            const viewData = this.soilProvider.getsoils();
            // check if we should render it without card container
            if (this.simpleView) {
                return soil(viewData.soils[0]);
            }
            let renderedViews = [];
            viewData.soils.forEach(b => !b.is_hidden && renderedViews.push(soil(b)));
            viewData.groups.forEach(g => {
                const renderedsoils = [];
                g.soils.forEach(b => !b.is_hidden && renderedsoils.push(soil(b)));
                if (renderedsoils.length) {
                    renderedViews.push(collapsableWrapper(renderedsoils, g));
                }
            });
            if (renderedViews.length == 0) {
                return empty();
            }
            return card(this.config.name || this.config.title, renderedViews);
        }
        /**
         * Called just after the update is finished (including rendering)
         */
        updated() {
            var _a;
            if (!((_a = this.config) === null || _a === void 0 ? void 0 : _a.style) || this.cssStyles == this.config.style) {
                return;
            }
            this.cssStyles = this.config.style;
            let styleElem = this.shadowRoot.querySelector("style");
            if (!styleElem) {
                styleElem = document.createElement("style");
                styleElem.type = 'text/css';
                this.shadowRoot.appendChild(styleElem);
            }
            // prefixing all selectors
            styleElem.innerHTML = processStyles("ha-card", this.cssStyles);
        }
        /**
         * Gets the height of your card.
         *
         * Home Assistant uses this to automatically distribute all cards over
         * the available columns. One is equal 50px.
         */
        getCardSize() {
            var _a;
            let size = ((_a = this.config.entities) === null || _a === void 0 ? void 0 : _a.length) || 1;
            if (this.config.collapse) {
                if (typeof this.config.collapse == "number") {
                    // +1 to account the expand button
                    return this.config.collapse + 1;
                }
                else {
                    return this.config.collapse.length + 1;
                }
            }
            // +1 to account header
            return size + 1;
        }
    }
    // Registering card
    customElements.define("soil-state-card", soilStateCard);

}());
//# sourceMappingURL=soil-state-card.js.map
