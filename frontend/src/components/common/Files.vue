<template>
  <div class="col-8 files-upload-wrapper">
    <div>
      <div class="row">
        <div class="col-7 mb-2">
          <b-form-file
            id="choose-files-button"
            :disabled="!$store.getters.can_upload_files || !$store.getters.edit_mode || loadingInitialFiles"
            :multiple="true"
            ref="filesInput"
            v-model="selectedFiles"
            :placeholder="placeholder"
            @input="onSelectedFilesChanged"
          />
        </div>
      </div>
      <small class="ml-1 muted">
         <span v-translate>Allowed files extensions: </span> {{allowedExtensions.join(', ')}}
      </small>
      <div v-if="tableItemsToUpload.length">
        <h5 class="mt-3 mb-3 ml-1"> {{tableItemsToUpload.length}} <span v-translate>files ready for upload:</span></h5>
      </div>
    </div>
    <b-table
      show-empty
      class="no-header"
      :empty-text="$gettext('Click the Browse button to add files')"
      :items="tableItemsToUpload"
      :fields="tableFieldsUploaded.filter(field => field.key !== 'date')"
    >

      <template v-slot:cell(description)="cell">
        <b-form-input
          class="d-inline"
          placeholder="Optional description"
          :value="cell.value"
          :disabled="!$store.getters.can_upload_files || !$store.getters.edit_mode"
          style="height: unset"
          @input="onFileDescriptionChanged($event, cell.item.details)"
        />
      </template>

      <template v-slot:cell(actions)="cell">
        <div class="d-flex">
          <b-button variant="outline-danger" v-if="$store.getters.can_upload_files && $store.getters.edit_mode" @click="deleteFile($event, cell.item.details)">
            <i class="fa fa-trash" aria-hidden="true"></i>
          </b-button>
          <div class="ml-2" style="min-width:300px" v-if="cell.item.details.percentage">
            <b-progress :value="cell.item.details.percentage" :max="100">
              <b-progress-bar :value="cell.item.details.percentage">
                Uploading: <strong>{{ parseInt(cell.item.details.percentage) }}%</strong>
              </b-progress-bar>
            </b-progress>
          </div>
        </div>
      </template>
    </b-table>
    <b-btn
      class="mb-4" variant="primary"
      v-translate
      v-if="tableItemsToUpload.length"
      v-html="$store.getters.edit_mode ? 'Start upload': 'Enable edit mode to upload files'"
      :disabled="!$store.getters.can_upload_files || !$store.getters.edit_mode"
      @click="startUpload"
    ></b-btn>
    <!-- TODO: there needs to be a method for just saving files. This is a dirty workaround -->
    <br>
    <div v-if="tableItemsUploaded.length">
      <h5 class="mb-4 ml-1" v-translate>Uploaded files</h5>
      <b-table
            show-empty
            :empty-text="$gettext('No files uploaded')"
            :items="tableItemsUploaded"
            :fields="tableFieldsUploaded"
          >
        <template v-slot:cell(actions)="cell">
          <b-btn
            variant="outline-primary"
            @click="$store.dispatch('downloadStuff', { url: cell.item.details.file_url, fileName: cell.item.details.name })"
            v-b-tooltip
            :title="downloadLabel"
          ><i class="fa fa-download"></i></b-btn>
          <b-button class="ml-2 mr-2" variant="outline-danger" v-if="$store.getters.can_upload_files && $store.getters.edit_mode" @click="deleteFile($event, cell.item.details)">
            <i class="fa fa-trash" aria-hidden="true"></i>
          </b-button>
        </template>
      </b-table>
    </div>
  </div>
</template>

<script>
import { isObject } from '@/components/common/services/utilsService'
import { update } from '@/components/common/services/api'
import FilesMixin from '@/components/common/mixins/FilesMixin'
import SaveMixin from '@/components/common/mixins/SaveMixin'
import { dateFormatToDisplay, dateFormatToYYYYMMDD } from '@/components/common/services/languageService.js'

