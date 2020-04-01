<script>
import { permissions, allowEditMode } from '@/components/common/dataDefinitions/permissions'

export default {
  data() {
    return {
      permissions,
      submissionInfoWithCustomPermissions: ['reporting_channel', 'submission_format', 'reporting_officer', 'submitted_at']
    }
  },
  created() {},
  computed: {
    //  User data
    isSecretariat() {
      return this.$store.state.currentUser.is_secretariat
    },
    isParty() {
      return !this.$store.state.currentUser.is_secretariat
    },
    //  Submission creator
    isCreatedBySecretariat() {
      return this.$store.state.current_submission.created_by === 'secretariat'
    },
    isCreatedByParty() {
      return this.$store.state.current_submission.created_by !== 'secretariat'
    },
    //  Permission dictionary index
    //    0 -> created by party, accesed by party
    //    1 -> created by party, accesed by secretariat
    //    2 -> created by secretariat, accesed by party
    //    3 -> created by secretariat, accesed by secretariat
    permissionsDictionaryIndex() {
      if (this.isCreatedByParty && this.isParty) return 0
      if (this.isCreatedByParty && this.isSecretariat) return 1
      if (this.isCreatedBySecretariat && this.isParty) return 2
      if (this.isCreatedBySecretariat && this.isSecretariat) return 3
      return null
    },
    //  Submission status
    submissionCurrentState() {
      return this.$store.state.current_submission.current_state
    },
    //  Edit mode status
    editModeEnabled() {
      return this.$store.getters.edit_mode
    },
    //  User permissions for remarks
    canChangeRemarksParty() {
      return (
        !this.permissions['remarks_party'][this.submissionCurrentState][this.permissionsDictionaryIndex]
        && this.$store.getters.can_change_remarks_party
        && this.editModeEnabled
      )
    },
    canChangeRemarksSecretariat() {
      return (
        !this.permissions['remarks_secretariat'][this.submissionCurrentState][this.permissionsDictionaryIndex]
        && this.$store.getters.can_change_remarks_secretariat
        && this.editModeEnabled
      )
    },
    //  User permissions for Files tab
    canUploadFiles() {
      return (
        !this.permissions['files'][this.submissionCurrentState][this.permissionsDictionaryIndex]
        && this.$store.getters.can_upload_files
        && this.editModeEnabled
      )
    },
    //  User permissions for Questionnaire tab
    canChangeQuestionnaire() {
      return (
        !this.permissions['questionnaire'][this.submissionCurrentState][this.permissionsDictionaryIndex]
        && this.editModeEnabled
      )
    },
    //  User permissions for Submission Info and Substance Data
    canEditData() {
      return (
        this.$store.getters.can_edit_data
        && this.editModeEnabled
      )
    },
    //  User can enter Edit Mode
    canEnableEditMode() {
      return allowEditMode()[this.submissionCurrentState][this.permissionsDictionaryIndex]
    }
  },
  methods: {
    isSubmissionInfoReadOnly(info) {
      if (this.submissionInfoWithCustomPermissions.includes(info)) {
        const readOnly = this.permissions[info][this.submissionCurrentState][this.permissionsDictionaryIndex]
        if (readOnly || !this.canEditData) return true
        return false
      }
      const readOnly = this.permissions['other_submission_info_data'][this.submissionCurrentState][this.permissionsDictionaryIndex]
      if (readOnly || !this.canEditData) return true
      return false
    },
    isFlagReadOnly(flagType) {
      const readOnly = this.permissions[flagType][this.submissionCurrentState][this.permissionsDictionaryIndex]
      if (readOnly || !this.editModeEnabled) return true
      return false
    },
    isRemarkReadOnly(remark) {
      let type = remark.split('_')
      type = type[type.length - 1]
      if (['party'].includes(type)) return !this.canChangeRemarksParty
      if (['secretariat', 'os'].includes(type)) return !this.canChangeRemarksSecretariat
      return true
    },
    canEditSubstanceData(onlySecretariat = false) {
      if (onlySecretariat) {
        return (
          !this.permissions['substance_data'][this.submissionCurrentState][this.permissionsDictionaryIndex]
          && this.canEditData
          && this.isSecretariat
        )
      }
      return (
        !this.permissions['substance_data'][this.submissionCurrentState][this.permissionsDictionaryIndex]
        && this.canEditData
      )
    }
  }
}
</script>
