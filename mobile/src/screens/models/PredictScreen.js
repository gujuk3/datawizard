import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, ScrollView, StyleSheet } from 'react-native';
import { predict } from '../../api/models';
import ErrorMessage from '../../components/ErrorMessage';
import SectionCard from '../../components/SectionCard';
import { colors } from '../../theme';

export default function PredictScreen({ route }) {
  const { model } = route.params;
  const featureColumns = model.feature_columns || [];
  const [values, setValues] = useState(() => Object.fromEntries(featureColumns.map((c) => [c, ''])));
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  function setValue(col, val) {
    setValues((prev) => ({ ...prev, [col]: val }));
  }

  async function handlePredict() {
    setError('');
    setResult(null);
    const features = {};
    for (const col of featureColumns) {
      const raw = values[col];
      if (raw === '' || raw === null || raw === undefined) {
        setError(`"${col}" için bir değer girin.`);
        return;
      }
      const num = Number(raw);
      features[col] = isNaN(num) ? raw : num;
    }
    setLoading(true);
    try {
      const data = await predict(model.id, features);
      setResult(data.prediction);
    } catch (e) {
      setError(e.response?.data?.error || 'Tahmin başarısız.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <ErrorMessage message={error} />

      <SectionCard title="Giriş Özellikleri">
        {featureColumns.map((col) => (
          <View key={col} style={styles.fieldRow}>
            <Text style={styles.fieldLabel}>{col}</Text>
            <TextInput
              style={styles.fieldInput}
              value={values[col]}
              onChangeText={(v) => setValue(col, v)}
              placeholder="değer"
              placeholderTextColor={colors.lightGray}
              keyboardType="default"
            />
          </View>
        ))}
      </SectionCard>

      <TouchableOpacity style={[styles.btn, loading && styles.btnDisabled]} onPress={handlePredict} disabled={loading}>
        <Text style={styles.btnText}>{loading ? 'Tahmin ediliyor…' : 'Tahmin Et'}</Text>
      </TouchableOpacity>

      {result !== null && (
        <SectionCard title="Sonuç">
          <Text style={styles.resultLabel}>Tahmin</Text>
          <Text style={styles.resultValue}>{String(result)}</Text>
        </SectionCard>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  content: { padding: 12, paddingBottom: 40 },
  fieldRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 10 },
  fieldLabel: { width: 120, fontSize: 13, color: colors.dark, fontWeight: '500' },
  fieldInput: {
    flex: 1,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 8,
    padding: 10,
    fontSize: 14,
    color: colors.dark,
  },
  btn: { backgroundColor: colors.secondary, borderRadius: 8, padding: 15, alignItems: 'center', marginVertical: 8 },
  btnDisabled: { backgroundColor: colors.lightGray },
  btnText: { color: '#fff', fontSize: 16, fontWeight: '600' },
  resultLabel: { fontSize: 13, color: colors.mediumGray, marginBottom: 4 },
  resultValue: { fontSize: 28, fontWeight: '800', color: colors.primary },
});
