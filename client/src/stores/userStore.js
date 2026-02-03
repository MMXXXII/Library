import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'

export const useUserStore = defineStore('user', () => {
  const user = ref(null)
  const isAuthenticated = ref(false)
  const isOtpVerified = ref(false)
  const isSuperUser = ref(false)
  const loading = ref(false)
  const pendingUsername = ref(null)

  function initializePending() {
    const savedPending = sessionStorage.getItem('pending_username')
    if (savedPending) {
      pendingUsername.value = savedPending
    }
  }

  async function login(usernameParam, passwordParam) {
    loading.value = true

    const response = await axios.post('/userprofile/login/', {
      username: usernameParam,
      password: passwordParam,
    })

    loading.value = false

    if (response.data.success) {
      user.value = {
        username: response.data.username,
        email: response.data.email,
        is_superuser: response.data.is_superuser,
      }
      isAuthenticated.value = true
      isSuperUser.value = response.data.is_superuser
      isOtpVerified.value = false
    }
  }

  async function fetchUserInfo() {
    const { data } = await axios.get('/userprofile/info/')
    user.value = data
    isAuthenticated.value = !!data.is_authenticated
    isSuperUser.value = data.is_superuser
    isOtpVerified.value = data.second_factor === true
  }

  async function logout() {
    loading.value = true
    await axios.post('/userprofile/logout/')
    resetAuthState()
    sessionStorage.removeItem('pending_username')
    loading.value = false
  }

  function resetAuthState() {
    user.value = null
    isAuthenticated.value = false
    isOtpVerified.value = false
    isSuperUser.value = false
    pendingUsername.value = null
  }

  return {
    user,
    isAuthenticated,
    login,
    isSuperUser,
    loading,
    pendingUsername,
    
    initializePending,

    fetchUserInfo,
    logout,
  }
})
