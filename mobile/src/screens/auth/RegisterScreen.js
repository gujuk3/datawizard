import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, KeyboardAvoidingView, Platform, ScrollView } from 'react-native';
import { register } from '../../api/auth';
import ErrorMessage from '../../components/ErrorMessage';
import { colors } from '../../theme';

export default function RegisterScreen({ navigation }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  async function handleRegister() {
    setError('');
    setLoading(true);
    try {
      await register(email.trim(), password);
      setSuccess(true);
    } catch (e) {
      const data = e.response?.data;
      setError(data?.email?.[0] || data?.password?.[0] || data?.detail || 'Kayıt başarısız.');
    } finally {
      setLoading(false);
    }
  }

  if (success) {
    return (
      <View style={styles.container}>
        <Text style={styles.logo}>DataWizard</Text>
        <Text style={styles.successTitle}>E-postanızı kontrol edin</Text>
        <Text style={styles.successText}>
          {email} adresine doğrulama bağlantısı gönderdik. Hesabınızı etkinleştirmek için tıklayın.
        </Text>
        <TouchableOpacity style={styles.button} onPress={() => navigation.navigate('Login')}>
          <Text style={styles.buttonText}>Girişe Dön</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <KeyboardAvoidingView style={styles.flex} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
        <Text style={styles.logo}>DataWizard</Text>
        <Text style={styles.subtitle}>Hesap oluşturun</Text>

        <ErrorMessage message={error} />

        <TextInput
          style={styles.input}
          placeholder="E-posta"
          placeholderTextColor={colors.lightGray}
          value={email}
          onChangeText={setEmail}
          autoCapitalize="none"
          keyboardType="email-address"
        />
        <TextInput
          style={styles.input}
          placeholder="Şifre"
          placeholderTextColor={colors.lightGray}
          value={password}
          onChangeText={setPassword}
          secureTextEntry
        />

        <TouchableOpacity style={styles.button} onPress={handleRegister} disabled={loading}>
          <Text style={styles.buttonText}>{loading ? 'Hesap oluşturuluyor…' : 'Kayıt Ol'}</Text>
        </TouchableOpacity>

        <TouchableOpacity onPress={() => navigation.navigate('Login')}>
          <Text style={styles.link}>Zaten hesabınız var mı? <Text style={styles.linkBold}>Giriş Yap</Text></Text>
        </TouchableOpacity>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.background },
  container: { flexGrow: 1, justifyContent: 'center', padding: 28 },
  logo: { fontSize: 32, fontWeight: '800', color: colors.primary, textAlign: 'center', marginBottom: 6 },
  subtitle: { fontSize: 15, color: colors.mediumGray, textAlign: 'center', marginBottom: 28 },
  input: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 8,
    padding: 14,
    fontSize: 15,
    color: colors.dark,
    marginBottom: 12,
  },
  button: {
    backgroundColor: colors.primary,
    borderRadius: 8,
    padding: 15,
    alignItems: 'center',
    marginTop: 4,
    marginBottom: 16,
  },
  buttonText: { color: '#fff', fontSize: 16, fontWeight: '600' },
  link: { color: colors.mediumGray, textAlign: 'center', marginTop: 10, fontSize: 14 },
  linkBold: { color: colors.primary, fontWeight: '600' },
  successTitle: { fontSize: 22, fontWeight: '700', color: colors.dark, textAlign: 'center', marginBottom: 12 },
  successText: { color: colors.mediumGray, textAlign: 'center', fontSize: 15, marginBottom: 28, lineHeight: 22 },
});
