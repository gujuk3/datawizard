import React, { useCallback, useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet } from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import { listDatasets } from '../../api/datasets';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorMessage from '../../components/ErrorMessage';
import { colors } from '../../theme';

const ANALYTICS_OPTIONS = [
  { key: 'Statistics', label: 'İstatistikler', icon: 'stats-chart-outline', screen: 'Statistics' },
  { key: 'Correlation', label: 'Korelasyon', icon: 'grid-outline', screen: 'Correlation' },
  { key: 'MissingValues', label: 'Eksik Değerler', icon: 'alert-circle-outline', screen: 'MissingValues' },
  { key: 'LLMExplain', label: 'AI Açıklaması', icon: 'sparkles-outline', screen: 'LLMExplain' },
];

export default function AnalyticsHomeScreen({ navigation }) {
  const [datasets, setDatasets] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useFocusEffect(useCallback(() => {
    listDatasets()
      .then((data) => { setDatasets(data); if (data.length) setSelected(data[0]); })
      .catch(() => setError('Veri setleri yüklenemedi.'))
      .finally(() => setLoading(false));
  }, []));

  if (loading) return <LoadingSpinner />;

  return (
    <View style={styles.container}>
      <ErrorMessage message={error} />

      <Text style={styles.sectionLabel}>Veri Seti Seç</Text>
      <FlatList
        horizontal
        data={datasets}
        keyExtractor={(item) => String(item.id)}
        showsHorizontalScrollIndicator={false}
        style={styles.datasetPicker}
        renderItem={({ item }) => (
          <TouchableOpacity
            style={[styles.dsChip, selected?.id === item.id && styles.dsChipActive]}
            onPress={() => setSelected(item)}
          >
            <Text style={[styles.dsChipText, selected?.id === item.id && styles.dsChipTextActive]} numberOfLines={1}>
              {item.name}
            </Text>
          </TouchableOpacity>
        )}
        ListEmptyComponent={<Text style={styles.emptyText}>Veri seti yok. Önce bir tane yükleyin.</Text>}
      />

      {selected && (
        <>
          <Text style={styles.sectionLabel}>Analiz</Text>
          {ANALYTICS_OPTIONS.map((opt) => (
            <TouchableOpacity
              key={opt.key}
              style={styles.optCard}
              onPress={() => navigation.navigate(opt.screen, { dataset: selected })}
            >
              <Ionicons name={opt.icon} size={24} color={colors.primary} />
              <Text style={styles.optLabel}>{opt.label}</Text>
              <Ionicons name="chevron-forward" size={18} color={colors.lightGray} />
            </TouchableOpacity>
          ))}
        </>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background, padding: 14 },
  sectionLabel: { fontSize: 13, fontWeight: '700', color: colors.mediumGray, marginTop: 8, marginBottom: 8, textTransform: 'uppercase', letterSpacing: 0.5 },
  datasetPicker: { marginBottom: 12 },
  dsChip: {
    borderRadius: 16,
    borderWidth: 1.5,
    borderColor: colors.border,
    paddingHorizontal: 12,
    paddingVertical: 4,
    marginRight: 8,
    backgroundColor: colors.surface,
    maxWidth: 160,
    alignSelf: 'flex-start',
  },
  dsChipActive: { borderColor: colors.primary, backgroundColor: '#f8f6ff' },
  dsChipText: { fontSize: 13, color: colors.mediumGray },
  dsChipTextActive: { color: colors.primary, fontWeight: '600' },
  optCard: {
    backgroundColor: colors.surface,
    borderRadius: 10,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
    elevation: 1,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
  },
  optLabel: { flex: 1, fontSize: 15, fontWeight: '500', color: colors.dark, marginLeft: 14 },
  emptyText: { color: colors.lightGray, fontSize: 14 },
});
