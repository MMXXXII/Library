import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'

export const useUserStore = defineStore('user', () => {
  const user = ref(null)
  const isAuthenticated = ref(false)
  const isSuperUser = ref(false)

  async function login(usernameParam, passwordParam) {
    const response = await axios.post('/userprofile/login/', {
      username: usernameParam,
      password: passwordParam,
    })
    if (response.data.success) {
      user.value = {
        username: response.data.username,
        email: response.data.email,
        is_superuser: response.data.is_superuser,
      }
      isAuthenticated.value = true
      isSuperUser.value = response.data.is_superuser
    }
  }

  async function fetchUserInfo() {
    const { data } = await axios.get('/userprofile/info/')
    user.value = data
    isAuthenticated.value = !!data.is_authenticated
    isSuperUser.value = data.is_superuser
  }

  async function logout() {
    await axios.post('/userprofile/logout/')
    user.value = null
    isAuthenticated.value = false
    isSuperUser.value = false
  }

  return {
    user,
    isAuthenticated,
    isSuperUser,
    login,
    fetchUserInfo,
    logout,
  }
})