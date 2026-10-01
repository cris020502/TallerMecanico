<script setup lang="ts">
import { computed, ref } from 'vue'
import api, { type AuthResponse, type User } from './api'

const view = ref<'login' | 'register' | 'recovery'>('login')
const loading = ref(false)
const error = ref('')
const notice = ref('')
const valid = ref(false)
const user = ref<User | null>(JSON.parse(localStorage.getItem('user') ?? 'null'))
const login = ref({ email: '', password: '' })
const register = ref({ full_name: '', email: '', password: '', confirm: '' })
const recoveryEmail = ref('')
const passwordRules = [(v: string) => !!v || 'Campo requerido', (v: string) => v.length >= 10 || 'Mínimo 10 caracteres', (v: string) => /[A-Z]/.test(v) && /[a-z]/.test(v) && /\d/.test(v) || 'Incluye mayúscula, minúscula y número']
const emailRules = [(v: string) => !!v || 'El correo es requerido', (v: string) => /.+@.+\..+/.test(v) || 'Correo inválido']
const roleLabel: Record<string, string> = { administrador: 'Administrador del taller', recepcionista: 'Recepcionista', asesor_vehiculos: 'Asesor de vehículos', tecnico_consulta: 'Técnico de consulta', cliente: 'Cliente', sistema: 'Sistema' }
const title = computed(() => view.value === 'login' ? 'Bienvenido de nuevo' : view.value === 'register' ? 'Crea tu cuenta' : 'Recupera tu acceso')

function saveAuth(data: AuthResponse) { localStorage.setItem('access_token', data.access_token); localStorage.setItem('refresh_token', data.refresh_token); localStorage.setItem('user', JSON.stringify(data.user)); user.value = data.user }
async function submitLogin() { if (!valid.value) return; loading.value = true; error.value = ''; try { saveAuth((await api.post<AuthResponse>('/auth/login', login.value)).data) } catch (e: any) { error.value = e.response?.data?.detail ?? 'No fue posible iniciar sesión.' } finally { loading.value = false } }
async function submitRegister() { if (!valid.value || register.value.password !== register.value.confirm) { error.value = 'Verifica la contraseña y su confirmación.'; return }; loading.value = true; error.value = ''; try { saveAuth((await api.post<AuthResponse>('/auth/register', register.value)).data) } catch (e: any) { error.value = e.response?.data?.detail ?? 'No fue posible crear la cuenta.' } finally { loading.value = false } }
async function submitRecovery() { if (!valid.value) return; loading.value = true; error.value = ''; try { notice.value = (await api.post('/auth/recovery', { email: recoveryEmail.value })).data.message } catch { error.value = 'No fue posible procesar la solicitud.' } finally { loading.value = false } }
async function logout() { try { await api.post('/auth/logout', { refresh_token: localStorage.getItem('refresh_token') }) } finally { localStorage.clear(); user.value = null; view.value = 'login' } }
</script>

