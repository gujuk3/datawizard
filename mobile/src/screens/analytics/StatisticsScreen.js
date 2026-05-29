import React, { useEffect, useState } from 'react';
import { View, Text, ScrollView, StyleSheet } from 'react-native';
import { getStatistics } from '../../api/analytics';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorMessage from '../../components/ErrorMessage';
import SectionCard from '../../components/SectionCard';
import { colors } from '../../theme';

function StatRow({ label, value }) {
  return (
    <View style={styles.row}>
      <Text style={styles.rowLabel}>{label}</Text>
      <Text style={styles.rowValue}>{value ?? '—'}</Text>
    </View>
  );
}

export default function StatisticsScreen({ route }) {
  const { dataset } = route.params;
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    getStatistics(dataset.id)
      .then(setStats)
      .catch(() => setError('İstatistikler yüklenemedi.'))
      .finally(() => setLoading(false));
  }, [dataset.id]);

  if (loading) return <LoadingSpinner />;

  const numeric = stats?.statistics?.numeric || {};
  const categorical = stats?.statistics?.categorical || {};

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <ErrorMessage message={error} />

      {Object.keys(numeric).map((col) => {
        const s = numeric[col];
        return (
          <SectionCard key={col} title={col}>
            <StatRow label="Ortalama" value={s.mean} />
            <StatRow label="Medyan" value={s.median} />
            <StatRow label="Std. Sapma" value={s.std} />
            <StatRow label="Min" value={s.min} />
            <StatRow label="Maks" value={s.max} />
            <StatRow label="Q1" value={s.q1} />
            <StatRow label="Q3" value={s.q3} />
            <StatRow label="Çarpıklık" value={s.skewness} />
          </SectionCard>
        );
      })}

      {Object.keys(categorical).map((col) => {
        const s = categorical[col];
        return (
          <SectionCard key={col} title={col}>
            <StatRow label="Benzersiz değer" value={s.unique_count} />
            <StatRow label="En yaygın" value={s.top_values?.[0]?.value} />
            <StatRow label="Mod" value={s.mode} />
          </SectionCard>
        );
      })}

      {Object.keys(numeric).length === 0 && Object.keys(categorical).length === 0 && (
        <Text style={styles.empty}>İstatistik bulunamadı.</Text>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  content: { padding: 12 },
  row: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 5, borderBottomWidth: 1, borderBottomColor: colors.border },
  rowLabel: { fontSize: 13, color: colors.mediumGray },
  rowValue: { fontSize: 13, fontWeight: '600', color: colors.dark },
  empty: { textAlign: 'center', color: colors.lightGray, marginTop: 40 },
});
