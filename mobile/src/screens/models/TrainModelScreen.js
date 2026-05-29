import React, { useEffect, useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, ScrollView, StyleSheet } from 'react-native';
import { Picker } from '@react-native-picker/picker';
import { Ionicons } from '@expo/vector-icons';
import { listDatasets, previewDataset } from '../../api/datasets';
import { trainModel } from '../../api/models';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorMessage from '../../components/ErrorMessage';
import SectionCard from '../../components/SectionCard';
import { colors } from '../../theme';

const ALGORITHMS = {
  classification: ['logistic_regression', 'random_forest_classifier', 'decision_tree', 'knn'],
  regression: ['linear_regression', 'random_forest_regressor'],
};

export default function TrainModelScreen({ navigation }) {
  const [datasets, setDatasets] = useState([]);
  const [columns, setColumns] = useState([]);
  const [name, setName] = useState('');
  const [datasetId, setDatasetId] = useState(null);
  const [modelType, setModelType] = useState('classification');
  const [algorithm, setAlgorithm] = useState('random_forest_classifier');
  const [targetColumn, setTargetColumn] = useState('');
  const [testSize, setTestSize] = useState('0.2');
  const [loading, setLoading] = useState(true);
  const [training, setTraining] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);

  useEffect(() => {
    listDatasets()
      .then((data) => {
        setDatasets(data);
        if (data.length) {
          setDatasetId(data[0].id);
          loadColumns(data[0].id);
        }
      })
      .catch(() => setError('Veri setleri yüklenemedi.'))
      .finally(() => setLoading(false));
  }, []);

  async function loadColumns(id) {
    try {
      const preview = await previewDataset(id);
      setColumns(preview.columns || []);
      setTargetColumn(preview.columns?.[preview.columns.length - 1] || '');
    } catch {
      setColumns([]);
    }
  }

  function handleDatasetChange(id) {
    setDatasetId(id);
    loadColumns(id);
  }

  function handleModelTypeChange(type) {
    setModelType(type);
    setAlgorithm(ALGORITHMS[type][0]);
  }

  async function handleTrain() {
    if (!name.trim()) { setError('Model adı zorunludur.'); return; }
    if (!datasetId || !targetColumn) { setError('Veri seti ve hedef sütun seçin.'); return; }
    const ts = parseFloat(testSize);
    if (isNaN(ts) || ts < 0.1 || ts > 0.5) { setError('Test boyutu 0.1 ile 0.5 arasında olmalıdır.'); return; }

    setError('');
    setTraining(true);
    try {
      const data = await trainModel({
        name: name.trim(),
        dataset_id: datasetId,
        model_type: modelType,
        algorithm,
        target_column: targetColumn,
        test_size: ts,
      });
      setResult(data);
    } catch (e) {
      setError(e.response?.data?.error || 'Eğitim başarısız. Yapılandırmanızı kontrol edin.');
    } finally {
      setTraining(false);
    }
  }

  if (loading) return <LoadingSpinner />;

  if (result) {
    const evaluation = result.evaluation || {};
    const llmExplanation = result.llm_explanation;
    return (
      <ScrollView style={styles.container} contentContainerStyle={styles.content}>
        <View style={styles.successHeader}>
          <Ionicons name="checkmark-circle" size={48} color={colors.secondary} />
          <Text style={styles.successTitle}>Model eğitildi</Text>
          <Text style={styles.successSub}>{result.model?.name}</Text>
        </View>

        {Object.keys(evaluation).some((k) => typeof evaluation[k] === 'number') && (
          <SectionCard title="Metrikler">
            {Object.entries(evaluation)
              .filter(([, v]) => typeof v === 'number')
              .map(([k, v]) => (
                <View key={k} style={styles.metricRow}>
                  <Text style={styles.metricLabel}>{k}</Text>
                  <Text style={styles.metricValue}>{v.toFixed(4)}</Text>
                </View>
              ))}
          </SectionCard>
        )}

        {llmExplanation ? (
          <SectionCard title="AI Açıklaması">
            <Text style={styles.explanation}>{llmExplanation}</Text>
          </SectionCard>
        ) : null}

        <TouchableOpacity style={styles.trainBtn} onPress={() => navigation.goBack()}>
          <Text style={styles.trainBtnText}>Modellere Dön</Text>
        </TouchableOpacity>
      </ScrollView>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <ErrorMessage message={error} />

      <SectionCard title="Model Adı">
        <TextInput
          style={styles.input}
          placeholder="ör. Sınıflandırıcım"
          placeholderTextColor={colors.lightGray}
          value={name}
          onChangeText={setName}
        />
      </SectionCard>

      <SectionCard title="Veri Seti">
        <View style={styles.pickerWrap}>
          <Picker selectedValue={datasetId} onValueChange={handleDatasetChange} style={styles.picker}>
            {datasets.map((d) => <Picker.Item key={d.id} label={d.name} value={d.id} />)}
          </Picker>
        </View>
      </SectionCard>

      <SectionCard title="Model Türü">
        <View style={styles.toggle}>
          {[['classification', 'Sınıflandırma'], ['regression', 'Regresyon']].map(([type, label]) => (
            <TouchableOpacity
              key={type}
              style={[styles.toggleBtn, modelType === type && styles.toggleBtnActive]}
              onPress={() => handleModelTypeChange(type)}
            >
              <Text style={[styles.toggleText, modelType === type && styles.toggleTextActive]}>{label}</Text>
            </TouchableOpacity>
          ))}
        </View>
      </SectionCard>

      <SectionCard title="Algoritma">
        <View style={styles.pickerWrap}>
          <Picker selectedValue={algorithm} onValueChange={setAlgorithm} style={styles.picker}>
            {ALGORITHMS[modelType].map((a) => <Picker.Item key={a} label={a} value={a} />)}
          </Picker>
        </View>
      </SectionCard>

      <SectionCard title="Hedef Sütun">
        <View style={styles.pickerWrap}>
          <Picker selectedValue={targetColumn} onValueChange={setTargetColumn} style={styles.picker}>
            {columns.map((c) => <Picker.Item key={c} label={c} value={c} />)}
          </Picker>
        </View>
      </SectionCard>

      <SectionCard title="Test Boyutu">
        <TextInput
          style={styles.input}
          placeholder="0.2"
          placeholderTextColor={colors.lightGray}
          value={testSize}
          onChangeText={setTestSize}
          keyboardType="decimal-pad"
        />
        <Text style={styles.hint}>0.1 ile 0.5 arasında olmalıdır</Text>
      </SectionCard>

      <TouchableOpacity style={[styles.trainBtn, training && styles.trainBtnDisabled]} onPress={handleTrain} disabled={training}>
        <Text style={styles.trainBtnText}>{training ? 'Eğitiliyor…' : 'Modeli Eğit'}</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  content: { padding: 12, paddingBottom: 40 },
  input: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 8,
    padding: 12,
    fontSize: 15,
    color: colors.dark,
  },
  pickerWrap: { borderWidth: 1, borderColor: colors.border, borderRadius: 8, overflow: 'hidden' },
  picker: { color: colors.dark },
  toggle: { flexDirection: 'row', gap: 8 },
  toggleBtn: { flex: 1, padding: 10, borderRadius: 8, borderWidth: 1.5, borderColor: colors.border, alignItems: 'center' },
  toggleBtnActive: { borderColor: colors.primary, backgroundColor: '#f8f6ff' },
  toggleText: { fontSize: 13, color: colors.mediumGray, fontWeight: '500' },
  toggleTextActive: { color: colors.primary, fontWeight: '700' },
  hint: { fontSize: 12, color: colors.lightGray, marginTop: 4 },
  trainBtn: { backgroundColor: colors.primary, borderRadius: 8, padding: 15, alignItems: 'center', marginTop: 8 },
  trainBtnDisabled: { backgroundColor: colors.lightGray },
  trainBtnText: { color: '#fff', fontSize: 16, fontWeight: '600' },
  successHeader: { alignItems: 'center', marginBottom: 16 },
  successTitle: { fontSize: 22, fontWeight: '700', color: colors.dark, marginTop: 12 },
  successSub: { fontSize: 14, color: colors.mediumGray, marginTop: 4 },
  metricRow: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 5, borderBottomWidth: 1, borderBottomColor: colors.border },
  metricLabel: { fontSize: 13, color: colors.mediumGray },
  metricValue: { fontSize: 13, fontWeight: '600', color: colors.dark },
  explanation: { fontSize: 15, color: colors.dark, lineHeight: 24 },
});