<template>
  <v-app>
    <v-main class="page">
      <section v-if="user" class="dashboard">
        <v-card max-width="720" class="pa-8" elevation="8">
          <div class="d-flex justify-space-between align-start mb-8"><div><div class="text-overline text-primary">Taller Mecánico</div><h1 class="text-h4">Hola, {{ user.full_name }}</h1><p class="text-medium-emphasis">Sesión autenticada correctamente.</p></div><v-btn variant="tonal" @click="logout">Cerrar sesión</v-btn></div>
          <v-divider class="mb-5" /><h2 class="text-h6 mb-3">Perfil y permisos</h2>
          <v-chip v-for="role in user.roles" :key="role" class="mr-2 mb-2" color="primary">{{ roleLabel[role] ?? role }}</v-chip>
          <p class="mt-5 text-medium-emphasis">Desde aquí se integrarán los módulos de órdenes, diagnósticos, autorizaciones, inventario y notificaciones según los permisos asignados.</p>
        </v-card>
      </section>
      <section v-else class="auth-layout">
        <aside class="hero"><v-icon size="54" color="secondary">mdi-car-wrench</v-icon><h1>Control total para tu taller.</h1><p>Gestiona la experiencia de cada vehículo desde su recepción hasta su entrega.</p><div class="actors"><span v-for="item in Object.values(roleLabel)" :key="item">{{ item }}</span></div></aside>
        <div class="form-wrap"><v-card width="100%" max-width="460" class="pa-7" elevation="10"><div class="text-overline text-primary font-weight-bold">Taller Mecánico</div><h2 class="text-h4 mb-2">{{ title }}</h2><p class="text-medium-emphasis mb-6">{{ view === 'login' ? 'Ingresa con tus credenciales para continuar.' : view === 'register' ? 'Regístrate para consultar el estado de tu vehículo.' : 'Te enviaremos las instrucciones de recuperación.' }}</p>
          <v-alert v-if="error" type="error" density="compact" class="mb-4">{{ error }}</v-alert><v-alert v-if="notice" type="success" density="compact" class="mb-4">{{ notice }}</v-alert>
          <v-form v-model="valid" @submit.prevent="view === 'login' ? submitLogin() : view === 'register' ? submitRegister() : submitRecovery()">
            <template v-if="view === 'login'">
              <v-text-field v-model="login.email" label="Correo electrónico" type="email" :rules="emailRules" variant="outlined" />
              <v-text-field v-model="login.password" label="Contraseña" type="password" :rules="passwordRules" variant="outlined" />
            </template>
            <template v-else-if="view === 'register'">
              <v-text-field v-model="register.full_name" label="Nombre completo" :rules="[(v) => !!v || 'El nombre es requerido', (v) => v.length >= 3 || 'Mínimo 3 caracteres']" variant="outlined" />
              <v-text-field v-model="register.email" label="Correo electrónico" type="email" :rules="emailRules" variant="outlined" />
              <v-text-field v-model="register.password" label="Contraseña" type="password" :rules="passwordRules" variant="outlined" />
              <v-text-field v-model="register.confirm" label="Confirmar contraseña" type="password" :rules="[(v) => v === register.password || 'Las contraseñas no coinciden']" variant="outlined" />
            </template>
            <v-text-field v-else v-model="recoveryEmail" label="Correo electrónico" type="email" :rules="emailRules" variant="outlined" />
            <v-btn type="submit" color="primary" block size="large" :loading="loading">{{ view === 'login' ? 'Iniciar sesión' : view === 'register' ? 'Crear cuenta' : 'Solicitar recuperación' }}</v-btn>
          </v-form>
          <div class="text-center mt-5"><a v-if="view === 'login'" @click="view = 'recovery'; error = ''; notice = ''">¿Olvidaste tu contraseña?</a><a v-if="view !== 'login'" @click="view = 'login'; error = ''; notice = ''">Volver al inicio de sesión</a><p v-if="view === 'login'" class="mt-4">¿Eres cliente nuevo? <a @click="view = 'register'; error = ''">Crea tu cuenta</a></p></div>
        </v-card></div>
      </section>
    </v-main>
  </v-app>
</template>

<style scoped>
.page { min-height: 100vh; background: #f4f7fb; }.auth-layout { min-height: 100vh; display: grid; grid-template-columns: minmax(300px, 1fr) minmax(420px, 1fr); }.hero { background: linear-gradient(145deg, #062b58, #0b5cab); color: white; padding: clamp(3rem, 10vw, 9rem); display: flex; flex-direction: column; justify-content: center; }.hero h1 { font-size: clamp(2.2rem, 4vw, 4rem); line-height: 1.05; margin: 1.4rem 0; }.hero p { font-size: 1.1rem; max-width: 430px; opacity: .85; }.actors { display: flex; flex-wrap: wrap; gap: .5rem; margin-top: 2rem; }.actors span { border: 1px solid rgba(255,255,255,.3); padding: .4rem .7rem; border-radius: 50px; font-size: .82rem; }.form-wrap, .dashboard { display: flex; align-items: center; justify-content: center; padding: 2rem; }.dashboard { min-height: 100vh; } a { color: #0b5cab; cursor: pointer; font-weight: 600; text-decoration: none; } @media (max-width: 760px) { .auth-layout { grid-template-columns: 1fr; }.hero { min-height: 280px; padding: 3rem 2rem; }.hero h1 { font-size: 2.3rem; } }
</style>
