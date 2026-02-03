<script setup>
import { ref, onMounted } from 'vue'
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
  if (userStore.isAuthenticated) {
    router.replace('/books')
  }
}

async function handleLogout() {
  await userStore.logout()
  router.replace('/login')
}
</script>

<template>
  <v-container>
    <v-card max-width="400" class="mx-auto my-10">
      <v-card-title>Вход в систему</v-card-title>
      <v-card-text>
        <v-form @submit.prevent="handleLogin">
          <v-text-field
            v-model="username"
            label="Имя пользователя"
            autocomplete="username"
            required
          ></v-text-field>

          <v-text-field
            v-model="password"
            label="Пароль"
            type="password"
            autocomplete="current-password"
            required
          ></v-text-field>

          <v-btn
            type="submit"
            :loading="userStore.loading"
            :disabled="userStore.loading"
            block
          >
            {{ userStore.loading ? 'Загрузка...' : 'Войти' }}
          </v-btn>
        </v-form>

        <v-alert
          v-if="userStore.error"
          type="error"
          dense
          text
          class="mt-4"
        >
          {{ userStore.error }}
        </v-alert>
      </v-card-text>
    </v-card>
  </v-container>
</template>
