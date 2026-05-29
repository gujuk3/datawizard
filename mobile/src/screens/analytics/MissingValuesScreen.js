import React, { useEffect, useState } from 'react';
import { View, Text, ScrollView, StyleSheet } from 'react-native';
import { getMissingValues } from '../../api/analytics';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorMessage from '../../components/ErrorMessage';
import SectionCard from '../../components/SectionCard';
import { colors } from '../../theme';

export default function MissingValuesScreen({ route }) {
  const { dataset } = route.params;
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    getMissingValues(dataset.id)
      .then(setData)
      .catch(() => setError('Eksik değer verisi yüklenemedi.'))
      .finally(() => setLoading(false));
  }, [dataset.id]);

  if (loading) return <LoadingSpinner />;

  const report = data?.missing_values || {};
  const columns = (report.columns || []).filter((c) => c.missing_count > 0);

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <ErrorMessage message={error} />

      <SectionCard>
        <Text style={styles.summary}>
          {columns.length === 0
            ? 'Bu veri setinde eksik değer bulunamadı.'
            : `${columns.length} sütunda eksik değer var · Tüm hücrelerin %${report.total_missing_pct ?? 0}'i`}
        </Text>
      </SectionCard>

      {columns.map((col) => {
        const pct = parseFloat(col.missing_pct) || 0;
        return (
          <SectionCard key={col.name}>
            <View style={styles.colHeader}>
              <Text style={styles.colName}>{col.name}</Text>
              <Text style={[styles.pctLabel, pct > 30 && styles.pctHigh]}>%{pct.toFixed(1)}</Text>
            </View>
            <Text style={styles.countText}>{col.total_count} satırdan {col.missing_count} tanesi eksik</Text>
            <View style={styles.barBg}>
              <View style={[styles.barFill, { width: `${Math.min(pct, 100)}%`, backgroundColor: pct > 30 ? colors.danger : colors.primary }]} />
            </View>
          </SectionCard>
        );
      })}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  content: { padding: 12 },
  summary: { fontSize: 15, color: colors.dark, lineHeight: 22 },
  colHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  colName: { fontSize: 15, fontWeight: '600', color: colors.dark },
  pctLabel: { fontSize: 14, fontWeight: '700', color: colors.primary },
  pctHigh: { color: colors.danger },
  countText: { fontSize: 12, color: colors.mediumGray, marginTop: 2, marginBottom: 8 },
  barBg: { height: 8, backgroundColor: colors.border, borderRadius: 4, overflow: 'hidden' },
  barFill: { height: 8, borderRadius: 4 },
});
