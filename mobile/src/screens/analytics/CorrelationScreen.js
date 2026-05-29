import React, { useEffect, useState } from 'react';
import { View, Text, ScrollView, StyleSheet } from 'react-native';
import { getCorrelation } from '../../api/analytics';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorMessage from '../../components/ErrorMessage';
import SectionCard from '../../components/SectionCard';
import { colors } from '../../theme';

function correlationColor(val) {
  if (val === null || val === undefined) return '#f0f2f5';
  const abs = Math.abs(val);
  if (abs >= 0.7) return val > 0 ? '#00b894' : '#e17055';
  if (abs >= 0.4) return val > 0 ? '#55efc4' : '#fab1a0';
  return '#f0f2f5';
}

export default function CorrelationScreen({ route }) {
  const { dataset } = route.params;
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    getCorrelation(dataset.id)
      .then(setData)
      .catch(() => setError('Korelasyon verisi yüklenemedi.'))
      .finally(() => setLoading(false));
  }, [dataset.id]);

  if (loading) return <LoadingSpinner />;

  const columns = data?.correlation?.columns || [];
  const matrix = data?.correlation?.matrix || [];

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <ErrorMessage message={error} />

      {columns.length > 0 ? (
        <SectionCard title="Korelasyon Matrisi">
          <ScrollView horizontal>
            <View>
              <View style={styles.headerRow}>
                <View style={styles.labelCell} />
                {columns.map((col) => (
                  <Text key={col} style={styles.headerCell} numberOfLines={1}>{col}</Text>
                ))}
              </View>
              {columns.map((rowLabel, rowIdx) => (
                <View key={rowLabel} style={styles.matrixRow}>
                  <Text style={styles.rowLabel} numberOfLines={1}>{rowLabel}</Text>
                  {columns.map((_, colIdx) => {
                    const val = matrix[rowIdx]?.[colIdx];
                    return (
                      <View key={colIdx} style={[styles.cell, { backgroundColor: correlationColor(val) }]}>
                        <Text style={styles.cellText}>{val !== undefined ? val.toFixed(2) : '—'}</Text>
                      </View>
                    );
                  })}
                </View>
              ))}
            </View>
          </ScrollView>
          <View style={styles.legend}>
            <View style={[styles.legendDot, { backgroundColor: '#00b894' }]} /><Text style={styles.legendText}>Güçlü pozitif</Text>
            <View style={[styles.legendDot, { backgroundColor: '#e17055' }]} /><Text style={styles.legendText}>Güçlü negatif</Text>
          </View>
        </SectionCard>
      ) : (
        <Text style={styles.empty}>Korelasyon için yeterli sayısal sütun yok.</Text>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  content: { padding: 12 },
  headerRow: { flexDirection: 'row' },
  labelCell: { width: 80 },
  headerCell: { width: 64, fontSize: 11, fontWeight: '700', color: colors.primary, textAlign: 'center', padding: 4 },
  matrixRow: { flexDirection: 'row', alignItems: 'center' },
  rowLabel: { width: 80, fontSize: 11, fontWeight: '600', color: colors.dark, paddingRight: 4 },
  cell: { width: 64, height: 40, justifyContent: 'center', alignItems: 'center', margin: 1, borderRadius: 4 },
  cellText: { fontSize: 11, fontWeight: '600', color: colors.dark },
  legend: { flexDirection: 'row', alignItems: 'center', marginTop: 12, flexWrap: 'wrap' },
  legendDot: { width: 12, height: 12, borderRadius: 6, marginRight: 4 },
  legendText: { fontSize: 12, color: colors.mediumGray, marginRight: 16 },
  empty: { textAlign: 'center', color: colors.lightGray, marginTop: 40 },
});
