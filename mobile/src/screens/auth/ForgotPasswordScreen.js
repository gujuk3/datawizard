import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, KeyboardAvoidingView, Platform } from 'react-native';
import { forgotPassword } from '../../api/auth';
import ErrorMessage from '../../components/ErrorMessage';
import { colors } from '../../theme';

export default function ForgotPasswordScreen({ navigation }) {
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);

  async function handleSubmit() {
    setError('');
    setLoading(true);
    try {
      await forgotPassword(email.trim());
      setSent(true);
    } catch (e) {
      setError(e.response?.data?.detail || 'Bir hata oluştu. Tekrar deneyin.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <KeyboardAvoidingView style={styles.flex} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <View style={styles.container}>
        <Text style={styles.title}>Şifreyi Sıfırla</Text>

        {sent ? (
          <>
            <Text style={styles.sentText}>
              {email} için bir hesap mevcutsa sıfırlama bağlantısı gönderildi.
            </Text>
            <TouchableOpacity style={styles.button} onPress={() => navigation.navigate('Login')}>
              <Text style={styles.buttonText}>Girişe Dön</Text>
            </TouchableOpacity>
          </>
        ) : (
          <>
            <Text style={styles.subtitle}>E-postanızı girin, sıfırlama bağlantısı gönderelim.</Text>
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
            <TouchableOpacity style={styles.button} onPress={handleSubmit} disabled={loading}>
              <Text style={styles.buttonText}>{loading ? 'Gönderiliyor…' : 'Sıfırlama Bağlantısı Gönder'}</Text>
            </TouchableOpacity>
            <TouchableOpacity onPress={() => navigation.goBack()}>
              <Text style={styles.link}>Girişe Dön</Text>
            </TouchableOpacity>
          </>
        )}
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.background },
  container: { flex: 1, padding: 28, justifyContent: 'center' },
  title: { fontSize: 26, fontWeight: '800', color: colors.dark, marginBottom: 8 },
  subtitle: { color: colors.mediumGray, fontSize: 15, marginBottom: 24 },
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
    marginBottom: 12,
  },
  buttonText: { color: '#fff', fontSize: 16, fontWeight: '600' },
  link: { color: colors.primary, textAlign: 'center', fontSize: 14, marginTop: 8 },
  sentText: { color: colors.dark, fontSize: 15, lineHeight: 22, marginBottom: 24 },
});
