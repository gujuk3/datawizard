import React, { useEffect, useState } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet } from 'react-native';
import { getModel } from '../../api/models';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorMessage from '../../components/ErrorMessage';
import SectionCard from '../../components/SectionCard';
import { colors } from '../../theme';

function MetricRow({ label, value }) {
  return (
    <View style={styles.row}>
      <Text style={styles.rowLabel}>{label}</Text>
      <Text style={styles.rowValue}>{typeof value === 'number' ? value.toFixed(4) : String(value ?? '—')}</Text>
    </View>
  );
}

export default function ModelDetailScreen({ route, navigation }) {
  const { modelId } = route.params;
  const [model, setModel] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    getModel(modelId)
      .then(setModel)
      .catch(() => setError('Model yüklenemedi.'))
      .finally(() => setLoading(false));
  }, [modelId]);

  if (loading) return <LoadingSpinner />;
  if (!model) return <ErrorMessage message={error || 'Model bulunamadı.'} />;

  const metrics = model.metrics || [];
  const scalarMetrics = metrics.filter((m) => m.metric_value !== null);
  const featureImportance = metrics.find((m) => m.metric_name === 'feature_importance')?.additional_data || [];

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <ErrorMessage message={error} />

      <SectionCard title="Model Bilgisi">
        <MetricRow label="Algoritma" value={model.algorithm} />
        <MetricRow label="Tür" value={model.model_type} />
        <MetricRow label="Hedef" value={model.target_column} />
        <MetricRow label="Test boyutu" value={`%${(model.train_test_split * 100).toFixed(0)}`} />
        <MetricRow label="Eğitim süresi" value={model.training_duration ? `${model.training_duration}s` : '—'} />
      </SectionCard>

      {scalarMetrics.length > 0 && (
        <SectionCard title="Metrikler">
          {scalarMetrics.map((m) => (
            <MetricRow key={m.metric_name} label={m.metric_name} value={m.metric_value} />
          ))}
        </SectionCard>
      )}

      {featureImportance.length > 0 && (
        <SectionCard title="Özellik Önemi">
          {featureImportance.slice(0, 8).map((f) => (
            <View key={f.feature} style={styles.featureRow}>
              <Text style={styles.featureName} numberOfLines={1}>{f.feature}</Text>
              <View style={styles.barBg}>
                <View style={[styles.barFill, { width: `${Math.min(parseFloat(f.importance_pct), 100)}%` }]} />
              </View>
              <Text style={styles.featurePct}>%{f.importance_pct}</Text>
            </View>
          ))}
        </SectionCard>
      )}

      <TouchableOpacity
        style={styles.predictBtn}
        onPress={() => navigation.navigate('Predict', { model })}
      >
        <Text style={styles.predictBtnText}>Tahmin Yap</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  content: { padding: 12, paddingBottom: 32 },
  row: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 6, borderBottomWidth: 1, borderBottomColor: colors.border },
  rowLabel: { fontSize: 13, color: colors.mediumGray },
  rowValue: { fontSize: 13, fontWeight: '600', color: colors.dark },
  featureRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 8 },
  featureName: { width: 100, fontSize: 12, color: colors.dark },
  barBg: { flex: 1, height: 8, backgroundColor: colors.border, borderRadius: 4, marginHorizontal: 8, overflow: 'hidden' },
  barFill: { height: 8, backgroundColor: colors.primary, borderRadius: 4 },
  featurePct: { width: 42, fontSize: 12, color: colors.mediumGray, textAlign: 'right' },
  predictBtn: {
    backgroundColor: colors.secondary,
    borderRadius: 8,
    padding: 15,
    alignItems: 'center',
    marginTop: 8,
  },
  predictBtnText: { color: '#fff', fontSize: 16, fontWeight: '600' },
});
