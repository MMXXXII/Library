<script setup>
import { onMounted, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '../stores/userStore'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const username = ref('')
const password = ref('')

onMounted(async () => {
  await userStore.fetchUserInfo()

  if (userStore.isAuthenticated) {
    router.replace('/books')
  }
})

async function handleLogin() {
  await userStore.login(username.value, password.value)
  router.replace('/books')
}

async function handleLogout() {
  await userStore.logout()
  router.replace('/login')
}
</script>

<template>
  <v-container class="profile-container" v-if="$route.path === '/profile'">
    <v-card max-width="600" class="mx-auto my-5 pa-5">
      <v-card-title>Профиль пользователя</v-card-title>
      <v-card-text>
        <v-progress-linear v-if="userStore.loading" indeterminate color="primary"></v-progress-linear>

        <div v-else-if="userStore.user">
          <v-list dense>
            <v-list-item>
              <v-list-item-content>
                <v-list-item-title><strong>Имя пользователя:</strong> {{ userStore.user.username }}</v-list-item-title>
              </v-list-item-content>
            </v-list-item>
            <v-list-item>
              <v-list-item-content>
                <v-list-item-title><strong>Email:</strong> {{ userStore.user.email }}</v-list-item-title>
              </v-list-item-content>
            </v-list-item>
          </v-list>
          <v-btn color="error" class="mt-4" @click="handleLogout" block>Выход</v-btn>
        </div>

        <v-alert type="error" v-else-if="userStore.error" dense outlined>
          {{ userStore.error }}
        </v-alert>
      </v-card-text>
    </v-card>
  </v-container>

  <v-container max-width="400" class="login-container mx-auto my-5 pa-5" v-else>
    <v-card class="pa-8" elevation="8" rounded="lg">
      <v-form @submit.prevent="handleLogin">
        <v-text-field
          label="Имя пользователя"
          v-model="username"
          required
          autocomplete="username"
          prepend-inner-icon="mdi-account"
          dense
          variant="outlined"
          class="mb-4"
        ></v-text-field>

        <v-text-field
          label="Пароль"
          v-model="password"
          required
          type="password"
          autocomplete="current-password"
          prepend-inner-icon="mdi-lock"
          dense
          variant="outlined"
        ></v-text-field>

        <v-btn 
          type="submit" 
          :loading="userStore.loading" 
          :disabled="userStore.loading" 
          color="primary" 
          block
          size="large"
          class="mt-6"
          rounded="lg"
        >
          {{ userStore.loading ? 'Загрузка...' : 'Войти' }}
        </v-btn>

        <v-alert v-if="userStore.error" type="error" dense outlined class="mt-6" rounded="lg">
          {{ userStore.error }}
        </v-alert>
      </v-form>
    </v-card>
  </v-container>
</template>