import client from './client';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';

const API_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000/api';

export async function login(email, password) {
  const { data } = await axios.post(`${API_URL}/auth/login/`, { email, password });
  await AsyncStorage.setItem('access_token', data.access);
  await AsyncStorage.setItem('refresh_token', data.refresh);
  return data;
}

export async function register(email, password) {
  const { data } = await axios.post(`${API_URL}/auth/register/`, { email, password });
  return data;
}

export async function forgotPassword(email) {
  const { data } = await axios.post(`${API_URL}/auth/forgot-password/`, { email });
  return data;
}

export async function getMe() {
  const { data } = await client.get('/auth/me/');
  return data;
}

export async function logout() {
  await AsyncStorage.multiRemove(['access_token', 'refresh_token']);
}
