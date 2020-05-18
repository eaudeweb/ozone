<script>
export default {
  data() {
    return {
      submissionInfoWithCustomPermissions: ['reporting_channel', 'submission_format', 'reporting_officer', 'submitted_at']
    }
  },
  created() {},
  computed: {
    permissions() {
      return this.$store.state.permissions.form.permission_matrix
    },
    //  User data
    isSecretariat() {
      return this.$store.state.currentUser.is_secretariat
    },
    isParty() {
      return !this.$store.state.currentUser.is_secretariat
    },
    //  Submission creator
    isCreatedBySecretariat() {
      return this.$store.state.current_submission.filled_by_secretariat
    },
    isCreatedByParty() {
      return !this.$store.state.current_submission.filled_by_secretariat
    },
    //  Submission status
    submissionCurrentState() {
      return this.$store.state.current_submission.current_state
    },
    //  Edit mode status
    editModeEnabled() {
      return this.canEnableEditMode && this.$store.getters.edit_mode
    },
    //  User permissions for remarks
    canChangeRemarksParty() {
      return (
        !this.permissions['remarks_party']
        && this.editModeEnabled
      )
    },
    canChangeRemarksSecretariat() {
      return (
        !this.permissions['remarks_secretariat']
        && this.editModeEnabled
      )
    },
    //  User permissions for Files tab
    canUploadFiles() {
      return (
        !this.permissions['files']
        && this.editModeEnabled
      )
    },
    //  User permissions for Questionnaire tab
    canChangeQuestionnaire() {
      return (
        !this.permissions['questionnaire']
        && this.editModeEnabled
      )
    },
    //  User permissions for other submission info data
    canEditOtherSubmissionInfoData() {
      return (
        !this.permissions['other_submission_info_data']
        && this.editModeEnabled
      )
    },
    canEditSubmissionInfoData() {
      return (
        !this.permissions['other_submission_info_data']
        || !this.permissions['reporting_channel']
        || !this.permissions['submission_format']
        || !this.permissions['reporting_officer']
        || !this.permissions['submitted_at']
      )
    },
    //  User can edit substance data
    canEditSubstanceData() {
      return (
        !this.permissions['substance_data']
        && this.editModeEnabled
      )
    },
    //  User can enter Edit Mode
    canEnableEditMode() {
      let ok = false
      Object.keys(this.permissions).forEach(permission => {
        if (!this.permissions[permission] && !ok) ok = true
      })
      return ok
    }
  },
  methods: {
    isSubmissionInfoReadOnly(info) {
      if (this.submissionInfoWithCustomPermissions.includes(info)) {
        return this.permissions[info] || !this.editModeEnabled
      }
      return this.permissions['other_submission_info_data'] || !this.editModeEnabled
    },
    isFlagReadOnly(flagType) {
      return this.permissions[flagType] || !this.editModeEnabled
    },
    isRemarkReadOnly(remark) {
      let type = remark.split('_')
      type = type[type.length - 1]
      if (['party'].includes(type)) return !this.canChangeRemarksParty
      if (['secretariat', 'os'].includes(type)) return !this.canChangeRemarksSecretariat
      return true
    },
    isSubstanceDataReadOnly(inputField) {
      return ['remarks_os', 'remarks_party'].includes(inputField) ? this.isRemarkReadOnly(inputField) : !this.canEditSubstanceData
    },
    isActionReadOnly(action = null, applyOn) {
      if (
        (action === 'add' || action === 'edit' || action === 'delete')
        && (this.permissions[applyOn] || !this.editModeEnabled)
      ) return true
      if (
        action === 'view'
        && !this.permissions[applyOn]
        && this.editModeEnabled
      ) return true
      return false
    }
  }
}
</script>
