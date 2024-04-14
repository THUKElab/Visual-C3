

def compute_p_r_f1(true_predict, all_predict, all_error):
    p = true_predict / (all_predict + 1e-10) * 100
    r = true_predict / (all_error + 1e-10) * 100

    if true_predict == all_error and all_error == 0: 
        r = 100

    f1 = round(2 * p * r / (p + r + 1e-10), 3)
    return {'p': round(p, 3), 'r': round(r, 3), 'f1': f1}


def write_report(output_file, metric, output_errors):
    with open(output_file, 'wt', encoding='utf-8') as f:
        f.write('overview:\n')
        for key in metric:
            f.write(f'{key}:{metric[key]}\n')
        f.write('\n cases:\n')
        for output_error in output_errors:
            f.write("\n".join(output_error))
            f.write("\n\n")


def input_check_and_process(src_sentences, tgt_sentences, bert_pred_sentences, ocr_pred_sentences):
    assert len(src_sentences) == len(tgt_sentences) == len(bert_pred_sentences) == len(ocr_pred_sentences)
    src_char_list = [list(s) for s in src_sentences]
    tgt_char_list = [list(s) for s in tgt_sentences]
    bert_pred_char_list = [list(s) for s in bert_pred_sentences]
    ocr_pred_char_list = [list(s) for s in ocr_pred_sentences]

    assert all(
        [len(src) == len(tgt) == len(bert_pred) == len(ocr_pred) for src, tgt, bert_pred, ocr_pred in
         zip(src_char_list, tgt_char_list, bert_pred_char_list, ocr_pred_char_list)]
    )
    return src_char_list, tgt_char_list, bert_pred_char_list, ocr_pred_char_list


