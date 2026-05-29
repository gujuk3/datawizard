import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Alert } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../../context/AuthContext';
import SectionCard from '../../components/SectionCard';
import { colors } from '../../theme';

export default function AccountScreen() {
  const { user, logout } = useAuth();

  function confirmLogout() {
    Alert.alert(
      'Çıkış Yap',
      'Çıkış yapmak istediğinizden emin misiniz?',
      [
        { text: 'İptal', style: 'cancel' },
        { text: 'Çıkış Yap', style: 'destructive', onPress: logout },
      ]
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.avatar}>
        <Ionicons name="person-circle-outline" size={80} color={colors.primary} />
        <Text style={styles.email}>{user?.email || ''}</Text>
      </View>

      <SectionCard title="Hesap">
        <View style={styles.row}>
          <Text style={styles.rowLabel}>E-posta</Text>
          <Text style={styles.rowValue}>{user?.email || '—'}</Text>
        </View>
      </SectionCard>

      <TouchableOpacity style={styles.logoutBtn} onPress={confirmLogout}>
        <Ionicons name="log-out-outline" size={20} color="#fff" style={styles.logoutIcon} />
        <Text style={styles.logoutText}>Çıkış Yap</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background, padding: 16 },
  avatar: { alignItems: 'center', paddingVertical: 28 },
  email: { fontSize: 15, color: colors.mediumGray, marginTop: 8 },
  row: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 6 },
  rowLabel: { fontSize: 14, color: colors.mediumGray },
  rowValue: { fontSize: 14, fontWeight: '600', color: colors.dark },
  logoutBtn: {
    flexDirection: 'row',
    backgroundColor: colors.danger,
    borderRadius: 8,
    padding: 15,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 16,
  },
  logoutIcon: { marginRight: 8 },
  logoutText: { color: '#fff', fontSize: 16, fontWeight: '600' },
});
