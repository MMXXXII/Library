<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/userStore'

const router = useRouter()
const userStore = useUserStore()

onMounted(async () => {
  await userStore.fetchUserInfo()
  if (!userStore.isAuthenticated) {
    router.push('/login')
  }
})

async function handleLogout() {
  await userStore.logout()
  router.push('/login')
}
</script>


<template>
  <v-container class="profile-container">
    <v-card class="pa-6 mx-auto" max-width="600" elevation="4" rounded="lg">     
      <div class="text-center mb-5">
        <v-avatar size="100" color="primary" class="mx-auto mb-3">
          <v-icon size="60" color="white">mdi-account-circle</v-icon>
        </v-avatar>
        <v-card-title class="pa-0 justify-center">Профиль пользователя</v-card-title>
      </div>

      <v-card-text>
        <v-progress-linear
          v-if="userStore.loading"
          indeterminate
          height="4"
          class="mb-4"
          rounded
          color="primary"
        ></v-progress-linear>

        <div v-else-if="userStore.user" class="text-center">
          <v-list dense max-width="400" style="margin: 0 auto;">
            <v-list-item>
              <v-list-item-avatar>
                <v-icon>mdi-account</v-icon>
              </v-list-item-avatar>
              <v-list-item-content>
                <v-list-item-title>Имя пользователя</v-list-item-title>
                <v-list-item-subtitle>{{ userStore.user.username }}</v-list-item-subtitle>
              </v-list-item-content>
            </v-list-item>

            <v-divider class="my-2"></v-divider>

            <v-list-item>
              <v-list-item-avatar>
                <v-icon>mdi-email</v-icon>
              </v-list-item-avatar>
              <v-list-item-content>
                <v-list-item-title>Email</v-list-item-title>
                <v-list-item-subtitle>{{ userStore.user.email }}</v-list-item-subtitle>
              </v-list-item-content>
            </v-list-item>
          </v-list>

          <v-btn
            color="error"
            class="mt-5"
            block
            rounded="lg"
            @click="handleLogout"
            max-width="300"
          >
            Выход
          </v-btn>
        </div>
      </v-card-text>
    </v-card>
  </v-container>
</template>