def calculate_metric(src_sentences, tgt_sentences, bert_pred_sentences, ocr_pred_sentences, report_file=None,
                     ignore_chars=""):
    src_char_list, tgt_char_list, bert_pred_char_list, ocr_pred_char_list = input_check_and_process(src_sentences,
                                                                                                    tgt_sentences,
                                                                                                    bert_pred_sentences,
                                                                                                    ocr_pred_sentences)
    ignore_chars = ''

    sentence_cuo_detection, sentence_bie_detection, sentence_cuo_correction, sentence_bie_correction, char_cuo_detection, char_bie_detection, char_cuo_correction, char_bie_correction = [
        {'all_error': 0, 'true_predict': 0, 'all_predict': 0} for _ in range(8)]

    output_errors = []
    for src_chars, tgt_chars, bert_pred_chars, ocr_pred_chars in zip(src_char_list, tgt_char_list, bert_pred_char_list,
                                                                     ocr_pred_char_list):
        true_cuo_error_indexes = []
        true_bie_error_indexes = []
        detect_cuo_indexes = []
        detect_bie_indexes = []

        for index, (src_char, tgt_char, bert_pred_char, ocr_pred_char) in enumerate(
                zip(src_chars, tgt_chars, bert_pred_chars, ocr_pred_chars)):

            if src_char in ignore_chars or tgt_char in ignore_chars:
                bert_pred_chars[index] = tgt_char
                src_chars[index] = tgt_char
                ocr_pred_chars[index] = tgt_char
                continue

            if src_char != tgt_char and src_char != 'X': 
                char_bie_detection['all_error'] += 1
                char_bie_correction['all_error'] += 1
                true_bie_error_indexes.append(index)

            if src_char != tgt_char and src_char == 'X':  
                char_cuo_detection['all_error'] += 1
                char_cuo_correction['all_error'] += 1
                true_cuo_error_indexes.append(index)

            if src_char != bert_pred_char and src_char != 'X' and ocr_pred_char != 'X': 
                char_bie_detection['all_predict'] += 1
                char_bie_correction['all_predict'] += 1
                detect_bie_indexes.append(index)

                if src_char != tgt_char:
                    char_bie_detection['true_predict'] += 1
                if bert_pred_char == tgt_char:
                    char_bie_correction['true_predict'] += 1

            if ocr_pred_char == 'X': 
                char_cuo_detection['all_predict'] += 1
                char_cuo_correction['all_predict'] += 1
                detect_cuo_indexes.append(index)

            if src_char == ocr_pred_char and src_char == 'X':
                char_cuo_detection['true_predict'] += 1

            if bert_pred_char == tgt_char and src_char == ocr_pred_char and src_char == 'X':  # TODO：这里用的是bert之后的
                char_cuo_correction['true_predict'] += 1

        # sentence
        if true_bie_error_indexes:
            sentence_bie_detection['all_error'] += 1
            sentence_bie_correction['all_error'] += 1

        if true_cuo_error_indexes:
            sentence_cuo_detection['all_error'] += 1
            sentence_cuo_correction['all_error'] += 1

        
        if detect_bie_indexes:  
            sentence_bie_detection['all_predict'] += 1
            sentence_bie_correction['all_predict'] += 1

            if tuple(true_bie_error_indexes) == tuple(detect_bie_indexes):
                sentence_bie_detection['true_predict'] += 1

                if len(true_cuo_error_indexes) == 0:  
                    if tuple(tgt_chars) == tuple(bert_pred_chars):
                        sentence_bie_correction['true_predict'] += 1
                else:
                    if all(tgt_chars[i] == bert_pred_chars[i] for i in range(len(tgt_chars)) if i not in true_cuo_error_indexes):
                        sentence_bie_correction['true_predict'] += 1


        if detect_cuo_indexes:
            sentence_cuo_detection['all_predict'] += 1
            sentence_cuo_correction['all_predict'] += 1
            if tuple(true_cuo_error_indexes) == tuple(detect_cuo_indexes):
                sentence_cuo_detection['true_predict'] += 1

                if all(tgt_chars[i] == bert_pred_chars[i] for i in true_cuo_error_indexes):
                    sentence_cuo_correction['true_predict'] += 1


    result = dict()
    for prefix_name, sub_metric in zip(
            ['Sentence_Detection_Bie_', 'Sentence_Detection_Cuo_', 'Sentence_Correction_Cuo_',
             'Sentence_Correction_Bie_', 'Char_Detection_Bie_',
             'Char_Detection_Cuo_', 'Char_Correction_Cuo_', 'Char_Correction_Bie_'],
            [sentence_bie_detection, sentence_cuo_detection, sentence_cuo_correction, sentence_bie_correction,
             char_bie_detection, char_cuo_detection, char_cuo_correction, char_bie_correction]):
        sub_r = compute_p_r_f1(sub_metric['true_predict'], sub_metric['all_predict'], sub_metric['all_error']).items()
        for k, v in sub_r:
            result[prefix_name + k] = v
    if report_file:
        write_report(report_file, result, output_errors)


    return result


def open_file(inputfiles):
    file_dist = {}
    with open(inputfiles, 'r', encoding='utf-8') as f:
        for line in f.readlines():
            if line == '\n':
                continue
            filename = line.split('  ')[0]
            lines = line.split('  ')[1]  
            lines = lines.strip('\n')
            file_dist[filename] = lines
    return file_dist


def main():
    predicts, tgts, srcs, ocr_preds = [], [], [], []
    prename, tgtname, ocrname, srcname = '', '', '', ''

    pre_dist = open_file(prename)
    tgt_dist = open_file(tgtname)
    ocrpre_dist = open_file(ocrname)
    src_dist = open_file(srcname)

    tgt_file = tgt_dist.keys()
    files = tgt_file

    for i in files:
        assert (len(pre_dist[i]) == len(src_dist[i]) and len(src_dist[i]) == len(tgt_dist[i]) and len(
                ocrpre_dist[i]) == len(tgt_dist[i]))
        predicts.append(pre_dist[i])
        srcs.append(src_dist[i])
        tgts.append(tgt_dist[i])
        ocr_preds.append(ocrpre_dist[i])

    print(calculate_metric(srcs, tgts, predicts, ocr_preds, "result.txt"))


if __name__ == "__main__":
    main()
