<template>
  <div :id="`${tabName}_tab`" v-if="tab_info">
    <h5
      class="errorHeading"
      v-if="$store.state.form.tabs.questionaire_questions.form_fields[tabName].selected === false && tab_info.form_fields.length"
    >Please note that submitting the form is not allowed as long as the selected answer for this section in the questionnare is "No"</h5>
    <div class="form-sections">
      <div class="table-wrapper">
        <div class="table-title">
          <h6>
            <span v-translate>Substances</span>
          </h6>
          <b-btn class="mr-3" variant="outline-danger" @click="bulkRemove(selectedForDelete)" v-if="selectedForDelete.length">
            <span><span v-translate>Delete</span>&nbsp;{{selectedForDelete.length}}&nbsp;<span v-translate>selected rows</span></span>
          </b-btn>
          <div v-show="table.tableFilters" class="table-filters">
            <b-input-group :prepend="$gettext('Filter')">
              <b-form-input :class="{ highlighted: table.filters.search && table.filters.search.length }"  v-model="table.filters.search"/>
            </b-input-group>
          </div>
          <i @click="table.tableFilters = !table.tableFilters" class="fa fa-filter fa-lg"></i>
        </div>

        <b-table
          show-empty
          outlined
          v-if="getTabInputFields && getTabDecisionQuantityFields"
          bordered
          hover
          head-variant="light"
          stacked="md"
          class="submission-table full-bordered"
          id="substance-table"
          :items="tableItems"
          :fields="tableFields"
          :empty-text="tableEmptyText"
          :filter="table.filters.search"
          ref="table"
        >

          <template v-for="field in tableFields" v-slot:[`head(${field.key})`]="field">
            <div :style="`width: ${field.width ? field.width + 'px' : 'auto'}`" v-html="field.label" :key="field.key"></div>
          </template>

          <template v-slot:thead-top>
            <tr class="first-header">
              <th
                v-for="(header, header_index) in tab_info.section_headers"
                :colspan="header.colspan"
                :key="header_index"
              >
                <div
                  v-if="header.tooltip"
                  v-b-tooltip.hover
                  placement="left"
                  :title="header.tooltip"
                >
                  <span v-html="header.label"></span>
                  <i class="fa fa-info-circle fa-lg"></i>
                </div>
                <div v-else>
                  <span v-html="header.label"></span>
                </div>
              </th>
            </tr>
          </template>

          <template v-slot:cell(group)="cell">
            <div class="group-cell">{{cell.item.group}}</div>
          </template>
          <template v-slot:cell(substance)="cell">
            <div class="substance-blend-cell">{{cell.item.substance}}</div>
          </template>

          <template v-slot:[`cell(${getCountrySlot})`]="cell">
            <CloneField
              :key="`${cell.item.index}_${getCountrySlot}_${tabName}`"
              v-on:removeThisField="remove_field(cell.item.index, cell.item.originalObj)"
              v-if="!cell.item[getCountrySlot] && canEditSubstanceData"
              :tabName="tabName"
              :current_field="cell.item.originalObj"
            />
            <div class="country-cell" v-else>{{cell.item[getCountrySlot]}}</div>
          </template>

          <template v-for="inputField in getTabInputFields"  v-slot:[`cell(${inputField})`]="cell">
            <fieldGenerator
              :key="`${cell.item.index}_${inputField}_${tabName}`"
              :fieldInfo="{index:cell.item.index,tabName: tabName, field:inputField}"
              :disabled="isSubstanceDataReadOnly(inputField)"
              :field="cell.item.originalObj[inputField]"
            />
          </template>

          <template v-slot:cell(checkForDelete)="cell">
            <fieldGenerator
              v-show="!isActionReadOnly('delete', 'substance_data')"
              :fieldInfo="{index:cell.item.index,tabName: tabName, field:'checkForDelete'}"
              :field="cell.item.originalObj.checkForDelete"
            />
          </template>

          <template v-slot:cell(validation)="cell">
            <b-btn-group class="row-controls">
              <span  @click="createModalData(cell.item.originalObj, cell.item.index)">
                <i
                  :class="{
                    'fa-pencil-square-o': !isActionReadOnly('edit', 'substance_data'),
                    'fa-eye': !isActionReadOnly('view', 'substance_data'),
                    'fa fa-lg': true
                  }"
                  :title="!isActionReadOnly('edit', 'substance_data') ? $gettext('Edit') : $gettext('View')"
                  v-b-tooltip
                ></i>
              </span>
              <span
                v-if="!isActionReadOnly('delete', 'substance_data')"
                @click="remove_field(cell.item.index)"
                class="table-btn"
              >
                <i class="fa fa-trash fa-lg" v-b-tooltip :title="$gettext('Delete')"></i>
              </span>
              <ValidationLabel
                :open-validation-callback="openValidation"
                :validation="cell.item.originalObj.validation.selected"
                :index="cell.item.index"
              />
            </b-btn-group>
          </template>

          <template
            v-for="tooltipField in getTabDecisionQuantityFields"
            v-slot:[`cell(${tooltipField})`]="cell"
          >
            <div
              class="edit-trigger"
              v-b-tooltip.hover="cell.item.originalObj[tooltipField].tooltip ? true : false"
              :title="cell.item.originalObj[tooltipField].tooltip"
              :key="tooltipField"
              @click="createModalData(cell.item.originalObj, cell.item.index)"
            >
              <span
                class="input"
                :class="{'text-right': tooltipField === 'quantity_exempted'}"
              >
                {{formatQuantity(cell.item[tooltipField])}}
                <i v-if="cell.item[tooltipField]" class="fa fa-info-circle fa-sm"></i>
              </span>
            </div>
            <div
              style="position: relative;z-index: 1; margin-top: 1rem"
              class="special-field"
              v-if="isQps.includes(parseInt(cell.item.originalObj.substance.selected))"
              :key="`${tooltipField}_qps`"
            >
              <b-input-group v-if="tooltipField === 'quantity_exempted'">
                <b-input-group-prepend>
                  <span class="input-group-text"
                    :id="`qps_tooltip_${cell.item.index}`"
                  >
                    QPS <i class="fa fa-info-circle fa-sm"></i>
                  </span>
                    <b-tooltip :target="`qps_tooltip_${cell.item.index}`" placement="bottom">
                      <span
                        v-translate="{qps_word: qps_word, substance: tab_data.display.substances[cell.item.originalObj.substance.selected], production: qps_production}">
                        Quantity of new %{substance} %{qps_word} to be used for QPS applications within your country %{production}
                      </span>
                    </b-tooltip>
                </b-input-group-prepend>
                <fieldGenerator
                  :fieldInfo="{index:cell.item.index,tabName: tabName, field:'quantity_quarantine_pre_shipment'}"
                  :disabled="!canEditSubstanceData"
                  :field="cell.item.originalObj.quantity_quarantine_pre_shipment"
                />
              </b-input-group>
              <b-input-group v-if="tooltipField === 'decision_exempted'">
                <b-input-group-prepend>
                  <span class="input-group-text" v-translate>
                    Remark
                  </span>
                </b-input-group-prepend>
                <fieldGenerator
                  :fieldInfo="{index:cell.item.index,tabName: tabName, field:'decision_quarantine_pre_shipment'}"
                  :disabled="!canEditSubstanceData"
                  :field="cell.item.originalObj.decision_quarantine_pre_shipment"
                />
              </b-input-group>
            </div>

            <div
              style="position: relative;z-index: 1; margin-top: 1rem"
              class="special-field"
              v-if="isPolyols.includes(parseInt(cell.item.originalObj.substance.selected))"
              :key="`${tooltipField}_polyols`"
            >
              <b-input-group v-if="tooltipField === 'quantity_exempted'">
                <b-input-group-prepend>
                  <span
                    class="input-group-text"
                    :id="`polyols_tooltip_${cell.item.index}`"
                  >
                    Contained in polyols<i class="fa fa-info-circle fa-sm"></i>
                  </span>
                    <b-tooltip :target="`polyols_tooltip_${cell.item.index}`" placement="bottom">
                      <span v-translate>
                        Amounts contained in pre-blended polyols, not to be included in the amount of total imports
                      </span>
                    </b-tooltip>
                </b-input-group-prepend>
                <fieldGenerator
                  :fieldInfo="{index:cell.item.index,tabName: tabName, field:'quantity_polyols'}"
                  :disabled="!canEditSubstanceData"
                  :field="cell.item.originalObj.quantity_polyols"
                />
              </b-input-group>
              <b-input-group v-if="tooltipField === 'decision_exempted'">
                <b-input-group-prepend>
                  <span class="input-group-text" v-translate>
                    Remark
                  </span>
                </b-input-group-prepend>
                <fieldGenerator
                  :fieldInfo="{index:cell.item.index,tabName: tabName, field:'decision_polyols'}"
                  :disabled="!canEditSubstanceData"
                  :field="cell.item.originalObj.decision_polyols"
                />
              </b-input-group>
            </div>

          </template>
        </b-table>
      </div>
      <div v-if="tabName === 'has_produced'" class="table-wrapper">
        <div class="table-title">
          <h6>
            <span v-translate>HFC-23</span>
          </h6>
          <b-btn class="mr-3" variant="outline-danger" @click="bulkRemove(selectedForDeleteFII)" v-if="selectedForDeleteFII.length">
            <span><span v-translate>Delete</span>&nbsp;{{selectedForDeleteFII.length}}&nbsp;<span v-translate>selected rows</span></span>
          </b-btn>
          <div v-show="tableFII.tableFilters" class="table-filters">
            <b-input-group :prepend="$gettext('Filter')">
              <b-form-input :class="{ highlighted: tableFII.filters.search && tableFII.filters.search.length }" v-model="tableFII.filters.search"/>
            </b-input-group>
          </div>
          <i @click="tableFII.tableFilters = !tableFII.tableFilters" class="fa fa-filter fa-lg"></i>
        </div>

        <b-table
          id="fii-table"
          show-empty
          outlined
          bordered

          hover
          head-variant="light"
          stacked="md"
          class="submission-table full-bordered"
          :items="tableItemsFII"
          :fields="tableFieldsFII"
          :empty-text="tableFIIEmptyText"
          :filter="tableFII.filters.search"
          ref="tableFII"
        >
          <template v-for="field in tableFieldsFII" v-slot:[`head(${field.key})`]="field">
            <div :style="`width: ${field.width ? field.width + 'px' : 'auto'}`" v-html="field.label" :key="field.key"></div>
          </template>
          <template v-slot:thead-top>
            <tr class="first-header">
              <th
                v-for="(header, header_index) in tab_info.special_headers.section_headers"
                :colspan="header.colspan"
                :key="header_index"
              >
                <div
                  v-if="header.tooltip"
                  v-b-tooltip.hover
                  placement="left"
                  :title="header.tooltip"
                >
                  <span v-html="header.label"></span>
                  <i class="fa fa-info-circle fa-lg"></i>
                </div>
                <div v-else>
                  <span v-html="header.label"></span>
                </div>
              </th>
            </tr>
          </template>

          <template v-slot:cell(group)="cell">
            <div class="group-cell">{{cell.item.group}}</div>
          </template>

          <template v-slot:cell(substance)="cell">
            <div class="substance-blend-cell">{{cell.item.substance}}</div>
          </template>

          <template v-slot:cell(checkForDelete)="cell">
            <fieldGenerator
              v-show="!isActionReadOnly('delete', 'substance_data')"
              :fieldInfo="{index:cell.item.index,tabName: tabName, field:'checkForDelete'}"
              :field="cell.item.originalObj.checkForDelete"
            />
          </template>

          <template
            v-for="inputField in getTabSpecialInputFields"
            v-slot:[`cell(${inputField})`]="cell"
          >
            <fieldGenerator
              :key="`${cell.item.index}_${inputField}_${tabName}`"
              :fieldInfo="{index:cell.item.index,tabName: tabName, field:inputField}"
              :disabled="!canEditSubstanceData"
              :field="cell.item.originalObj[inputField]"
            />
          </template>

          <template v-slot:cell(validation)="cell">
            <b-btn-group class="row-controls">
              <span  @click="createModalData(cell.item.originalObj, cell.item.index)">
                <i
                    :class="{
                      'fa-pencil-square-o': !isActionReadOnly('edit', 'substance_data'),
                      'fa-eye': !isActionReadOnly('view', 'substance_data'),
                      'fa fa-lg': true
                    }"
                    :title="!isActionReadOnly('edit', 'substance_data') ? $gettext('Edit') : $gettext('View')"
                    v-b-tooltip
                ></i>
              </span>
              <span
                v-if="!isActionReadOnly('delete', 'substance_data')"
                @click="remove_field(cell.item.index)"
                class="table-btn"
              >
                <i class="fa fa-trash fa-lg" v-b-tooltip :title="$gettext('Delete')"></i>
              </span>
              <ValidationLabel
                :open-validation-callback="openValidation"
                :validation="cell.item.originalObj.validation.selected"
                :index="cell.item.index"
              />
            </b-btn-group>
          </template>

          <template
            v-for="tooltipField in getTabDecisionQuantityFields"
            v-slot:[`cell(${tooltipField})`]="cell"
          >
            <div
              class="edit-trigger"
              v-b-tooltip.hover="cell.item.originalObj[tooltipField].tooltip ? true : false"
              :title="cell.item.originalObj[tooltipField].tooltip"
              :key="tooltipField"
              @click="createModalData(cell.item.originalObj, cell.item.index)"
            >
              <span
                class="input"
                :class="{'text-right': tooltipField === 'quantity_exempted'}"
              >
                {{formatQuantity(cell.item[tooltipField])}}
                <i v-if="cell.item[tooltipField]" class="fa fa-info-circle fa-sm"></i>
              </span>
            </div>
            <div
              style="position: relative;z-index: 1; margin-top: 1rem"
              class="special-field"
              v-if="isQps.includes(parseInt(cell.item.originalObj.substance.selected))"
              :key="`${tooltipField}_qps`"
            >
              <b-input-group v-if="tooltipField === 'quantity_exempted'">
                <b-input-group-prepend>
                  <span class="input-group-text"
                    :id="`qps_tooltip_${cell.item.index}`"
                  >
                    QPS <i class="fa fa-info-circle fa-sm"></i>
                  </span>
                    <b-tooltip :target="`qps_tooltip_${cell.item.index}`" placement="bottom">
                      <span
                        v-translate="{qps_word: qps_word, substance: tab_data.display.substances[cell.item.originalObj.substance.selected], production: qps_production}">
                        Quantity of new %{substance} %{qps_word} to be used for QPS applications within your country %{production}
                      </span>
                    </b-tooltip>
                </b-input-group-prepend>
                <fieldGenerator
                  :fieldInfo="{index:cell.item.index,tabName: tabName, field:'quantity_quarantine_pre_shipment'}"
                  :disabled="!canEditSubstanceData"
                  :field="cell.item.originalObj.quantity_quarantine_pre_shipment"
                />
              </b-input-group>
              <b-input-group v-if="tooltipField === 'decision_exempted'">
                <b-input-group-prepend>
                  <span class="input-group-text" v-translate>
                    Remark
                  </span>
                </b-input-group-prepend>
                <fieldGenerator
                  :fieldInfo="{index:cell.item.index,tabName: tabName, field:'decision_quarantine_pre_shipment'}"
                  :disabled="!canEditSubstanceData"
                  :field="cell.item.originalObj.decision_quarantine_pre_shipment"
                />
              </b-input-group>
            </div>

            <div
              style="position: relative;z-index: 1; margin-top: 1rem"
              class="special-field"
              v-if="isPolyols.includes(parseInt(cell.item.originalObj.substance.selected))"
              :key="`${tooltipField}_polyols`"
            >
              <b-input-group v-if="tooltipField === 'quantity_exempted'">
                <b-input-group-prepend>
                  <span
                    class="input-group-text"
                    :id="`polyols_tooltip_${cell.item.index}`"
                  >
                    Contained in polyols<i class="fa fa-info-circle fa-sm"></i>
                  </span>
                    <b-tooltip :target="`polyols_tooltip_${cell.item.index}`" placement="bottom">
                      <span v-translate>
                        Amounts contained in pre-blended polyols, not to be included in the amount of total imports
                      </span>
                    </b-tooltip>
                </b-input-group-prepend>
                <fieldGenerator
                  :fieldInfo="{index:cell.item.index,tabName: tabName, field:'quantity_polyols'}"
                  :disabled="!canEditSubstanceData"
                  :field="cell.item.originalObj.quantity_polyols"
                />
              </b-input-group>
              <b-input-group v-if="tooltipField === 'decision_exempted'">
                <b-input-group-prepend>
                  <span class="input-group-text" v-translate>
                    Remark
                  </span>
                </b-input-group-prepend>
                <fieldGenerator
                  :fieldInfo="{index:cell.item.index,tabName: tabName, field:'decision_polyols'}"
                  :disabled="!canEditSubstanceData"
                  :field="cell.item.originalObj.decision_polyols"
                />
              </b-input-group>
            </div>

          </template>
        </b-table>
      </div>
      <div v-if="hasBlends" class="table-wrapper">
        <div class="table-title">
          <h6 id="blends-table-title">
            <span v-translate>Mixtures</span>
          </h6>
          <b-btn class="mr-3" variant="outline-danger" @click="bulkRemove(selectedForDeleteBlends)" v-if="selectedForDeleteBlends.length">
            <span><span v-translate>Delete</span>&nbsp;{{selectedForDeleteBlends.length}}&nbsp;<span v-translate>selected rows</span></span>
          </b-btn>
          <div v-show="tableBlends.tableFilters" class="table-filters">
            <b-input-group :prepend="$gettext('Filter')">
              <b-form-input :class="{ highlighted: tableBlends.filters.search && tableBlends.filters.search.length }" v-model="tableBlends.filters.search"/>
            </b-input-group>
          </div>
          <i
            @click="tableBlends.tableFilters = !tableBlends.tableFilters"
            class="fa fa-filter fa-lg"
          ></i>
        </div>

        <b-table
          show-empty
          v-if="hasBlends"
          outlined
          bordered
          hover
          head-variant="light"
          class="submission-table full-bordered"
          stacked="md"
          id="blend-table"
          :items="tableItemsBlends"
          :fields="tableFieldsBlends"
          :empty-text="tableBlendsEmptyText"
          :filter="tableBlends.filters.search"
          ref="tableBlends"
        >
          <template v-for="field in tableFieldsBlends" v-slot:[`head(${field.key})`]="field">
            <div :style="`width: ${field.width ? field.width + 'px' : 'auto'}`" v-html="field.label" :key="field.key"></div>
          </template>
          <template v-slot:thead-top>
            <tr class="first-header">
              <th
                v-for="(header, header_index) in tab_info.section_headers"
                :colspan="header.colspan"
                :key="header_index"
              >
                <div
                  v-if="header.tooltip"
                  v-b-tooltip.hover
                  placement="left"
                  :title="header.tooltip"
                >
                  <span v-html="header.label"></span>
                  <i class="fa fa-info-circle fa-lg"></i>
                </div>
                <div v-else>
                  <span v-html="header.label"></span>
                </div>
              </th>
            </tr>
          </template>

          <template v-slot:cell(blend)="cell">
            <span
              style="cursor:pointer;"
              class="substance-blend-cell"
              v-b-tooltip.hover="'Click to expand/collapse mixture'"
              @click.stop="cell.toggleDetails"
            >
              <i :class="`fa fa-caret-${expandedStatus(cell.item._showDetails)}`"></i>
              {{cell.item.blend}}
            </span>
          </template>
          <template v-slot:cell(type)="cell">
            <div
              class="group-cell"
            >{{tab_data.blends.find(blend => cell.item.originalObj.blend.selected === blend.id).type}}</div>
          </template>
          <template v-slot:[`cell(${getCountrySlot})`]="cell">
            <CloneField
              :key="`${cell.item.index}_${getCountrySlot}_${tabName}`"
              v-on:removeThisField="remove_field(cell.item.index, true)"
              v-if="!cell.item[getCountrySlot] && canEditSubstanceData"
              :tabName="tabName"
              :current_field="cell.item.originalObj"
            />
            <div class="country-cell" v-else>{{cell.item[getCountrySlot]}}</div>
          </template>

          <template v-for="inputField in getTabInputFields" v-slot:[`cell(${inputField})`]="cell">
            <fieldGenerator
              :key="`${cell.item.index}_${inputField}_${tabName}`"
              :fieldInfo="{index:cell.item.index,tabName: tabName, field:inputField}"
              :disabled="isSubstanceDataReadOnly(inputField)"
              :field="cell.item.originalObj[inputField]"
            />
          </template>

          <template v-slot:cell(checkForDelete)="cell">
            <fieldGenerator
              v-show="canEditSubstanceData"
              :fieldInfo="{index:cell.item.index,tabName: tabName, field:'checkForDelete'}"
              :field="cell.item.originalObj.checkForDelete"
            />
          </template>

          <template v-slot:cell(validation)="cell">
            <b-btn-group class="row-controls">
              <span  @click="createModalData(cell.item.originalObj, cell.item.index)">
               <i
                  :class="{
                    'fa-pencil-square-o': !isActionReadOnly('edit', 'substance_data'),
                    'fa-eye': !isActionReadOnly('view', 'substance_data'),
                    'fa fa-lg': true
                  }"
                  :title="!isActionReadOnly('edit', 'substance_data') ? $gettext('Edit') : $gettext('View')"
                  v-b-tooltip
                ></i>
              </span>
              <span
                v-if="!isActionReadOnly('delete', 'substance_data')"
                @click="remove_field(cell.item.index)"
                class="table-btn"
              >
                <i class="fa fa-trash fa-lg" v-b-tooltip :title="$gettext('Delete')"></i>
              </span>
              <ValidationLabel
                :open-validation-callback="openValidation"
                :validation="cell.item.originalObj.validation.selected"
                :index="cell.item.index"
              />
            </b-btn-group>
          </template>

          <template
            v-for="tooltipField in getTabDecisionQuantityFields"
            v-slot:[`cell(${tooltipField})`]="cell"
          >
            <div
              class="edit-trigger"
              v-b-tooltip.hover="cell.item.originalObj[tooltipField].tooltip ? true : false"
              :title="cell.item.originalObj[tooltipField].tooltip"
              :key="tooltipField"
              @click="createModalData(cell.item.originalObj, cell.item.index)"
            >
              <span
                class="input"
                :class="{'text-right': tooltipField === 'quantity_exempted'}"
              >
                {{formatQuantity(cell.item[tooltipField])}}
                <i v-if="cell.item[tooltipField]" class="fa fa-info-circle fa-sm"></i>
              </span>
            </div>
            <div
              style="position: relative;z-index: 1; margin-top: 1rem"
              class="special-field"
              v-if="isQpsBlend.includes(parseInt(cell.item.originalObj.blend.selected))"
              :key="`${tooltipField}_qps`"
            >
              <b-input-group v-if="tooltipField === 'quantity_exempted'">
                <b-input-group-prepend>
                  <span class="input-group-text"
                    :id="`qps_tooltip_${cell.item.index}`"
                  >
                    QPS <i class="fa fa-info-circle fa-sm"></i>
                  </span>
                    <b-tooltip :target="`qps_tooltip_${cell.item.index}`" placement="bottom">
                      <span
                        v-translate="{qps_word: qps_word, substance: tab_data.display.blends[cell.item.originalObj.blend.selected].name, production: qps_production}">
                        Quantity of new %{substance} %{qps_word} to be used for QPS applications within your country %{production}
                      </span>
                    </b-tooltip>
                </b-input-group-prepend>
                <fieldGenerator
                  :fieldInfo="{index:cell.item.index,tabName: tabName, field:'quantity_quarantine_pre_shipment'}"
                  :disabled="!canEditSubstanceData"
                  :field="cell.item.originalObj.quantity_quarantine_pre_shipment"
                />
              </b-input-group>
              <b-input-group v-if="tooltipField === 'decision_exempted'">
                <b-input-group-prepend>
                  <span class="input-group-text" v-translate>
                    Remark
                  </span>
                </b-input-group-prepend>
                <fieldGenerator
                  :fieldInfo="{index:cell.item.index,tabName: tabName, field:'decision_quarantine_pre_shipment'}"
                  :disabled="!canEditSubstanceData"
                  :field="cell.item.originalObj.decision_quarantine_pre_shipment"
                />
              </b-input-group>
            </div>
          </template>

          <template v-slot:row-details="row">
            <thead>
              <tr>
                <th
                  class="small"
                  v-for="(header, header_index) in tab_info.blend_substance_headers"
                  :colspan="header.colspan"
                  :key="header_index"
                >
                  <span>{{labels[header]}}</span>
                </th>
              </tr>
            </thead>
            <tbody>
              <tr
                class="small"
                v-for="(substance, substance_index) in tab_data.display.blends[row.item.originalObj.blend.selected].components"
                :key="substance_index"
              >
                <td>{{substance.component_name}}</td>
                <td>
                  <b>{{(substance.percentage * 100).toPrecision(3)}}%</b>
                </td>
                <td v-for="(order, order_index) in blendSubstanceHeaders" :key="order_index">
                  <!-- <span v-if="row.item[order]"> -->
                  {{splitBlend(row.item[order], substance.percentage)}}
                  <!-- </span> -->
                </td>
              </tr>
            </tbody>
          </template>
        </b-table>
      </div>
    </div>
    <div id="tab-comments" class="table-wrapper">
      <div
        v-for="(comment, comment_key) in tab_info.comments"
        :key="comment_key"
        class="comments-input"
      >
        <label>
          <span>{{labels[comment_key]}}</span>
        </label>
        <!-- addComment(state, { data, tab, field }) { -->
        <textarea
          @change="$store.commit('addComment', {data: $event.target.value, tab:tabName, field: comment_key})"
          :disabled="isRemarkReadOnly(comment_key)"
          class="form-control"
          :value="comment.selected"
        ></textarea>
      </div>
    </div>
    <AppAside
      v-if="canEditSubstanceData || validationLength > 0"
      fixed
    >
      <DefaultAside
        v-on:fillSearch="fillTableSearch($event)"
        :canEditSubstanceData="canEditSubstanceData"
        :parentTabIndex.sync="sidebarTabIndex"
        :hovered="hovered"
        :tabName="tabName"
        :key="tabName"
      ></DefaultAside>
    </AppAside>

    <b-modal size="lg" ref="edit_modal" id="edit_modal" @hide="modal_data = null">
      <div v-if="modal_data" slot="modal-title">
        <span
          v-if="modal_data.field.substance.selected"
          v-translate="{name: tab_data.display.substances[modal_data.field.substance.selected]}"
        >Edit %{name} substance</span>
        <span
          v-else
          v-translate="{name: tab_data.display.blends[modal_data.field.blend.selected].name}"
        >Edit %{name} mixture</span>
      </div>
      <div v-if="modal_data">
      <b-btn @click="$refs.edit_modal.hide()" style="float:right" variant="success">Close</b-btn>

        <p class="muted">
          <span
            v-translate
          >All the quantity values should be expressed in metric tons (not ODP or CO₂-equivalent tonnes).</span>
          <br>
          <b>
            <span v-translate>The values are saved automatically in the table, as you type.</span>
          </b>
        </p>
        <b-row v-if="modal_data.field.substance.selected">
          <b-col>
            <span v-translate>Change substance</span>
          </b-col>
          <b-col>
            <multiselect
              class="mb-2"
              @input="updateFormField($event, {index:modal_data.index,tabName: tabName, field:'substance'})"
              trackBy="value"
              :disabled="!canEditSubstanceData"
              label="text"
              :hide-selected="true"
              :placeholder="$gettext('Select substance')"
              :value="parseInt(modal_data.field.substance.selected)"
              :options="tab_data.substances"
            />
          </b-col>
        </b-row>
        <div class="mb-3" v-for="(order, order_index) in tab_info.modal_order" :key="order_index">
          <b-row>
            <b-col>
              <span>{{labels[order]}}</span>
            </b-col>
            <b-col>
              <fieldGenerator
                :fieldInfo="{index:modal_data.index,tabName: tabName, field:order}"
                :disabled="!canEditSubstanceData"
                v-if="modal_data.field[order].type != 'multiselect'"
                :field="modal_data.field[order]"
              />
              <multiselect
                v-else
                :clear-on-select="true"
                :hide-selected="true"
                :close-on-select="true"
                :disabled="!canEditSubstanceData"
                trackBy="value"
                label="text"
                :placeholder="$gettext('Countries')"
                @input="updateFormField($event, {index:modal_data.index,tabName: tabName, field:order})"
                :value="parseInt(modal_data.field[order].selected)"
                :options="tab_data.countryOptions"
              />
            </b-col>
          </b-row>
        </div>
        <div v-if="fieldsDecisionQuantity">
          <b-row
            class="mb-3"
            v-for="(order,order_index) in fieldsDecisionQuantity"
            :key="order_index"
            v-show="anotherSpecialCase(order, modal_data)"
          >
            <b-col lg="3" class="mb-2">
              <span>{{labels[`decision_${order}`]}}</span>
            </b-col>
            <b-col lg="4">
              <b-input-group class="modal-group" :prepend="labels['quantity']">
                <fieldGenerator
                  :fieldInfo="{index:modal_data.index,tabName: tabName, field:`quantity_${order}`}"
                  :disabled="!canEditSubstanceData"
                  :field="modal_data.field[`quantity_${order}`]"
                />
              </b-input-group>
            </b-col>
            <b-col lg="5">
              <b-input-group class="modal-group" :prepend="labels['decision']">
                <fieldGenerator
                  :fieldInfo="{index:modal_data.index,tabName: tabName, field:`decision_${order}`}"
                  :disabled="!canEditSubstanceData"
                  :field="modal_data.field[`decision_${order}`]"
                />
              </b-input-group>
            </b-col>
          </b-row>
        </div>
        <b-row
          class="mt-3"
          v-for="comment_field in ['remarks_party','remarks_os']"
          :key="comment_field"
        >
          <b-col lg="3">
            <span>{{labels[comment_field]}}</span>
          </b-col>
          <b-col lg="9">
            <textarea
              :disabled="isRemarkReadOnly(comment_field)"
              class="form-control"
              v-model="modal_data.field[comment_field].selected"
            ></textarea>
          </b-col>
        </b-row>
      </div>
      <div slot="modal-footer">
        <b-btn @click="$refs.edit_modal.hide()" variant="success">
          <span v-translate>Close</span>
        </b-btn>
      </div>
    </b-modal>
  </div>
</template>

<script>
import { getLabels } from '@/components/art7/dataDefinitions/labels'
import inputFields from '@/components/art7/dataDefinitions/inputFields'
import FormTemplateMixin from '@/components/common/mixins/FormTemplateMixin'
import { intersect } from '@/components/common/services/utilsService'
import CloneField from '@/components/common/form-components/CloneField.vue'
import ValidationLabel from '@/components/common/form-components/ValidationLabel'

export default {
  mixins: [FormTemplateMixin],
  components: {
    CloneField,
    ValidationLabel
  },
  data() {
    return {
      tableFII: {
        tableFilters: false,
        pageOptions: [5, 25, 100],
        filters: {
          search: null,
          period_start: null,
          period_end: null,
          obligation: null,
          party: null,
          isCurrent: null
        }
      }
    }
  },

  props: {
    hasDisabledFields: Boolean
  },

  created() {
    this.setLabels()
  },
  methods: {
    setLabels() {
      const labels = getLabels(this.$gettext)
      this.labels = {
        ...labels.common,
        ...labels[this.tab_info.name]
      }
    },
    formatQuantity(value) {
      if (!value) return
      if (typeof (value) === 'string') return value
      if (typeof (value) === 'number') {
        if (value === 0) {
          return ''
        }
        if (value < 0) {
          return value.toPrecision(3)
        }
        if (value > 999) {
          return parseInt(value)
        }
        return value.toPrecision(3)
      }
    },

    fillTableSearch(data) {
      if (data.substance && data.substance === 'HFC-23' && this.tabName === 'has_produced') {
        this.tableFII.filters.search = data.substance
        this.tableFII.tableFilters = true
      } else if (data.substance) {
        this.table.filters.search = data.substance
        this.table.tableFilters = true
      }
      if (data.blend) {
        this.tableBlends.filters.search = data.blend
        this.tableBlends.tableFilters = true
      }
    },
    anotherSpecialCase(order, modal_data) {
      // determine what are we dealing with
      const type = modal_data.field.substance && modal_data.field.substance.selected
        ? 'substance'
        : modal_data.field.blend && modal_data.field.blend.selected
          ? 'blend'
          : null
      // just in case
      if (!type) return
      // this may look ugly, but it had to be done
      if (!['quarantine_pre_shipment', 'polyols'].includes(order)) {
        return true
      }
      if (this.isQps.includes(parseInt(modal_data.field[type].selected)) && order === 'quarantine_pre_shipment') {
        return true
      }
      if (this.isPolyols.includes(parseInt(modal_data.field[type].selected)) && order === 'polyols') {
        return true
      }
    }
  },
  computed: {
    selectedForDeleteFII() {
      return this.tableItemsFII.filter(field => field.checkForDelete).map(field => field.index)
    },
    getTabInputFields() {
      return intersect(inputFields, this.tab_info.fields_order)
    },
    qps_word() {
      let word = ''
      switch (this.tab_info.name) {
      case 'has_exports':
        word = 'exported'
        break
      case 'has_imports':
        word = 'imported'
        break
      case 'has_produced':
        word = 'produced'
        break
      case 'has_destroyed':
        word = 'destroyed'
        break
      case 'has_nonparty':
        word = 'traded'
        break
      default:
        break
      }
      return word
    },
    qps_production() {
      if (this.tabName === 'has_produced') {
        return 'and for exports'
      }
      return ''
    },
    isPolyols() {
      const tabsThatHavePolyols = ['has_imports', 'has_exports']
      if (!tabsThatHavePolyols.includes(this.tabName)) return []
      return [...this.tab_data.substances.filter(s => s.is_contained_in_polyols).map(s => s.value)]
    },
    // we might need this in the future
    // isPolyolsBlends() {
    //   const tabsThatHavePolyols = ['has_imports', 'has_exports']
    //   if (!tabsThatHavePolyols.includes(this.tabName)) return
    //   return [...this.tab_data.blends.filter(s => s.is_contained_in_polyols).map(s => s.id)]
    // },
    isQps() {
      const tabsThatHaveQPS = ['has_imports', 'has_exports', 'has_produced']
      if (!tabsThatHaveQPS.includes(this.tabName)) return []
      return [...this.tab_data.substances.filter(s => s.is_qps).map(s => s.value)]
    },
    isQpsBlend() {
      const tabsThatHaveQPS = ['has_imports', 'has_exports', 'has_produced']
      if (!tabsThatHaveQPS.includes(this.tabName)) return []
      return [...this.tab_data.blends.filter(s => s.is_qps).map(s => s.id)]
    },
    tableItems() {
      const tableFields = []
      this.tab_info.form_fields.forEach((element) => {
        const tableRow = {}
        Object.keys(element).forEach(key => {
          if (this.tabName === 'has_produced') {
            if (this.$store.getters.getCapturedSubstance(element.substance.selected)) {
              return
            }
          }
          if (element.substance.selected) {
            tableRow[key] = this.typeOfDisplayObj[key]
              ? this.$store.state.initialData.display[
                this.typeOfDisplayObj[key]
              ][element[key].selected]
              : (tableRow[key] = element[key].selected)
          }
        })
        if (Object.keys(tableRow).length) {
          tableRow.originalObj = element
          tableRow.index = this.tab_info.form_fields.indexOf(element)
          if (tableRow.originalObj.validation.selected.length) {
            tableRow.validation = 'invalid'
          } else {
            tableRow.validation = 'valid'
          }
          tableFields.push(tableRow)
        }
      })
      return tableFields
    },

    tableItemsFII() {
      const tableFields = []
      this.tab_info.form_fields.forEach((element) => {
        const tableRow = {}
        Object.keys(element).forEach(key => {
          if (this.tabName === 'has_produced' && element.substance.selected && this.$store.getters.getCapturedSubstance(element.substance.selected)) {
            tableRow[key] = this.typeOfDisplayObj[key]
              ? this.$store.state.initialData.display[
                this.typeOfDisplayObj[key]
              ][element[key].selected]
              : (tableRow[key] = element[key].selected)
          }
        })
        if (Object.keys(tableRow).length) {
          tableRow.originalObj = element
          tableRow.index = this.tab_info.form_fields.indexOf(element)
          if (tableRow.originalObj.validation.selected.length) {
            tableRow.validation = 'invalid'
          } else {
            tableRow.validation = 'valid'
          }
          tableFields.push(tableRow)
        }
      })
      return tableFields
    },

    tableFieldsFII() {
      const tableHeaders = []
      const options = {}
      this.tab_info.special_headers.section_subheaders.forEach((element) => {
        tableHeaders.push({
          key: element.name,
          label: element.label,
          ...options
        })
      })
      return tableHeaders
    },
    tableFIIEmptyText() {
      return this.$gettext('Please use the form on the right sidebar to add substances')
    },
    getTabSpecialInputFields() {
      return intersect(this.tab_info.special_fields_order, inputFields)
    },

    getCountrySlot() {
      return intersect(
        ['source_party', 'trade_party', 'destination_party'],
        this.tab_info.fields_order
      )[0]
    },

    hasSubstances() {
      return Object.keys(this.$store.state.form.tabs[this.tabName].default_properties).includes('substance')
    },
    hasBlends() {
      return Object.keys(this.$store.state.form.tabs[this.tabName].default_properties).includes('blend')
    },

    tableCounter() {
      const counter = []
      if (this.hasSubstances) counter.push(1)
      if (this.hasBlends) counter.push(1)
      return counter.length
    },

    getTabDecisionQuantityFields() {
      return intersect(
        ['decision_exempted', 'quantity_exempted'],
        this.tab_info.fields_order
      )
    },

    fieldsDecisionQuantity() {
      if (this.tab_info.hidden_fields_order) {
        const fields = []

        for (const field of this.tab_info.hidden_fields_order) {
          const current = field.split('_')
          current.shift()
          this.pushUnique(fields, current.join('_'))
        }

        return fields
      }
      return false
    }
  },
  watch: {
    '$language.current': {
      handler() {
        this.setLabels()
      }
    }
  }
}
</script>
