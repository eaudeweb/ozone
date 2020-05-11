const ALLOWED_FILE_EXTENSIONS = 'pdf,doc,docx,xls,xlsx,zip,rar,txt,htm,html,odt,ods,eml,ppt,pptx,mdb,png,jpg,jpeg,gif'

export default {
  data() {
    return {}
  },
  computed: {
    files() {
      const { files } = this.$store.state.form.tabs.files.form_fields
      return files
    },
    allowedExtensions() {
      return ALLOWED_FILE_EXTENSIONS.split(',').map(x => `.${x}`)
    }
  },
  methods: {
    async getSubmissionFiles() {
      const files = await this.$store.dispatch('getSubmissionFiles')
      this.$store.commit('deleteAllTabFiles')
      this.$store.commit('addTabFiles', { files })
    },
    getWereAllFilesUploadedSuccessfully() {
      return !this.files.find(file => !file.upload_successful)
    },
    getFilesWithUpdatedDescription() {
      return this.files.filter(file => file.isDescriptionUpdated)
    },
    getFilesNotUploaded() {
      return this.files.filter(file => !file.tus_id)
    },
    onProgressCallback(file, percentage) {
      this.$store.commit('updateFilePercentage', { file, percentage })
    },
    uploadFiles() {
      const files = this.getFilesNotUploaded()
      if (!files.length) {
        return
      }
      this.$store.commit('updateFilesUploadInProgress', true)
      return new Promise(async (resolve, reject) => {
        try {
          await this.$store.dispatch('uploadFiles', { files, onProgressCallback: this.onProgressCallback })
          const checkFilesUploadedSuccessfullyInterval = setInterval(async () => {
            if (this.getWereAllFilesUploadedSuccessfully()) {
              this.$store.commit('updateFilesUploadInProgress', false)
              clearInterval(checkFilesUploadedSuccessfullyInterval)
              resolve()
              return
            }
            await this.$store.dispatch('setJustUploadedFilesState')
          }, 1500)
        } catch (error) {
          this.$store.commit('updateFilesUploadInProgress', false)
          console.log('error upload', error)
          reject(error)
        }
      })
    }
  }
}