export default {
  mixins: [FilesMixin, SaveMixin],

  props: {
    tabId: Number,
    tabIndex: Number
  },
  data() {
    return {
      tabsToSave: [],
      selectedFiles: [],
      loadingInitialFiles: true,
      placeholder: this.$gettext('Click to browse files'),
      uploadLabel: this.$gettext('File not uploaded yet'),
      downloadLabel: this.$gettext('Download'),
      tableFieldsUploaded: [
        { key: 'fileName', label: this.$gettext('File Name') },
        { key: 'description', label: this.$gettext('Description') },
        { key: 'date', label: this.$gettext('Date') },
        { key: 'actions', label: this.$gettext('Actions') }
      ]
    }
  },
  async created() {
    await this.getSubmissionFiles()
    this.loadingInitialFiles = false
  },
  computed: {
    tableItemsUploaded() {
      return this.files.filter(file => file.upload_successful).map(file => ({
        fileName: file.name,
        description: file.description,
        date: this.formatDate(file.updated),
        details: file
      }))
    },
    tableItemsToUpload() {
      return this.files.filter(file => !file.upload_successful).map(file => ({
        fileName: file.name,
        description: file.description,
        details: file
      }))
    },
    form() {
      return this.$store.state.form
    },
    newTabs() {
      return this.$store.state.newTabs
    },
    is_secretariat() {
      return this.$store.state.currentUser.is_secretariat
    }
  },
  methods: {
    formatDate(date) {
      return dateFormatToDisplay(date)
    },
    async deleteFile(e, file) {
      const confirmed = await this.$store.dispatch('openConfirmModal', { title: 'Please confirm', description: 'Are you sure you want to delete the selected file?', $gettext: this.$gettext })
      if (!confirmed) {
        return
      }
      this.$store.dispatch('deleteTabFile', {	file })
      this.$refs.filesInput.reset()
    },
    onFileDescriptionChanged(description, file) {
      this.$store.commit('updateTabFileDescription', {
        file,
        description
      })
      if (this.$store.state.form.tabs.files !== 'edited') {
        this.$store.commit('setTabStatus', {
          tab: this.$store.state.form.tabs.files.name,
          value: 'edited'
        })
      }
    },
    async onSelectedFilesChanged() {
      if (!this.selectedFiles || !this.selectedFiles.length) {
        return
      }
      const files = this.selectedFiles.filter(file => this.allowedExtensions.find(extension => file.name.toLowerCase().trim().endsWith(extension)))
      const NotAllowedFiles = this.selectedFiles.filter(file => !this.allowedExtensions.find(extension => file.name.toLowerCase().trim().endsWith(extension)))
      if (NotAllowedFiles.length) {
        this.$store.dispatch('setAlert', {
          $gettext: this.$gettext,
          message: { __all__: [`${this.$gettext('The following files are not allowed')}: <br> ${NotAllowedFiles.map(f => f.name).join(' ')}`] },
          variant: 'danger'
        })
      }
      files.forEach((file, index) => {
        file.updated = index
      })
      this.$store.commit('addTabFiles', { files })

      this.$refs.filesInput.reset()
    },
    async startUpload() {
      await this.uploadFile()
      this.checkIfThereIsAnotherActionToDoBeforeReturning()
    },
    async uploadFile() {
      await new Promise(async (resolve) => {
        let current_tab_data = {}
        const tab = this.$store.state.form.tabs.files
        const url = this.$store.state.current_submission[tab.endpoint_url]
        if (isObject(tab.form_fields)) {
          const save_obj = JSON.parse(JSON.stringify(tab.default_properties))
          Object.keys(save_obj).forEach(key => {
            if (key === 'submitted_at' && !this.is_secretariat) {
              resolve()
              return
            }
            if (tab.name === 'flags') {
              if (this.$store.state.current_submission.changeable_flags.includes(key)) {
                current_tab_data[key] = tab.form_fields[key].selected
              }
            } else {
              current_tab_data[key] = tab.form_fields[key].selected
            }
            if (tab.form_fields[key].type === 'date') {
              current_tab_data[key] = dateFormatToYYYYMMDD(current_tab_data[key], this.$language.current)
            }
          })
        }
        try {
          await this.uploadFiles()
          current_tab_data = this.getFilesWithUpdatedDescription()
            .map(file => ({
              id: file.id,
              name: file.name,
              description: file.description
            }))
          await update(url, current_tab_data)
          await this.getSubmissionFiles()
          if (tab.status !== null) {
            this.$store.commit('setTabStatus', { tab: tab.name, value: true })
          }
          if (Array.isArray(tab.form_fields)) {
            if (!tab.form_fields.length) {
              this.$store.commit('updateNewTabs', tab.name)
            }
          }
        } catch (error) {
          this.$store.commit('setTabStatus', { tab: tab.name, value: false })
          this.resetActionToDispatch()
          this.$store.dispatch('setAlert', {
            $gettext: this.$gettext,
            message: { __all__: [this.alerts.save_failed] },
            variant: 'danger' })
        }
        resolve()
      })
    },
    checkIfThereIsAnotherActionToDoBeforeReturning(tabName) {
      this.tabsToSave = this.tabsToSave.filter(t => t !== tabName)
      if (this.tabsToSave.length === 0) {
        if (this.$store.state.actionToDispatch) {
          this.$store.dispatch('clearEdited')
          this.$store.dispatch('saveCallback', { actionToDispatch: this.$store.state.actionToDispatch, data: this.$store.state.dataForAction })
          this.resetActionToDispatch(false)
        }
      }
    }
  },
  watch: {
    'files': {
      handler() {
        if (parseInt(this.tabId) === this.tabIndex) {
          if (this.$store.state.form.tabs.files !== 'edited') {
            this.$store.commit('setTabStatus', {
              tab: this.$store.state.form.tabs.files.name,
              value: 'edited'
            })
          }
        }
      },
      deep: true
    }
  }
}
</script>

<style lang="css" scoped>
a {
  margin-bottom: 1rem;
}
.progress {
  height: 100%;
}
.btn-link:hover {
  text-decoration: none;
}
.uploadedFiles {
  display: flex;
}
.card-header {
  background: white;
  padding: 0;
  margin-bottom: 1rem;
}
</style>
